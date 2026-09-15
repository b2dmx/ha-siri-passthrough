"""Decide, per utterance, whether this one belongs to Siri.

Deliberately a pure states-machine read: Home Assistant already holds the state
in memory, so this is a dict lookup taken *before* the first audio chunk is
consumed. No network call, no buffering, nothing that could push the Siri path
any slower than it is with no routing at all.

That is the whole reason the decision is made from device state rather than by
trying Assist first and falling back -- a fallback can only decide once the
utterance is over, which means holding the audio, which is the latency this
integration exists to avoid.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import (
    CONF_SIRI_WHEN_ENTITY,
    CONF_SIRI_WHEN_STATES,
    DEFAULT_SIRI_WHEN_STATES,
)


def parse_states(raw: str | list[str] | None) -> list[str]:
    """Accept 'on, playing' or ['on', 'playing']."""
    if raw is None:
        raw = DEFAULT_SIRI_WHEN_STATES
    if isinstance(raw, str):
        raw = raw.split(",")
    return [s.strip().lower() for s in raw if str(s).strip()]


def wants_siri(hass: HomeAssistant, conf: dict) -> bool:
    """True if this utterance should go to Siri rather than to Assist."""
    entity_id = conf.get(CONF_SIRI_WHEN_ENTITY)
    if not entity_id:
        # No condition configured: this pipeline is for Siri, full stop.
        return True

    state = hass.states.get(entity_id)
    if state is None:
        # A condition naming an entity that does not exist should not silently
        # send everything to the television.
        return False

    return state.state.lower() in parse_states(conf.get(CONF_SIRI_WHEN_STATES))
