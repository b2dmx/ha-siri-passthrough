"""Config flow for Siri Passthrough."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_BRIDGE_URL, CONF_TARGET, DEFAULT_BRIDGE_URL, DOMAIN
from .discovery import find_bridge, probe


class SiriPassthroughConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the bridge URL, and check something answers on it."""

    VERSION = 1

    def __init__(self) -> None:
        self._suggested: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if self._suggested is None:
            # Probe before drawing the form, so the field is pre-filled with a
            # URL that actually works rather than one the user has to derive.
            self._suggested = await find_bridge(self.hass)

        if user_input is not None:
            url = str(user_input[CONF_BRIDGE_URL]).rstrip("/")
            if not await probe(self.hass, url):
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
                            CONF_BRIDGE_URL, self._suggested or DEFAULT_BRIDGE_URL
                        ),
                    ): str,
                    vol.Optional(CONF_TARGET): vol.Coerce(int),
                }
            ),
            errors=errors,
        )
