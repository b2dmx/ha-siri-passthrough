"""Config flow for Siri Passthrough."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BRIDGE_URL, CONF_TARGET, DEFAULT_BRIDGE_URL, DOMAIN


class SiriPassthroughConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the bridge URL, and check something answers on it."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = str(user_input[CONF_BRIDGE_URL]).rstrip("/")
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(
                    f"{url}/state", timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status >= 400:
                        errors["base"] = "cannot_connect"
                    else:
                        await resp.json(content_type=None)
            except (aiohttp.ClientError, TimeoutError):
                # The most common cause by far is the add-on's control API still
                # being loopback-only. Home Assistant runs in its own container,
                # so it counts as "a different machine" for that setting.
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                data = {CONF_BRIDGE_URL: url}
                if user_input.get(CONF_TARGET) not in (None, ""):
                    data[CONF_TARGET] = int(user_input[CONF_TARGET])
                return self.async_create_entry(title="Siri Passthrough", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BRIDGE_URL,
                        default=(user_input or {}).get(
                            CONF_BRIDGE_URL, DEFAULT_BRIDGE_URL
                        ),
                    ): str,
                    vol.Optional(CONF_TARGET): vol.Coerce(int),
                }
            ),
            errors=errors,
        )
