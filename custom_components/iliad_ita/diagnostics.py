"""Diagnostics support for Iliad Italia."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import IliadDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics without account identifiers or exact usage/credit values."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    data = coordinator.data

    return {
        "entry": {
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval is not None
                else None
            ),
        },
        "parsed_data": {
            "offer_name": data.offer_name,
            "offer_price_eur": data.offer_price_eur,
            "data_allowance_gb": data.data_allowance_gb,
            "balance_available": data.balance_eur is not None,
            "data_used_available": data.data_used_gb is not None,
            "data_remaining_available": data.data_remaining_gb is not None,
            "period_start": data.period_start.isoformat() if data.period_start else None,
            "period_end": data.period_end.isoformat() if data.period_end else None,
            "renewal_date": data.renewal_date.isoformat() if data.renewal_date else None,
            "fetched_at": data.fetched_at.isoformat(),
        },
    }
