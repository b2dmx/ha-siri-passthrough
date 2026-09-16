"""Create the assist pipeline during setup, so the user does not have to.

The pipeline has to pair this integration's two entities -- the passthrough
speech-to-text provider and the agent that stays quiet for it. Getting either
wrong produces a confusing failure (no audio reaches Siri, or the satellite
talks over Siri's reply), so it is better made here than described in a README.

The pipeline store is not a public API. Every call is therefore guarded, but
narrowly: a missing store is reported, not swallowed, because silently doing
nothing is exactly how this feature would appear to work while not working.
"""

from __future__ import annotations

import logging

from homeassistant.components.assist_pipeline.pipeline import (
    KEY_ASSIST_PIPELINE,
    async_get_pipelines,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _store(hass: HomeAssistant):
    """The pipeline storage collection, or None if it is not there."""
    data = hass.data.get(KEY_ASSIST_PIPELINE)
    return getattr(data, "pipeline_store", None) if data else None


async def async_create(
    hass: HomeAssistant, name: str, stt_entity: str, agent_entity: str
) -> str | None:
    """Create a pipeline wired to our entities. Returns its id, or None."""
    store = _store(hass)
    if store is None:
        _LOGGER.warning(
            "The assist pipeline store is not available; create the pipeline by "
            "hand (speech-to-text %s, conversation agent %s)", stt_entity, agent_entity
        )
        return None

    if any(p.name == name for p in async_get_pipelines(hass)):
        _LOGGER.debug("A pipeline named %s already exists; leaving it alone", name)
        return None

    # Borrow language and text-to-speech from the preferred pipeline: neither is
    # used on the Siri path, but a pipeline is not valid without them and they
    # should match whatever the user already runs.
    base = None
    try:
        base = store.data.get(store.async_get_preferred_item())
    except Exception as err:  # noqa: BLE001 -- non-public; a default is fine
        _LOGGER.debug("No preferred pipeline to copy from (%s)", err)

    # These keys are the Pipeline dataclass's fields exactly: the store builds
    # Pipeline(id=..., **data), so an extra or missing key raises.
    data = {
        "name": name,
        "language": getattr(base, "language", None) or "en",
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
