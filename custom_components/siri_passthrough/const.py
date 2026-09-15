"""Constants for the Siri Passthrough integration."""

DOMAIN = "siri_passthrough"

CONF_BRIDGE_URL = "bridge_url"
CONF_TARGET = "target"

DEFAULT_BRIDGE_URL = "http://homeassistant.local:8477"

# What the appletv-siri-voice bridge and tvOS both expect. Home Assistant's
# assist pipeline carries exactly this, so nothing in the chain resamples --
# which is the entire reason this approach is fast enough to be worth doing.
SAMPLE_RATE = 16000
BYTES_PER_MS = 32

# Returned as the "transcript" so the pipeline has something non-empty to carry
# into the conversation stage. Nothing ever reads it: the audio already went to
# Siri, and the bundled quiet agent answers with silence.
SENTINEL_TRANSCRIPT = "(sent to siri)"
