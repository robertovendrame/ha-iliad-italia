"""Sensors for Iliad Italia."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import IliadData
from .const import DOMAIN
from .coordinator import IliadDataUpdateCoordinator

SensorValue = float | int | str | date | datetime | None


@dataclass(frozen=True, kw_only=True)
class IliadSensorEntityDescription(SensorEntityDescription):
    """Describe an Iliad sensor."""

    value_fn: Callable[[IliadData], SensorValue]


def _period_active(data: IliadData) -> bool | None:
    """Return whether today belongs to the parsed Iliad reference period."""
    if data.period_start is None or data.period_end is None:
        return None
    today = dt_util.now().date()
    return data.period_start <= today <= data.period_end


def _total_data(data: IliadData) -> float | None:
    if data.data_used_gb is None or data.data_remaining_gb is None:
        return None
    return data.data_used_gb + data.data_remaining_gb


def _allowance_or_calculated_total(data: IliadData) -> float | None:
    return data.data_allowance_gb if data.data_allowance_gb is not None else _total_data(data)


def _used_percent(data: IliadData) -> float | None:
    total = _allowance_or_calculated_total(data)
    if total is None or total <= 0 or data.data_used_gb is None:
        return None
    return (data.data_used_gb / total) * 100


def _remaining_percent(data: IliadData) -> float | None:
    total = _allowance_or_calculated_total(data)
    if total is None or total <= 0 or data.data_remaining_gb is None:
        return None
    return (data.data_remaining_gb / total) * 100


def _roaming_used_percent(data: IliadData) -> float | None:
    total = data.roaming_data_allowance_gb
    if total is None or total <= 0 or data.roaming_data_used_gb is None:
        return None
    return (data.roaming_data_used_gb / total) * 100


def _roaming_remaining_percent(data: IliadData) -> float | None:
    total = data.roaming_data_allowance_gb
    if total is None or total <= 0 or data.roaming_data_remaining_gb is None:
        return None
    return (data.roaming_data_remaining_gb / total) * 100


def _previous_month_same_day(value: date) -> date:
    year = value.year
    month = value.month - 1
    if month == 0:
        month = 12
        year -= 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _cycle_start(data: IliadData) -> date | None:
    if data.period_start is not None:
        return data.period_start
    if data.renewal_date is not None:
        return _previous_month_same_day(data.renewal_date)
    return None


def _renewal_date_value(data: IliadData) -> date | None:
    if _period_active(data) is False:
        return None
    return data.renewal_date


def _days_until_renewal(data: IliadData) -> int | None:
    if _period_active(data) is False or data.renewal_date is None:
        return None
    return (data.renewal_date - dt_util.now().date()).days


def _average_daily_usage(data: IliadData) -> float | None:
    if _period_active(data) is False or data.data_used_gb is None:
        return None
    cycle_start = _cycle_start(data)
    if cycle_start is None:
        return None
    elapsed_days = (dt_util.now().date() - cycle_start).days
    if elapsed_days <= 0:
        return None
    return data.data_used_gb / elapsed_days


def _daily_budget_to_renewal(data: IliadData) -> float | None:
    if _period_active(data) is False or data.data_remaining_gb is None:
        return None
    days = _days_until_renewal(data)
    if days is None or days <= 0:
        return None
    return data.data_remaining_gb / days


def _projected_remaining_at_renewal(data: IliadData) -> float | None:
    if _period_active(data) is False or data.data_remaining_gb is None:
        return None
    days = _days_until_renewal(data)
    average = _average_daily_usage(data)
    if days is None or days < 0 or average is None:
        return None
    return data.data_remaining_gb - (average * days)


SENSORS: tuple[IliadSensorEntityDescription, ...] = (
    IliadSensorEntityDescription(
        key="account_user_id",
        translation_key="account_user_id",
        icon="mdi:account-key-outline",
        value_fn=lambda data: data.account_user_id,
    ),
    IliadSensorEntityDescription(
        key="phone_number",
        translation_key="phone_number",
        icon="mdi:phone",
        value_fn=lambda data: data.phone_number,
    ),
    IliadSensorEntityDescription(
        key="offer_name",
        translation_key="offer_name",
        icon="mdi:sim",
        value_fn=lambda data: data.offer_name,
    ),
    IliadSensorEntityDescription(
        key="offer_price",
        translation_key="offer_price",
        icon="mdi:cash-sync",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.offer_price_eur,
    ),
    IliadSensorEntityDescription(
        key="balance",
        translation_key="balance",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.balance_eur,
    ),
    IliadSensorEntityDescription(
        key="data_allowance",
        translation_key="data_allowance",
        icon="mdi:database-check-outline",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.data_allowance_gb,
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
    IliadSensorEntityDescription(
        key="data_total_calculated",
        translation_key="data_total_calculated",
        icon="mdi:database",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=_total_data,
    ),
    IliadSensorEntityDescription(
        key="data_used_percent",
        translation_key="data_used_percent",
        icon="mdi:chart-donut",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=_used_percent,
    ),
    IliadSensorEntityDescription(
        key="data_remaining_percent",
        translation_key="data_remaining_percent",
        icon="mdi:chart-donut-variant",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=_remaining_percent,
    ),
    IliadSensorEntityDescription(
        key="roaming_data_allowance",
        translation_key="roaming_data_allowance",
        icon="mdi:earth",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.roaming_data_allowance_gb,
    ),
    IliadSensorEntityDescription(
        key="roaming_data_used",
        translation_key="roaming_data_used",
        icon="mdi:earth-arrow-right",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.roaming_data_used_gb,
    ),
    IliadSensorEntityDescription(
        key="roaming_data_remaining",
        translation_key="roaming_data_remaining",
        icon="mdi:earth-check",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: data.roaming_data_remaining_gb,
    ),
    IliadSensorEntityDescription(
        key="roaming_data_used_percent",
        translation_key="roaming_data_used_percent",
        icon="mdi:chart-donut",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=_roaming_used_percent,
    ),
    IliadSensorEntityDescription(
        key="roaming_data_remaining_percent",
        translation_key="roaming_data_remaining_percent",
        icon="mdi:chart-donut-variant",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=_roaming_remaining_percent,
    ),
    IliadSensorEntityDescription(
        key="calls_duration",
        translation_key="calls_duration",
        icon="mdi:phone-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.calls_duration_seconds,
    ),
    IliadSensorEntityDescription(
        key="calls_cost",
        translation_key="calls_cost",
        icon="mdi:phone-alert-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.calls_cost_eur,
    ),
    IliadSensorEntityDescription(
        key="sms_count",
        translation_key="sms_count",
        icon="mdi:message-text-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="SMS",
        suggested_display_precision=0,
        value_fn=lambda data: data.sms_count,
    ),
    IliadSensorEntityDescription(
        key="sms_cost",
        translation_key="sms_cost",
        icon="mdi:message-alert-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.sms_cost_eur,
    ),
    IliadSensorEntityDescription(
        key="mms_count",
        translation_key="mms_count",
        icon="mdi:message-image-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="MMS",
        suggested_display_precision=0,
        value_fn=lambda data: data.mms_count,
    ),
    IliadSensorEntityDescription(
        key="mms_cost",
        translation_key="mms_cost",
        icon="mdi:message-alert-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.mms_cost_eur,
    ),
    IliadSensorEntityDescription(
        key="period_start",
        translation_key="period_start",
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: data.period_start,
    ),
    IliadSensorEntityDescription(
        key="period_end",
        translation_key="period_end",
        icon="mdi:calendar-end",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: data.period_end,
    ),
    IliadSensorEntityDescription(
        key="renewal_date",
        translation_key="renewal_date",
        icon="mdi:calendar-refresh",
        device_class=SensorDeviceClass.DATE,
        value_fn=_renewal_date_value,
    ),
    IliadSensorEntityDescription(
        key="days_until_renewal",
        translation_key="days_until_renewal",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        suggested_display_precision=0,
        value_fn=_days_until_renewal,
    ),
    IliadSensorEntityDescription(
        key="average_daily_usage",
        translation_key="average_daily_usage",
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="GB/day",
        suggested_display_precision=2,
        value_fn=_average_daily_usage,
    ),
    IliadSensorEntityDescription(
        key="daily_budget_to_renewal",
        translation_key="daily_budget_to_renewal",
        icon="mdi:chart-timeline-variant",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="GB/day",
        suggested_display_precision=2,
        value_fn=_daily_budget_to_renewal,
    ),
    IliadSensorEntityDescription(
        key="projected_remaining_at_renewal",
        translation_key="projected_remaining_at_renewal",
        icon="mdi:chart-line",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=2,
        value_fn=_projected_remaining_at_renewal,
    ),
    IliadSensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.fetched_at,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
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
    def native_value(self) -> SensorValue:
        return self.entity_description.value_fn(self.coordinator.data)
