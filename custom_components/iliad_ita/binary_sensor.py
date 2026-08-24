"""Binary sensors for Iliad Italia."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import IliadData
from .const import (
    CONF_DATA_THRESHOLD_GB,
    CONF_DATA_THRESHOLD_PERCENT,
    DEFAULT_DATA_THRESHOLD_GB,
    DEFAULT_DATA_THRESHOLD_PERCENT,
    DOMAIN,
)
from .coordinator import IliadDataUpdateCoordinator

LOW_DATA_DESCRIPTION = BinarySensorEntityDescription(
    key="low_data",
    translation_key="low_data",
    icon="mdi:database-alert-outline",
    device_class=BinarySensorDeviceClass.PROBLEM,
)


def _remaining_percent(data: IliadData) -> float | None:
    """Calculate the percentage of data remaining from parsed values."""
    if data.data_used_gb is None or data.data_remaining_gb is None:
        return None
    total = data.data_used_gb + data.data_remaining_gb
    if total <= 0:
        return None
    return (data.data_remaining_gb / total) * 100


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iliad binary sensors."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    async_add_entities([IliadLowDataBinarySensor(coordinator, entry)])


class IliadLowDataBinarySensor(
    CoordinatorEntity[IliadDataUpdateCoordinator], BinarySensorEntity
):
    """Indicate when remaining mobile data is below a configured threshold."""

    entity_description = LOW_DATA_DESCRIPTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        account_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{account_id}_low_data"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=entry.title,
            manufacturer="Iliad Italia",
            model="SIM / account mobile",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if either configured remaining-data threshold is reached."""
        data = self.coordinator.data
        remaining_gb = data.data_remaining_gb
        remaining_percent = _remaining_percent(data)
        if remaining_gb is None and remaining_percent is None:
            return None

        threshold_gb = float(
            self._entry.options.get(
                CONF_DATA_THRESHOLD_GB,
                DEFAULT_DATA_THRESHOLD_GB,
            )
        )
        threshold_percent = float(
            self._entry.options.get(
                CONF_DATA_THRESHOLD_PERCENT,
                DEFAULT_DATA_THRESHOLD_PERCENT,
            )
        )

        below_gb = remaining_gb is not None and remaining_gb <= threshold_gb
        below_percent = (
            remaining_percent is not None and remaining_percent <= threshold_percent
        )
        return below_gb or below_percent

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        """Expose active thresholds for dashboards and automations."""
        return {
            "threshold_gb": float(
                self._entry.options.get(
                    CONF_DATA_THRESHOLD_GB,
                    DEFAULT_DATA_THRESHOLD_GB,
                )
            ),
            "threshold_percent": float(
                self._entry.options.get(
                    CONF_DATA_THRESHOLD_PERCENT,
                    DEFAULT_DATA_THRESHOLD_PERCENT,
                )
            ),
        }
