"""Siri Passthrough -- put a Home Assistant voice satellite's microphone
straight onto Siri on an Apple TV.

The usual way to reach Siri from Home Assistant is to transcribe what you said,
then have Home Assistant read the transcript back out loud through TTS. That
works, but it cannot be fast: the utterance has to be *played* to Siri in real
time, on top of speech-to-text and synthesis. Several seconds, every time.

This integration skips all of it. It registers a speech-to-text provider that
does not transcribe -- it forwards the pipeline's live audio chunks to the
appletv-siri-voice bridge as they arrive, so Siri hears you while you are still
speaking. The only cost over a real Siri Remote is two LAN hops.

The bridge (https://github.com/marcusadolfsson/appletv-siri-voice) does the hard
part: it pairs as a HomeKit remote and holds the SIRI button down for the life
of the request body.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval

from . import health, pipelines
from .const import CONF_CREATE_PIPELINE, CONF_PIPELINE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.STT, Platform.CONVERSATION]

# Often enough that a broken chain is noticed the same evening, rare enough to
# be invisible.
CHECK_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Siri Passthrough from a config entry."""
    # Options win over the values captured at setup, so routing can be
    # changed later without removing and re-adding the integration.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        **entry.data,
        **{k: v for k, v in entry.options.items() if v not in (None, "")},
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if entry.options.get(CONF_CREATE_PIPELINE):
        # Only now do the entities exist to be named by a pipeline.
        await _create_pipeline(hass, entry)

    await health.async_check(hass, entry.entry_id)

    async def _recheck(_now) -> None:
        # A coroutine function handed straight to the tracker: it is awaited on
        # the event loop. Wrapping it in async_create_task from the callback
        # schedules from whatever thread fired the timer, which is not safe.
        await health.async_check(hass, entry.entry_id)

    entry.async_on_unload(
        async_track_time_interval(hass, _recheck, CHECK_INTERVAL)
    )
    entry.async_on_unload(entry.add_update_listener(_reload_on_change))
    return True


async def _create_pipeline(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Build the pipeline the flow offered, then stop offering it."""
    registry = er.async_get(hass)
    stt_id = registry.async_get_entity_id("stt", DOMAIN, f"{entry.entry_id}-stt")
    agent_id = registry.async_get_entity_id(
        "conversation", DOMAIN, f"{entry.entry_id}-conversation"
    )
    if stt_id and agent_id:
        await pipelines.async_create(
            hass,
            entry.options.get(CONF_PIPELINE_NAME) or "Siri",
            stt_id,
            agent_id,
        )
    else:
        _LOGGER.warning("Entities not registered yet; skipping pipeline creation")

    # One-shot: a reload must not keep making pipelines.
    options = dict(entry.options)
    options.pop(CONF_CREATE_PIPELINE, None)
    options.pop(CONF_PIPELINE_NAME, None)
    hass.config_entries.async_update_entry(entry, options=options)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _reload_on_change(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
