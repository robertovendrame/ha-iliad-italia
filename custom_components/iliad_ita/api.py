"""Async client for Iliad Italia account data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import re

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import CONSUMPTION_URL, LOGIN_URL


class IliadError(Exception):
    """Base Iliad error."""


class IliadAuthError(IliadError):
    """Authentication failed."""


class IliadConnectionError(IliadError):
    """Network request failed."""


class IliadParseError(IliadError):
    """Expected values could not be parsed."""


@dataclass(slots=True)
class IliadData:
    """Values exposed by the Iliad account page."""

    balance_eur: float | None
    data_used_gb: float | None
    data_remaining_gb: float | None
    data_allowance_gb: float | None
    offer_name: str | None
    offer_price_eur: float | None
    renewal_date: date | None
    period_start: date | None
    period_end: date | None
    fetched_at: datetime


def _decimal(value: str) -> float:
    text = value.strip().replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return float(text)


def _size_to_gb(value: str, unit: str) -> float:
    number = _decimal(value)
    factors = {"KB": 1 / 1_000_000, "MB": 1 / 1_000, "GB": 1, "TB": 1_000}
    return number * factors[unit.upper()]


_ITALIAN_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

_TEXTUAL_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
    r"settembre|ottobre|novembre|dicembre)"
    r"(?:\s+(\d{4}))?\b",
    flags=re.IGNORECASE,
)


def _build_date(day: int, month: int, year: int | None, reference: date) -> date | None:
    if year is None:
        year = reference.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            return None
        if candidate < reference:
            year += 1
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_textual_date(text: str, reference: date) -> date | None:
    match = _TEXTUAL_DATE_RE.search(text)
    if not match:
        return None
    return _build_date(
        int(match.group(1)),
        _ITALIAN_MONTHS[match.group(2).lower()],
        int(match.group(3)) if match.group(3) else None,
        reference,
    )


def _parse_reference_period(text: str, reference: date) -> tuple[date | None, date | None]:
    normalized = " ".join(text.split())
    marker = re.search(r"periodo\s+di\s+riferimento\s+dal\s+", normalized, re.IGNORECASE)
    if not marker:
        return None, None
    matches = list(_TEXTUAL_DATE_RE.finditer(normalized[marker.end() : marker.end() + 180]))
    if len(matches) < 2:
        return None, None
    period_start = _parse_textual_date(matches[0].group(0), reference)
    period_end = _parse_textual_date(matches[1].group(0), reference)
    if period_start is None or period_end is None or period_end < period_start:
        return None, None
    return period_start, period_end


def _parse_renewal_date(text: str, reference: date, period_end: date | None = None) -> date | None:
    """Parse only a date explicitly attached to renewal text, then use period fallback."""
    normalized = " ".join(text.split())

    numeric = re.search(
        r"(?:si\s+)?rinnov\w*\s+(?:il\s+)?"
        r"(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if numeric:
        year_raw = numeric.group(3)
        year = int(year_raw) if year_raw else None
        if year is not None and year < 100:
            year += 2000
        parsed = _build_date(int(numeric.group(1)), int(numeric.group(2)), year, reference)
        if parsed is not None:
            return parsed

    textual = re.search(
        r"(?:si\s+)?rinnov\w*\s+(?:il\s+)?"
        r"(\d{1,2}\s+(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|"
        r"agosto|settembre|ottobre|novembre|dicembre)(?:\s+\d{4})?)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if textual:
        parsed = _parse_textual_date(textual.group(1), reference)
        if parsed is not None:
            return parsed

    return period_end + timedelta(days=1) if period_end is not None else None


def _parse_offer_metadata(text: str) -> tuple[str | None, float | None, float | None]:
    """Parse offer name, official data allowance and renewal price from page text."""
    normalized = " ".join(text.split())

    offer_name = None
    offer_match = re.search(
        r"\b(Offerta\s+.+?)(?=\s*[•·]\s*Credito\b|\s+Credito\s*:)",
        normalized,
        flags=re.IGNORECASE,
    )
    if offer_match:
        offer_name = " ".join(offer_match.group(1).split())

    data_allowance_gb = None
    allowance_match = re.search(
        r"\b\d+[\d.,]*\s*(KB|MB|GB|TB)\s*/\s*(\d+[\d.,]*)\s*(KB|MB|GB|TB)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if allowance_match:
        data_allowance_gb = _size_to_gb(allowance_match.group(2), allowance_match.group(3))

    offer_price_eur = None
    renewal_match = re.search(r"si\s+rinnova\b(.{0,120})", normalized, flags=re.IGNORECASE)
    if renewal_match:
        price_match = re.search(r"\ba\s*([\d.,]+)\s*€", renewal_match.group(1), flags=re.IGNORECASE)
        if price_match:
            offer_price_eur = _decimal(price_match.group(1))

    return offer_name, data_allowance_gb, offer_price_eur


def parse_account_page(html: str) -> IliadData:
    """Parse Iliad's consumi-e-credito HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    balance = None
    balance_node = soup.select_one("b.red[data-cs-mask]")
    if balance_node:
        match = re.search(r"([\d.,]+)\s*€", balance_node.get_text(" ", strip=True))
        if match:
            balance = _decimal(match.group(1))

    size_pattern = re.compile(r"(\d+[\d.,]*)\s*(KB|MB|GB|TB)", re.IGNORECASE)
    remaining = None
    remaining_node = soup.select_one("span.big.red")
    if remaining_node:
        value_match = re.search(r"([\d.,]+)", remaining_node.get_text(" ", strip=True))
        unit_node = remaining_node.find_next("span", class_=["small", "red"]) or soup.select_one("span.small.red")
        unit_match = re.search(r"\b(KB|MB|GB|TB)\b", unit_node.get_text(" ", strip=True), re.IGNORECASE) if unit_node else None
        if value_match and unit_match:
            remaining = _size_to_gb(value_match.group(1), unit_match.group(1))

    used = None
    for node in soup.select("span.red"):
        if node is remaining_node:
            continue
        match = size_pattern.search(node.get_text(" ", strip=True))
        if match:
            used = _size_to_gb(match.group(1), match.group(2))
            break

    fetched_at = datetime.now(timezone.utc)
    page_text = soup.get_text(" ", strip=True)
    period_start, period_end = _parse_reference_period(page_text, fetched_at.date())
    renewal_date = _parse_renewal_date(page_text, fetched_at.date(), period_end)
    offer_name, data_allowance_gb, offer_price_eur = _parse_offer_metadata(page_text)

    if balance is None and used is None and remaining is None:
        raise IliadParseError("Nessun dato Iliad riconosciuto nella pagina account")

    return IliadData(
        balance_eur=balance,
        data_used_gb=used,
        data_remaining_gb=remaining,
        data_allowance_gb=data_allowance_gb,
        offer_name=offer_name,
        offer_price_eur=offer_price_eur,
        renewal_date=renewal_date,
        period_start=period_start,
        period_end=period_end,
        fetched_at=fetched_at,
    )


class IliadClient:
    """Minimal async client for the Iliad personal area."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password

    async def async_fetch_data(self) -> IliadData:
        try:
            async with self._session.post(
                LOGIN_URL,
                data={"login-ident": self._username, "login-pwd": self._password},
                allow_redirects=True,
                timeout=20,
            ) as response:
                if response.status >= 400:
                    raise IliadConnectionError(f"Login HTTP {response.status}")
                await response.read()

            async with self._session.get(CONSUMPTION_URL, allow_redirects=True, timeout=20) as response:
                if response.status >= 400:
                    raise IliadConnectionError(f"Account HTTP {response.status}")
                html = await response.text()
                final_url = str(response.url)
        except (ClientError, TimeoutError) as err:
            raise IliadConnectionError(str(err)) from err

        if "/account/login" in final_url or 'name="login-ident"' in html:
            raise IliadAuthError("Credenziali Iliad non valide o sessione non autenticata")

        return parse_account_page(html)
