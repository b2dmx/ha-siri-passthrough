"""Create the assist pipeline during setup, so the user does not have to.

The pipeline has to pair this integration's two entities -- the passthrough
speech-to-text provider and the agent that stays quiet for it. Getting either
wrong produces a confusing failure (no audio reaches Siri, or the satellite
talks over Siri's reply), so it is better made here than described in a README.

The pipeline store is not a public API, so every call is guarded: if it moves,
setup still succeeds and the user builds the pipeline by hand.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _store(hass: HomeAssistant):
    from homeassistant.components.assist_pipeline.pipeline import (
        async_get_pipeline_store,
    )

    return async_get_pipeline_store(hass)


async def async_create(
    hass: HomeAssistant, name: str, stt_entity: str, agent_entity: str
) -> str | None:
    """Create a pipeline wired to our entities. Returns its id, or None."""
    try:
        store = _store(hass)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not reach the pipeline store (%s); skipping", err)
        return None

    if any(p.name == name for p in store.data.values()):
        _LOGGER.debug("A pipeline named %s already exists; leaving it alone", name)
        return None

    # Borrow language and text-to-speech from the preferred pipeline: neither is
    # used on the Siri path, but a pipeline is not valid without them and they
    # should match whatever the user already runs.
    base = None
    try:
        base = store.data.get(store.async_get_preferred_item())
    except Exception:  # noqa: BLE001
        pass

    data = {
        "name": name,
        "language": getattr(base, "language", "en"),
        "conversation_engine": agent_entity,
        "conversation_language": "*",
        "stt_engine": stt_entity,
        "stt_language": getattr(base, "stt_language", None),
        "tts_engine": getattr(base, "tts_engine", None),
        "tts_language": getattr(base, "tts_language", None),
        "tts_voice": getattr(base, "tts_voice", None),
        "wake_word_entity": None,
        "wake_word_id": None,
        "prefer_local_intents": False,
    }

    try:
        created = await store.async_create_item(data)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not create the pipeline (%s); create it by hand", err)
        return None

    _LOGGER.info("Created assist pipeline %r", name)
    return getattr(created, "id", None)
