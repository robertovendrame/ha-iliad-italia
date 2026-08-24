"""Async client for Iliad Italia account data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
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


def _parse_renewal_date(text: str, reference: date) -> date | None:
    """Find a renewal date only in text located close to a renewal label."""
    normalized = " ".join(text.split())

    for keyword in re.finditer(r"rinnov\w*", normalized, flags=re.IGNORECASE):
        start = max(0, keyword.start() - 40)
        end = min(len(normalized), keyword.end() + 120)
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

        textual = re.search(
            r"\b(\d{1,2})\s+"
            r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
            r"settembre|ottobre|novembre|dicembre)"
            r"(?:\s+(\d{4}))?\b",
            window,
            flags=re.IGNORECASE,
        )
        if textual:
            day = int(textual.group(1))
            month = _ITALIAN_MONTHS[textual.group(2).lower()]
            year = int(textual.group(3)) if textual.group(3) else None
            parsed = _build_date(day, month, year, reference)
            if parsed is not None:
                return parsed

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
    renewal_date = _parse_renewal_date(
        soup.get_text(" ", strip=True),
        fetched_at.date(),
    )

    if balance is None and used is None and remaining is None:
        raise IliadParseError("Nessun dato Iliad riconosciuto nella pagina account")

    return IliadData(
        balance_eur=balance,
        data_used_gb=used,
        data_remaining_gb=remaining,
        renewal_date=renewal_date,
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
