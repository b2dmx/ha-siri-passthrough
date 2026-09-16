"""Notice when the chain is broken, and say which link.

There are four things between a held microphone button and Siri, and when one
of them is wrong nothing announces it -- the mic just appears to do nothing.
These checks put the answer in Repairs instead.
"""

from __future__ import annotations

import logging

from homeassistant.components.assist_pipeline.pipeline import async_get_pipelines
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir

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


def _our_stt_entity(hass: HomeAssistant, entry_id: str) -> str | None:
    """Our speech-to-text entity id, by registry lookup rather than by guess."""
    return er.async_get(hass).async_get_entity_id("stt", DOMAIN, f"{entry_id}-stt")


def _pipeline_uses_us(hass: HomeAssistant, entry_id: str) -> bool:
    """True if some assist pipeline is wired to our speech-to-text entity."""
    ours = _our_stt_entity(hass, entry_id)
    if ours is None:
        return True  # not registered yet; nothing to report

    try:
        pipelines = async_get_pipelines(hass)
    except Exception as err:  # noqa: BLE001 -- cannot tell, so do not nag
        _LOGGER.debug("Could not read the pipelines (%s)", err)
        return True

    return any(p.stt_engine == ours for p in pipelines)


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
    issue(ISSUE_NO_PIPELINE, not _pipeline_uses_us(hass, entry_id))
