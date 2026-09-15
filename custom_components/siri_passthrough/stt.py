"""A speech-to-text provider that does not transcribe.

Home Assistant hands an STT provider a live ``AsyncIterable[bytes]`` of audio
while the person is still talking -- it is a stream, not a finished recording.
That is the whole trick here: instead of recognising the audio, this provider
pipes those chunks into the bridge's ``/siri/stream`` endpoint as they arrive.
The bridge holds the HomeKit SIRI button down for as long as the request body
keeps coming and releases it when the body ends, so the utterance reaches Siri
live rather than being reconstructed and replayed afterwards.

Nothing is recognised locally, so the "transcript" is a fixed sentinel. See
``conversation.py`` for why that does not produce a "sorry, I didn't understand"
every time.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterable

import aiohttp

from homeassistant.components import stt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BRIDGE_URL,
    CONF_FALLBACK_STT,
    CONF_TARGET,
    DOMAIN,
    SENTINEL_TRANSCRIPT,
)
from .routing import wants_siri

_LOGGER = logging.getLogger(__name__)

# Long enough for any plausible utterance, short enough that a wedged bridge
# does not pin the pipeline open until aiohttp's five-minute default.
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=60)

# Siri's language is whatever the Apple TV is set to; this list only has to
# satisfy the pipeline's own language matching, which happens before any audio
# is sent and never reaches Siri.
_LANGUAGES = [
    "en-US", "en-GB", "en-AU", "en-CA", "en-IE", "en-IN", "en-NZ", "en-ZA",
    "de-DE", "es-ES", "es-MX", "fr-FR", "fr-CA", "it-IT", "ja-JP", "ko-KR",
    "nl-NL", "nb-NO", "pt-BR", "sv-SE", "zh-CN", "zh-TW",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the passthrough STT entity."""
    async_add_entities([SiriPassthroughSTT(hass, entry)])


class SiriPassthroughSTT(stt.SpeechToTextEntity):
    """Streams pipeline audio to Siri instead of recognising it."""

    _attr_has_entity_name = True
    _attr_name = "Siri passthrough"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        data = hass.data[DOMAIN][entry.entry_id]
        self._conf = data
        self._session = async_get_clientsession(hass)
        self._url = str(data[CONF_BRIDGE_URL]).rstrip("/")
        self._target = data.get(CONF_TARGET)
        self._attr_unique_id = f"{entry.entry_id}-stt"

    @property
    def supported_languages(self) -> list[str]:
        return _LANGUAGES

    @property
    def supported_formats(self) -> list[stt.AudioFormats]:
        return [stt.AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        return [stt.AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[stt.AudioChannels]:
        return [stt.AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Send this utterance to Siri, or hand it to a real recogniser."""
        # Taken before a single chunk is read, so the Siri path is unchanged by
        # the existence of routing.
        if not wants_siri(self.hass, self._conf):
            return await self._delegate(metadata, stream)

        return await self._to_siri(stream)

    async def _delegate(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Let another speech-to-text engine have the stream instead."""
        engine_id = self._conf.get(CONF_FALLBACK_STT)
        if not engine_id:
            _LOGGER.warning(
                "Routing says this utterance is not for Siri, but no fallback "
                "speech-to-text engine is configured; discarding it"
            )
            return stt.SpeechResult("", stt.SpeechResultState.ERROR)

        engine = stt.async_get_speech_to_text_entity(self.hass, engine_id)
        if engine is None:
            _LOGGER.error("Fallback speech-to-text engine %s not found", engine_id)
            return stt.SpeechResult("", stt.SpeechResultState.ERROR)

        _LOGGER.debug("Not for Siri; handing the stream to %s", engine_id)
        return await engine.async_process_audio_stream(metadata, stream)

    async def _to_siri(self, stream: AsyncIterable[bytes]) -> stt.SpeechResult:
        """Forward the live audio to Siri and return a sentinel transcript."""
        path = "/siri/stream"
        if self._target is not None:
            path += f"?target={int(self._target)}"

        sent = 0

        async def _body() -> AsyncIterable[bytes]:
            # Counting here rather than pre-reading keeps the stream un-buffered;
            # the point of this integration is that nothing waits for the end of
            # the utterance before Siri hears the start of it.
            nonlocal sent
            async for chunk in stream:
                if chunk:
                    sent += len(chunk)
                    yield chunk

        try:
            async with self._session.post(
                f"{self._url}{path}", data=_body(), timeout=_REQUEST_TIMEOUT
            ) as resp:
                body = await resp.json(content_type=None)
                if resp.status >= 400:
                    _LOGGER.error(
                        "Bridge rejected the utterance (%s): %s", resp.status, body
                    )
                    return stt.SpeechResult("", stt.SpeechResultState.ERROR)
        except asyncio.TimeoutError:
            _LOGGER.error("Timed out streaming to the bridge at %s", self._url)
            return stt.SpeechResult("", stt.SpeechResultState.ERROR)
        except aiohttp.ClientError as err:
            _LOGGER.error("Bridge unreachable at %s: %s", self._url, err)
            return stt.SpeechResult("", stt.SpeechResultState.ERROR)

        if not sent:
            # An empty utterance is not an error worth surfacing -- the button
            # was tapped rather than held -- but Siri got nothing.
            _LOGGER.debug("No audio arrived from the pipeline; nothing sent")

        _LOGGER.debug("Streamed %d bytes to Siri via %s", sent, self._url)
        return stt.SpeechResult(SENTINEL_TRANSCRIPT, stt.SpeechResultState.SUCCESS)
