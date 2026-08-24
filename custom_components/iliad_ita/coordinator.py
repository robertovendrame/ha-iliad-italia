"""Data coordinator for Iliad Italia."""

from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import CookieJar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IliadAuthError, IliadClient, IliadConnectionError, IliadData, IliadParseError
from .const import (
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class IliadDataUpdateCoordinator(DataUpdateCoordinator[IliadData]):
    """Coordinate refreshes from the Iliad personal area."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        session = async_create_clientsession(hass, cookie_jar=CookieJar())
        self._client = IliadClient(
            session,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        interval_hours = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL_HOURS,
                DEFAULT_UPDATE_INTERVAL_HOURS,
            )
        )
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=interval_hours),
        )

    async def _async_update_data(self) -> IliadData:
        try:
            return await self._client.async_fetch_data()
        except IliadAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (IliadConnectionError, IliadParseError) as err:
            raise UpdateFailed(str(err)) from err
