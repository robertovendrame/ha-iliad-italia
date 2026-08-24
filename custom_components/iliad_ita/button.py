"""Buttons for Iliad Italia."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IliadDataUpdateCoordinator

REFRESH_BUTTON = ButtonEntityDescription(
    key="refresh",
    translation_key="refresh",
    icon="mdi:refresh",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iliad buttons."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    async_add_entities([IliadRefreshButton(coordinator, entry)])


class IliadRefreshButton(CoordinatorEntity[IliadDataUpdateCoordinator], ButtonEntity):
    """Button to force an immediate Iliad account refresh."""

    entity_description = REFRESH_BUTTON
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        account_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{account_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=entry.title,
            manufacturer="Iliad Italia",
            model="SIM / account mobile",
        )

    async def async_press(self) -> None:
        """Request an immediate refresh from Iliad."""
        await self.coordinator.async_request_refresh()
