"""Notice when the chain is broken, and say which link.

There are four things between a held microphone button and Siri, and when one
of them is wrong nothing announces it -- the mic just appears to do nothing.
These checks put the answer in Repairs instead.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import CONF_BRIDGE_URL, DOMAIN
from .discovery import probe

_LOGGER = logging.getLogger(__name__)

ISSUE_UNREACHABLE = "bridge_unreachable"
ISSUE_UNPAIRED = "bridge_unpaired"
ISSUE_NO_PIPELINE = "no_pipeline"


async def _bridge_state(hass: HomeAssistant, url: str) -> dict | None:
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    import aiohttp

    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"{url}/state", timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            if resp.status >= 400:
                return None
            return await resp.json(content_type=None)
    except Exception:  # noqa: BLE001 -- any failure here means "cannot tell"
        return None


def _pipeline_uses_us(hass: HomeAssistant) -> bool:
    """True if some assist pipeline is wired to our speech-to-text entity."""
    try:
        from homeassistant.components.assist_pipeline.pipeline import (
            async_get_pipeline_store,
        )

        store = async_get_pipeline_store(hass)
    except Exception:  # noqa: BLE001 -- internal API; absence is not a failure
        return True  # cannot tell, so do not nag

    stt_ids = {
        s.entity_id
        for s in hass.states.async_all("stt")
        if s.entity_id.startswith("stt.siri_passthrough")
    }
    if not stt_ids:
        return True

    return any(p.stt_engine in stt_ids for p in store.data.values())


async def async_check(hass: HomeAssistant, entry_id: str) -> None:
    """Raise or clear the Repairs issues for one config entry."""
    conf = hass.data[DOMAIN][entry_id]
    url = str(conf[CONF_BRIDGE_URL]).rstrip("/")

    state = await _bridge_state(hass, url)

    def issue(key: str, on: bool, **placeholders: str) -> None:
        if on:
            ir.async_create_issue(
                hass, DOMAIN, key, is_fixable=False, severity=ir.IssueSeverity.WARNING,
                translation_key=key, translation_placeholders=placeholders or None,
            )
        else:
            ir.async_delete_issue(hass, DOMAIN, key)

    if state is None:
        issue(ISSUE_UNREACHABLE, True, url=url)
        # Everything downstream is unknowable while the bridge is silent.
        ir.async_delete_issue(hass, DOMAIN, ISSUE_UNPAIRED)
        return

    issue(ISSUE_UNREACHABLE, False)
    issue(ISSUE_UNPAIRED, not state.get("targets"))
    issue(ISSUE_NO_PIPELINE, not _pipeline_uses_us(hass))
