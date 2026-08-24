"""Sensors for Iliad Italia."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import IliadData
from .const import DOMAIN
from .coordinator import IliadDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class IliadSensorEntityDescription(SensorEntityDescription):
    """Describe an Iliad sensor."""

    value_fn: Callable[[IliadData], float | None]


SENSORS: tuple[IliadSensorEntityDescription, ...] = (
    IliadSensorEntityDescription(
        key="balance",
        translation_key="balance",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.balance_eur,
    ),
    IliadSensorEntityDescription(
        key="data_used",
        translation_key="data_used",
        icon="mdi:progress-download",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.data_used_gb,
    ),
    IliadSensorEntityDescription(
        key="data_remaining",
        translation_key="data_remaining",
        icon="mdi:progress-check",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.data_remaining_gb,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iliad sensors."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    async_add_entities(IliadSensor(coordinator, entry, description) for description in SENSORS)


class IliadSensor(CoordinatorEntity[IliadDataUpdateCoordinator], SensorEntity):
    """Representation of an Iliad account value."""

    entity_description: IliadSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
        description: IliadSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        account_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{account_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=entry.title,
            manufacturer="Iliad Italia",
            model="SIM / account mobile",
        )

    @property
    def native_value(self) -> float | None:
        """Return current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
