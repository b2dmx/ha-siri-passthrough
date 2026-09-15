"""Siri Passthrough -- put a Home Assistant voice satellite's microphone
straight onto Siri on an Apple TV.

The usual way to reach Siri from Home Assistant is to transcribe what you said,
then have Home Assistant read the transcript back out loud through TTS. That
works, but it cannot be fast: the utterance has to be *played* to Siri in real
time, on top of speech-to-text and synthesis. Several seconds, every time.

This integration skips all of it. It registers a speech-to-text provider that
does not transcribe anything -- it forwards the pipeline's live audio chunks to
the appletv-siri-voice bridge as they arrive, so Siri hears you while you are
still speaking. The only cost over a real Siri Remote is two LAN hops.

The bridge (https://github.com/marcusadolfsson/appletv-siri-voice) does the hard
part: it pairs as a HomeKit remote and holds the SIRI button down for the life
of the request body.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.STT, Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Siri Passthrough from a config entry."""
    # Options win over the values captured at setup, so routing can be
    # changed later without removing and re-adding the integration.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        **entry.data,
        **{k: v for k, v in entry.options.items() if v not in (None, "")},
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload_on_change))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _reload_on_change(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
