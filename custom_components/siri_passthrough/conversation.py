"""The conversation stage, which has to serve two masters.

When the utterance went to Siri, the Apple TV is already answering on the
television and the transcript is a sentinel that means nothing. Letting the
default agent see it would produce "sorry, I didn't understand" spoken over
Siri's reply, every single time -- so this answers with silence.

When routing sent the utterance to a real recogniser instead, the transcript is
a genuine sentence that deserves a genuine answer, so it is passed to whichever
agent the user configured.
"""

from __future__ import annotations

import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_FALLBACK_AGENT, DOMAIN, SENTINEL_TRANSCRIPT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the routing conversation agent."""
    async_add_entities([RouterAgent(hass, entry)])


class RouterAgent(conversation.ConversationEntity):
    """Silence for Siri's utterances, a real agent for everything else."""

    _attr_has_entity_name = True
    _attr_name = "Siri passthrough (silent)"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._conf = hass.data[DOMAIN][entry.entry_id]
        self._attr_unique_id = f"{entry.entry_id}-conversation"

    @property
    def supported_languages(self) -> list[str] | str:
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        text = (user_input.text or "").strip()
        agent_id = self._conf.get(CONF_FALLBACK_AGENT)

        if text != SENTINEL_TRANSCRIPT and agent_id:
            # A real sentence, recognised by the fallback engine.
            _LOGGER.debug("Passing %r to %s", text, agent_id)
            return await conversation.async_converse(
                self.hass,
                text=user_input.text,
                conversation_id=user_input.conversation_id,
                context=user_input.context,
                language=user_input.language,
                agent_id=agent_id,
                device_id=getattr(user_input, "device_id", None),
            )

        # Siri has it. Say nothing.
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech("")
        return conversation.ConversationResult(
            response=response, conversation_id=user_input.conversation_id
        )
