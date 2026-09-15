"""A conversation agent that says nothing.

Every assist pipeline has to have a conversation agent, and by the time the
pipeline reaches that stage the audio has already gone to Siri -- the Apple TV
is answering on the television. If the default agent ran here it would be handed
the sentinel transcript, fail to match it, and announce "sorry, I didn't
understand that" over the top of Siri's reply, every single time.

So this agent accepts anything and responds with silence.
"""

from __future__ import annotations

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the quiet conversation agent."""
    async_add_entities([QuietAgent(entry)])


class QuietAgent(conversation.ConversationEntity):
    """Answers everything with nothing."""

    _attr_has_entity_name = True
    _attr_name = "Siri passthrough (silent)"

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_unique_id = f"{entry.entry_id}-conversation"

    @property
    def supported_languages(self) -> list[str] | str:
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Return an empty response so nothing is spoken or shown."""
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech("")
        return conversation.ConversationResult(
            response=response, conversation_id=user_input.conversation_id
        )
