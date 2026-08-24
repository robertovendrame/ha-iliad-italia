"""Config flow for Iliad Italia."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IliadAuthError, IliadClient, IliadConnectionError, IliadParseError
from .const import CONF_NAME, DEFAULT_NAME, DOMAIN


def account_key(username: str) -> str:
    """Return a stable, non-plain-text identifier for an Iliad account."""
    normalized = username.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


async def _validate_input(hass: HomeAssistant, data: Mapping[str, str]) -> None:
    """Validate Iliad credentials by fetching current account data."""
    client = IliadClient(
        async_get_clientsession(hass),
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )
    await client.async_fetch_data()


def _map_error(err: Exception) -> str:
    """Map client exceptions to config-flow error keys."""
    if isinstance(err, IliadAuthError):
        return "invalid_auth"
    if isinstance(err, IliadConnectionError):
        return "cannot_connect"
    return "cannot_parse"


class IliadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Iliad Italia config flow."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup of a new Iliad account."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = str(user_input[CONF_USERNAME]).strip()
            password = str(user_input[CONF_PASSWORD])
            name = str(user_input[CONF_NAME]).strip() or DEFAULT_NAME
            data = {
                CONF_NAME: name,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            }

            await self.async_set_unique_id(account_key(username))
            self._abort_if_unique_id_configured()

            try:
                await _validate_input(self.hass, data)
            except (IliadAuthError, IliadConnectionError, IliadParseError) as err:
                errors["base"] = _map_error(err)
            else:
                return self.async_create_entry(title=name, data=data)

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

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication for an existing Iliad account."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate a replacement password and reload the entry."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            data = {
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: str(user_input[CONF_PASSWORD]),
            }
            try:
                await _validate_input(self.hass, data)
            except (IliadAuthError, IliadConnectionError, IliadParseError) as err:
                errors["base"] = _map_error(err)
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: data[CONF_PASSWORD]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow changing the friendly name and credentials of an entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            username = str(user_input[CONF_USERNAME]).strip()
            password = str(user_input[CONF_PASSWORD])
            name = str(user_input[CONF_NAME]).strip() or DEFAULT_NAME
            data = {
                CONF_NAME: name,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            }

            await self.async_set_unique_id(account_key(username))
            self._abort_if_unique_id_mismatch(reason="wrong_account")

            try:
                await _validate_input(self.hass, data)
            except (IliadAuthError, IliadConnectionError, IliadParseError) as err:
                errors["base"] = _map_error(err)
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data=data,
                    title=name,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=entry.title): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data[CONF_USERNAME],
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
