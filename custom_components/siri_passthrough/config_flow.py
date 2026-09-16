"""Config flow: walk the whole chain, not just this integration's own settings.

Setting this up by hand means an add-on repository, a hidden control-API
toggle, a pairing dance in the Home app, and a hand-built assist pipeline whose
two engines must both be right. Most of that can be checked or done here, so
the parts a person must do are the only parts they are asked for.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BRIDGE_URL,
    CONF_CREATE_PIPELINE,
    CONF_FALLBACK_AGENT,
    CONF_FALLBACK_STT,
    CONF_PIPELINE_NAME,
    CONF_SIRI_WHEN_ENTITY,
    CONF_SIRI_WHEN_STATES,
    CONF_TARGET,
    DEFAULT_BRIDGE_URL,
    DEFAULT_PIPELINE_NAME,
    DEFAULT_SIRI_WHEN_STATES,
    DOMAIN,
)
from .discovery import find_bridge, probe, read_state


def routing_schema(current: dict) -> vol.Schema:
    """Fields for deciding which utterances belong to Siri."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_SIRI_WHEN_ENTITY,
                description={"suggested_value": current.get(CONF_SIRI_WHEN_ENTITY)},
            ): selector.EntitySelector(),
            vol.Optional(
                CONF_SIRI_WHEN_STATES,
                default=current.get(CONF_SIRI_WHEN_STATES, DEFAULT_SIRI_WHEN_STATES),
            ): str,
            vol.Optional(
                CONF_FALLBACK_STT,
                description={"suggested_value": current.get(CONF_FALLBACK_STT)},
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="stt")),
            vol.Optional(
                CONF_FALLBACK_AGENT,
                description={"suggested_value": current.get(CONF_FALLBACK_AGENT)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="conversation")
            ),
        }
    )


class SiriPassthroughConfigFlow(ConfigFlow, domain=DOMAIN):
    """Bridge, then pairing, then a pipeline."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SiriPassthroughOptionsFlow()

    def __init__(self) -> None:
        self._suggested: str | None = None
        self._url: str | None = None
        self._target: int | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if self._suggested is None:
            # Probe before drawing the form, so the field is pre-filled with a
            # URL that works rather than one the user has to derive. Nothing in
            # the Home Assistant UI exposes it.
            self._suggested = await find_bridge(self.hass)

        if user_input is not None:
            url = str(user_input[CONF_BRIDGE_URL]).rstrip("/")
            if not await probe(self.hass, url):
                # Almost always the add-on's control API still being loopback
                # only. Home Assistant is its own container, so it counts as a
                # different machine for that setting.
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                self._url = url
                if user_input.get(CONF_TARGET) not in (None, ""):
                    self._target = int(user_input[CONF_TARGET])
                return await self.async_step_pair()

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

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Wait for an Apple TV to appear, which only pairing can produce."""
        state = await read_state(self.hass, self._url or "")
        targets = (state or {}).get("targets") or {}

        if targets:
            return await self.async_step_finish()

        errors: dict[str, str] = {}
        if user_input is not None:
            # They pressed continue and there is still nothing: say so rather
            # than letting setup finish into something that cannot work.
            errors["base"] = "still_unpaired"

        return self.async_show_form(
            step_id="pair", data_schema=vol.Schema({}), errors=errors
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Offer to build the pipeline, and take the routing rule while here."""
        if user_input is not None:
            data: dict[str, Any] = {CONF_BRIDGE_URL: self._url}
            if self._target is not None:
                data[CONF_TARGET] = self._target

            options = {k: v for k, v in user_input.items() if v not in (None, "")}
            return self.async_create_entry(
                title="Siri Passthrough", data=data, options=options
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_CREATE_PIPELINE, default=True): bool,
                vol.Optional(
                    CONF_PIPELINE_NAME, default=DEFAULT_PIPELINE_NAME
                ): str,
            }
        ).extend(routing_schema({}).schema)

        return self.async_show_form(step_id="finish", data_schema=schema)


class SiriPassthroughOptionsFlow(OptionsFlow):
    """Change routing after setup."""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=routing_schema(current)
        )
