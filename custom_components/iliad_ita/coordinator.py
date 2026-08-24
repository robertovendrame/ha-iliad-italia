"""Data coordinator for Iliad Italia."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IliadAuthError, IliadClient, IliadConnectionError, IliadData, IliadParseError
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IliadDataUpdateCoordinator(DataUpdateCoordinator[IliadData]):
    """Coordinate refreshes from the Iliad personal area."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self._client = IliadClient(
            async_get_clientsession(hass),
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> IliadData:
        try:
            return await self._client.async_fetch_data()
        except IliadAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (IliadConnectionError, IliadParseError) as err:
            raise UpdateFailed(str(err)) from err
