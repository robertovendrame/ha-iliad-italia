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
    roaming_data_used_gb: float | None
    roaming_data_remaining_gb: float | None
    roaming_data_allowance_gb: float | None
    calls_duration_seconds: int | None
    calls_cost_eur: float | None
    sms_count: int | None
    sms_cost_eur: float | None
    mms_count: int | None
    mms_cost_eur: float | None
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
    factors = {
        "B": 1 / 1_000_000_000,
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

_DATA_PAIR_RE = re.compile(
    r"(\d+[\d.,]*)\s*(B|KB|MB|GB|TB)\s*/\s*"
    r"(\d+[\d.,]*)\s*(B|KB|MB|GB|TB)",
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


def _normalize_offer_candidate(text: str) -> str | None:
    """Extract and normalize an offer-like label from a DOM text fragment."""
    normalized = " ".join(text.split())
    if not re.search(r"\bofferta\b", normalized, flags=re.IGNORECASE):
        return None

    candidate = re.split(
        r"\s*(?:[●•·|]|Credito\s*:|Si\s+rinnova\b|Periodo\s+di\s+riferimento\b)",
        normalized,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" :-–—●•·|")

    match = re.search(r"\bOfferta\b(?:\s+[^●•·|]{1,90})?", candidate, flags=re.IGNORECASE)
    if not match:
        return None

    value = " ".join(match.group(0).split()).strip(" :-–—●•·|")
    if not 3 < len(value) <= 100:
        return None
    return value


def _offer_candidate_score(value: str) -> int:
    """Prefer specific commercial names over generic portal labels."""
    lower = value.casefold()
    score = 0
    if re.search(r"\d", value):
        score += 8
    if "dati" in lower or "giga" in lower or "gb" in lower:
        score += 5
    if len(value.split()) >= 3:
        score += 2
    if lower in {"offerta", "offerta mobile", "la tua offerta", "dettaglio offerta mobile"}:
        score -= 20
    elif "mobile" in lower and not re.search(r"\d", value):
        score -= 5
    return score


def _parse_offer_name_from_dom(soup: BeautifulSoup) -> str | None:
    """Select the most specific offer label exposed by the page DOM."""
    candidates: set[str] = set()

    for text_node in soup.find_all(string=re.compile(r"\bofferta\b", re.IGNORECASE)):
        value = _normalize_offer_candidate(str(text_node))
        if value:
            candidates.add(value)

        parent = text_node.parent
        for _ in range(3):
            if parent is None:
                break
            value = _normalize_offer_candidate(parent.get_text(" ", strip=True))
            if value:
                candidates.add(value)
            parent = parent.parent

    if not candidates:
        return None

    best = max(candidates, key=lambda value: (_offer_candidate_score(value), -len(value)))
    return best if _offer_candidate_score(best) >= 0 else None


def _parse_offer_metadata(text: str) -> tuple[str | None, float | None, float | None]:
    """Parse offer name fallback, official data allowance and renewal price."""
    normalized = " ".join(text.split())

    offer_name = None
    offer_match = re.search(
        r"\b(Offerta\s+.+?)(?=\s*[●•·]\s*Credito\b|\s+Credito\s*:)",
        normalized,
        flags=re.IGNORECASE,
    )
    if offer_match:
        offer_name = " ".join(offer_match.group(1).split()).strip(" :-–—●•·|")

    data_allowance_gb = None
    allowance_match = _DATA_PAIR_RE.search(normalized)
    if allowance_match:
        data_allowance_gb = _size_to_gb(allowance_match.group(3), allowance_match.group(4))

    offer_price_eur = None
    renewal_match = re.search(r"si\s+rinnova\b(.{0,120})", normalized, flags=re.IGNORECASE)
    if renewal_match:
        price_match = re.search(r"\ba\s*([\d.,]+)\s*€", renewal_match.group(1), flags=re.IGNORECASE)
        if price_match:
            offer_price_eur = _decimal(price_match.group(1))

    return offer_name, data_allowance_gb, offer_price_eur


def _data_pair(match: re.Match[str]) -> tuple[float, float]:
    return (
        _size_to_gb(match.group(1), match.group(2)),
        _size_to_gb(match.group(3), match.group(4)),
    )


def _parse_data_buckets(soup: BeautifulSoup) -> list[tuple[float, float, float | None]]:
    """Parse national and roaming data buckets from varying Iliad layouts.

    Older/current Iliad layouts do not consistently use the same CSS classes for
    the Estero tab. We therefore collect explicit DOM pairs first and then scan
    the flattened account text for additional ``used / allowance`` pairs. The
    latter fixes layouts where the roaming values exist in the HTML but are not
    represented by ``span.red`` elements.
    """
    pairs: list[tuple[float, float]] = []

    def add_pair(pair: tuple[float, float]) -> None:
        if not any(abs(pair[0] - old[0]) < 1e-9 and abs(pair[1] - old[1]) < 1e-9 for old in pairs):
            pairs.append(pair)

    for node in soup.find_all(string=_DATA_PAIR_RE):
        match = _DATA_PAIR_RE.search(str(node))
        if match:
            add_pair(_data_pair(match))

    page_text = soup.get_text(" ", strip=True)
    for match in _DATA_PAIR_RE.finditer(page_text):
        add_pair(_data_pair(match))

    remaining_values: list[float] = []
    for node in soup.select("span.big.red"):
        value_match = re.search(r"([\d.,]+)", node.get_text(" ", strip=True))
        unit_node = node.find_next("span", class_=["small", "red"])
        unit_match = (
            re.search(
                r"\b(B|KB|MB|GB|TB)\b",
                unit_node.get_text(" ", strip=True),
                re.IGNORECASE,
            )
            if unit_node
            else None
        )
        if value_match and unit_match:
            remaining_values.append(_size_to_gb(value_match.group(1), unit_match.group(1)))

    buckets: list[tuple[float, float, float | None]] = []
    for index, (used, allowance) in enumerate(pairs):
        explicit_remaining = remaining_values[index] if index < len(remaining_values) else None
        calculated_remaining = max(0.0, allowance - used)
        remaining = explicit_remaining if explicit_remaining is not None else calculated_remaining
        buckets.append((used, allowance, remaining))

    return buckets


def _parse_duration_seconds(value: str) -> int | None:
    """Convert Iliad duration strings such as ``1h 2m 3s`` to seconds."""
    normalized = " ".join(value.split()).lower()
    matches = re.findall(r"(\d+)\s*([hms])", normalized)
    if not matches:
        return None
    total = 0
    for number, unit in matches:
        amount = int(number)
        total += amount * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


def _parse_usage_counters(text: str) -> tuple[int | None, float | None, int | None, float | None, int | None, float | None]:
    """Parse voice/SMS/MMS counters from the current consumption summary."""
    normalized = " ".join(text.split())

    calls_duration_seconds = None
    duration_match = re.search(
        r"(?:Durata|Chiamate)\s*:\s*((?:\d+\s*[hms]\s*)+)",
        normalized,
        flags=re.IGNORECASE,
    )
    if duration_match:
        calls_duration_seconds = _parse_duration_seconds(duration_match.group(1))

    calls_cost_eur = None
    calls_cost_match = re.search(
        r"Consumi\s+voce\s*:\s*([\d.,]+)\s*€",
        normalized,
        flags=re.IGNORECASE,
    )
    if calls_cost_match:
        calls_cost_eur = _decimal(calls_cost_match.group(1))

    sms_count = None
    sms_match = re.search(r"\b(\d+)\s+SMS\b", normalized, flags=re.IGNORECASE)
    if sms_match:
        sms_count = int(sms_match.group(1))

    sms_cost_eur = None
    sms_cost_match = re.search(
        r"SMS\s+extra\s*:\s*([\d.,]+)\s*€",
        normalized,
        flags=re.IGNORECASE,
    )
    if sms_cost_match:
        sms_cost_eur = _decimal(sms_cost_match.group(1))

    mms_count = None
    mms_match = re.search(r"\b(\d+)\s+MMS\b", normalized, flags=re.IGNORECASE)
    if mms_match:
        mms_count = int(mms_match.group(1))

    mms_cost_eur = None
    mms_cost_match = re.search(
        r"Consumi\s+MMS\s*:\s*([\d.,]+)\s*€",
        normalized,
        flags=re.IGNORECASE,
    )
    if mms_cost_match:
        mms_cost_eur = _decimal(mms_cost_match.group(1))

    return (
        calls_duration_seconds,
        calls_cost_eur,
        sms_count,
        sms_cost_eur,
        mms_count,
        mms_cost_eur,
    )


def parse_account_page(html: str) -> IliadData:
    """Parse Iliad's consumi-e-credito HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    balance = None
    balance_node = soup.select_one("b.red[data-cs-mask]")
    if balance_node:
        match = re.search(r"([\d.,]+)\s*€", balance_node.get_text(" ", strip=True))
        if match:
            balance = _decimal(match.group(1))

    page_text = soup.get_text(" ", strip=True)
    buckets = _parse_data_buckets(soup)

    used = buckets[0][0] if buckets else None
    data_allowance_gb = buckets[0][1] if buckets else None
    remaining = buckets[0][2] if buckets else None

    roaming_used = buckets[1][0] if len(buckets) > 1 else None
    roaming_allowance = buckets[1][1] if len(buckets) > 1 else None
    roaming_remaining = buckets[1][2] if len(buckets) > 1 else None

    size_pattern = re.compile(r"(\d+[\d.,]*)\s*(B|KB|MB|GB|TB)", re.IGNORECASE)
    if remaining is None:
        remaining_node = soup.select_one("span.big.red")
        if remaining_node:
            value_match = re.search(r"([\d.,]+)", remaining_node.get_text(" ", strip=True))
            unit_node = remaining_node.find_next("span", class_=["small", "red"]) or soup.select_one("span.small.red")
            unit_match = (
                re.search(r"\b(B|KB|MB|GB|TB)\b", unit_node.get_text(" ", strip=True), re.IGNORECASE)
                if unit_node
                else None
            )
            if value_match and unit_match:
                remaining = _size_to_gb(value_match.group(1), unit_match.group(1))

    if used is None:
        for node in soup.select("span.red"):
            match = size_pattern.search(node.get_text(" ", strip=True))
            if match:
                used = _size_to_gb(match.group(1), match.group(2))
                break

    (
        calls_duration_seconds,
        calls_cost_eur,
        sms_count,
        sms_cost_eur,
        mms_count,
        mms_cost_eur,
    ) = _parse_usage_counters(page_text)

    fetched_at = datetime.now(timezone.utc)
    period_start, period_end = _parse_reference_period(page_text, fetched_at.date())
    renewal_date = _parse_renewal_date(page_text, fetched_at.date(), period_end)
    offer_name_fallback, allowance_fallback, offer_price_eur = _parse_offer_metadata(page_text)
    offer_name = _parse_offer_name_from_dom(soup) or offer_name_fallback
    if data_allowance_gb is None:
        data_allowance_gb = allowance_fallback

    if balance is None and used is None and remaining is None:
        raise IliadParseError("Nessun dato Iliad riconosciuto nella pagina account")

    return IliadData(
        balance_eur=balance,
        data_used_gb=used,
        data_remaining_gb=remaining,
        data_allowance_gb=data_allowance_gb,
        roaming_data_used_gb=roaming_used,
        roaming_data_remaining_gb=roaming_remaining,
        roaming_data_allowance_gb=roaming_allowance,
        calls_duration_seconds=calls_duration_seconds,
        calls_cost_eur=calls_cost_eur,
        sms_count=sms_count,
        sms_cost_eur=sms_cost_eur,
        mms_count=mms_count,
        mms_cost_eur=mms_cost_eur,
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
