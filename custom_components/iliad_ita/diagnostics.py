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
    """Return privacy-safe diagnostics for an Iliad config entry."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    data = coordinator.data

    return {
        "entry": {
            "title": entry.title,
            "unique_id": entry.unique_id,
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
            "balance_eur": data.balance_eur,
            "data_used_gb": data.data_used_gb,
            "data_remaining_gb": data.data_remaining_gb,
            "renewal_date": data.renewal_date.isoformat() if data.renewal_date else None,
            "fetched_at": data.fetched_at.isoformat(),
        },
    }
