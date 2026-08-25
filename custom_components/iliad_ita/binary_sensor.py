"""Binary sensors for Iliad Italia."""

from __future__ import annotations

import calendar
from datetime import date

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
from homeassistant.util import dt as dt_util

from .api import IliadData
from .const import (
    CONF_CREDIT_THRESHOLD_EUR,
    CONF_DATA_THRESHOLD_GB,
    CONF_DATA_THRESHOLD_PERCENT,
    DEFAULT_CREDIT_THRESHOLD_EUR,
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

LOW_CREDIT_DESCRIPTION = BinarySensorEntityDescription(
    key="low_credit",
    translation_key="low_credit",
    icon="mdi:cash-alert",
    device_class=BinarySensorDeviceClass.PROBLEM,
)

PROJECTED_EXHAUSTION_DESCRIPTION = BinarySensorEntityDescription(
    key="projected_data_exhaustion",
    translation_key="projected_data_exhaustion",
    icon="mdi:chart-line-variant",
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


def _previous_month_same_day(value: date) -> date:
    """Infer the previous monthly renewal date as a fallback."""
    year = value.year
    month = value.month - 1
    if month == 0:
        month = 12
        year -= 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _cycle_start(data: IliadData) -> date | None:
    """Return the real reference-period start, with a legacy fallback."""
    if data.period_start is not None:
        return data.period_start
    if data.renewal_date is not None:
        return _previous_month_same_day(data.renewal_date)
    return None


def _projected_remaining_at_renewal(data: IliadData) -> float | None:
    """Project remaining GB at renewal from average usage in the current cycle."""
    if (
        data.renewal_date is None
        or data.data_used_gb is None
        or data.data_remaining_gb is None
    ):
        return None

    today = dt_util.now().date()
    days_remaining = (data.renewal_date - today).days
    if days_remaining < 0:
        return None

    cycle_start = _cycle_start(data)
    if cycle_start is None:
        return None
    elapsed_days = (today - cycle_start).days
    if elapsed_days <= 0:
        return None

    average_daily_usage = data.data_used_gb / elapsed_days
    return data.data_remaining_gb - (average_daily_usage * days_remaining)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iliad binary sensors."""
    coordinator: IliadDataUpdateCoordinator = entry.runtime_data
    async_add_entities(
        [
            IliadLowDataBinarySensor(coordinator, entry),
            IliadLowCreditBinarySensor(coordinator, entry),
            IliadProjectedDataExhaustionBinarySensor(coordinator, entry),
        ]
    )


class IliadBinarySensorBase(
    CoordinatorEntity[IliadDataUpdateCoordinator], BinarySensorEntity
):
    """Base class for Iliad problem binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        account_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{account_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=entry.title,
            manufacturer="Iliad Italia",
            model="SIM / account mobile",
        )


class IliadLowDataBinarySensor(IliadBinarySensorBase):
    """Indicate when remaining mobile data is below a configured threshold."""

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, LOW_DATA_DESCRIPTION)

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
        """Expose active data thresholds for dashboards and automations."""
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


class IliadLowCreditBinarySensor(IliadBinarySensorBase):
    """Indicate when available credit is below the configured threshold."""

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, LOW_CREDIT_DESCRIPTION)

    @property
    def is_on(self) -> bool | None:
        """Return true when available credit reaches the configured threshold."""
        balance = self.coordinator.data.balance_eur
        if balance is None:
            return None
        threshold = float(
            self._entry.options.get(
                CONF_CREDIT_THRESHOLD_EUR,
                DEFAULT_CREDIT_THRESHOLD_EUR,
            )
        )
        return balance <= threshold

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        """Expose the active credit threshold."""
        return {
            "threshold_eur": float(
                self._entry.options.get(
                    CONF_CREDIT_THRESHOLD_EUR,
                    DEFAULT_CREDIT_THRESHOLD_EUR,
                )
            )
        }


class IliadProjectedDataExhaustionBinarySensor(IliadBinarySensorBase):
    """Indicate when current usage pace is projected to exhaust data before renewal."""

    def __init__(
        self,
        coordinator: IliadDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, PROJECTED_EXHAUSTION_DESCRIPTION)

    @property
    def is_on(self) -> bool | None:
        """Return true when projected remaining data at renewal is below zero."""
        projected = _projected_remaining_at_renewal(self.coordinator.data)
        if projected is None:
            return None
        return projected < 0

    @property
    def extra_state_attributes(self) -> dict[str, float | str | None]:
        """Expose projection inputs for dashboards and diagnostics."""
        data = self.coordinator.data
        projected = _projected_remaining_at_renewal(data)
        return {
            "period_start": data.period_start.isoformat() if data.period_start else None,
            "period_end": data.period_end.isoformat() if data.period_end else None,
            "renewal_date": data.renewal_date.isoformat() if data.renewal_date else None,
            "projected_remaining_gb": projected,
        }
