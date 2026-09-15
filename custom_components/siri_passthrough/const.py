"""Constants for the Siri Passthrough integration."""

DOMAIN = "siri_passthrough"

CONF_BRIDGE_URL = "bridge_url"
CONF_TARGET = "target"

# Routing. When SIRI_WHEN_ENTITY is set, an utterance only goes to Siri while
# that entity is in one of SIRI_WHEN_STATES; otherwise the same live stream is
# handed to FALLBACK_STT and answered by FALLBACK_AGENT, so one pipeline serves
# both the television and the house. The check is a states-machine read taken
# before the first audio chunk is consumed, so it costs nothing.
CONF_SIRI_WHEN_ENTITY = "siri_when_entity"
CONF_SIRI_WHEN_STATES = "siri_when_states"
CONF_FALLBACK_STT = "fallback_stt"
CONF_FALLBACK_AGENT = "fallback_agent"

DEFAULT_SIRI_WHEN_STATES = "on, playing, paused"

DEFAULT_PORT = 8477
DEFAULT_BRIDGE_URL = f"http://homeassistant.local:{DEFAULT_PORT}"

# What the appletv-siri-voice bridge and tvOS both expect. Home Assistant's
# assist pipeline carries exactly this, so nothing in the chain resamples --
# which is the entire reason this approach is fast enough to be worth doing.
SAMPLE_RATE = 16000
BYTES_PER_MS = 32

# Returned as the "transcript" so the pipeline has something non-empty to carry
# into the conversation stage, and so a satellite that displays the recognised
# text has something to show. Nothing acts on it: the audio already went to
# Siri, and the bundled agent answers it with silence.
#
# Kept human-readable rather than a marker string for exactly that reason -- on
# a screen it reads as a status line instead of debug output.
SENTINEL_TRANSCRIPT = "Asked Siri"
