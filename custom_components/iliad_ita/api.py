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
    factors = {
        "KB": 1 / 1_000_000,
        "MB": 1 / 1_000,
        "GB": 1,
        "TB": 1_000,
    }
    return number * factors[unit.upper()]


_ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

_TEXTUAL_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
    r"settembre|ottobre|novembre|dicembre)"
    r"(?:\s+(\d{4}))?\b",
    flags=re.IGNORECASE,
)


def _build_date(day: int, month: int, year: int | None, reference: date) -> date | None:
    """Build a date and infer the year when Iliad omits it."""
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
    """Parse an Italian textual date such as '02 Settembre 2026'."""
    match = _TEXTUAL_DATE_RE.search(text)
    if not match:
        return None

    day = int(match.group(1))
    month = _ITALIAN_MONTHS[match.group(2).lower()]
    year = int(match.group(3)) if match.group(3) else None
    return _build_date(day, month, year, reference)


def _parse_reference_period(text: str, reference: date) -> tuple[date | None, date | None]:
    """Parse 'Periodo di riferimento dal <date> al <date>' from Iliad."""
    normalized = " ".join(text.split())
    marker = re.search(
        r"periodo\s+di\s+riferimento\s+dal\s+",
        normalized,
        flags=re.IGNORECASE,
    )
    if not marker:
        return None, None

    window = normalized[marker.end() : marker.end() + 180]
    matches = list(_TEXTUAL_DATE_RE.finditer(window))
    if len(matches) < 2:
        return None, None

    period_start = _parse_textual_date(matches[0].group(0), reference)
    period_end = _parse_textual_date(matches[1].group(0), reference)
    if period_start is None or period_end is None or period_end < period_start:
        return None, None

    return period_start, period_end


def _parse_renewal_date(
    text: str,
    reference: date,
    period_end: date | None = None,
) -> date | None:
    """Find the renewal date, with a fallback from the reference period end."""
    normalized = " ".join(text.split())

    # Primary source: a date close to 'rinnovo' / 'si rinnova'.
    for keyword in re.finditer(r"rinnov\w*", normalized, flags=re.IGNORECASE):
        start = max(0, keyword.start() - 40)
        end = min(len(normalized), keyword.end() + 140)
        window = normalized[start:end]

        numeric = re.search(
            r"\b(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?\b",
            window,
        )
        if numeric:
            day = int(numeric.group(1))
            month = int(numeric.group(2))
            year_raw = numeric.group(3)
            year = int(year_raw) if year_raw else None
            if year is not None and year < 100:
                year += 2000
            parsed = _build_date(day, month, year, reference)
            if parsed is not None:
                return parsed

        parsed = _parse_textual_date(window, reference)
        if parsed is not None:
            return parsed

    # Real Iliad pages expose the offer reference period. Renewal is the day
    # immediately following the period end.
    if period_end is not None:
        return period_end + timedelta(days=1)

    return None


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
        unit_node = remaining_node.find_next("span", class_=["small", "red"])
        if unit_node is None:
            unit_node = soup.select_one("span.small.red")
        unit_match = (
            re.search(r"\b(KB|MB|GB|TB)\b", unit_node.get_text(" ", strip=True), re.IGNORECASE)
            if unit_node
            else None
        )
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
    renewal_date = _parse_renewal_date(
        page_text,
        fetched_at.date(),
        period_end,
    )

    if balance is None and used is None and remaining is None:
        raise IliadParseError("Nessun dato Iliad riconosciuto nella pagina account")

    return IliadData(
        balance_eur=balance,
        data_used_gb=used,
        data_remaining_gb=remaining,
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
        """Authenticate and retrieve current account consumption data."""
        try:
            async with self._session.post(
                LOGIN_URL,
                data={
                    "login-ident": self._username,
                    "login-pwd": self._password,
                },
                allow_redirects=True,
                timeout=20,
            ) as response:
                if response.status >= 400:
                    raise IliadConnectionError(f"Login HTTP {response.status}")
                await response.read()

            async with self._session.get(
                CONSUMPTION_URL,
                allow_redirects=True,
                timeout=20,
            ) as response:
                if response.status >= 400:
                    raise IliadConnectionError(f"Account HTTP {response.status}")
                html = await response.text()
                final_url = str(response.url)

        except (ClientError, TimeoutError) as err:
            raise IliadConnectionError(str(err)) from err

        if "/account/login" in final_url or 'name="login-ident"' in html:
            raise IliadAuthError("Credenziali Iliad non valide o sessione non autenticata")

        return parse_account_page(html)
