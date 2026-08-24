"""Config flow for Iliad Italia."""

from __future__ import annotations

import hashlib

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IliadAuthError, IliadClient, IliadConnectionError, IliadParseError
from .const import CONF_NAME, DEFAULT_NAME, DOMAIN


def account_key(username: str) -> str:
    """Return a stable, non-plain-text identifier for an Iliad account."""
    normalized = username.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


async def _validate_input(hass: HomeAssistant, data: dict[str, str]) -> None:
    client = IliadClient(
        async_get_clientsession(hass),
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )
    await client.async_fetch_data()


class IliadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Iliad Italia config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            user_input[CONF_USERNAME] = username
            name = user_input[CONF_NAME].strip() or DEFAULT_NAME
            user_input[CONF_NAME] = name

            await self.async_set_unique_id(account_key(username))
            self._abort_if_unique_id_configured()

            try:
                await _validate_input(self.hass, user_input)
            except IliadAuthError:
                errors["base"] = "invalid_auth"
            except IliadConnectionError:
                errors["base"] = "cannot_connect"
            except IliadParseError:
                errors["base"] = "cannot_parse"
            else:
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
