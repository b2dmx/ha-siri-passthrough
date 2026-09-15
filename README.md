# Siri Passthrough

Talk to **Siri on your Apple TV** through any Home Assistant voice satellite —
live, while you're still speaking.

Home Assistant can already send Siri a *transcript*: recognise your speech, then
read it back through text-to-speech. It works, but it can't be quick — the
sentence has to be played to Siri in real time, after recognition and synthesis.

This registers a speech-to-text provider that doesn't transcribe. It forwards
the pipeline's audio to Siri as the chunks arrive, so the only delay is two LAN
hops.

## Requirements

- The [appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice)
  bridge, paired with your Apple TV
- Home Assistant 2024.6 or newer

## Install

1. HACS → ⋮ → **Custom repositories** → add this repo as an **Integration**
2. Install, restart Home Assistant
3. **Settings → Devices & Services → Add Integration → Siri Passthrough**

The bridge URL is detected for you. **[Full setup guide →](docs/setup.md)**

## Use it

Build a pipeline under **Settings → Voice assistants**:

| Stage | Pick |
|---|---|
| Speech-to-text | **Siri passthrough** |
| Conversation agent | **Siri passthrough (silent)** |
| Text-to-speech | anything (unused) |

Point a satellite at it and hold the mic. Siri answers on the TV.

## One pipeline for both

Optional. Under **Configure**, set an entity and the states it should be in —
`media_player.apple_tv_4k` being `on`, say. While that holds the mic goes to
Siri; otherwise the same audio becomes an ordinary Assist command.

The check is a state read taken before any audio is consumed, so the Siri path
is exactly as fast with routing on as off.

## Limitations

- One utterance at a time, across all Apple TVs — a bridge limit
- No transcript comes back; Siri replies on the TV, not in Home Assistant
- The Apple TV has to be awake

## Credits

The hard part — HomeKit Target Control, pairing, and the data stream that
carries Siri audio — is
[marcusadolfsson/appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice).
This is a thin adapter onto it.

Built with [Claude Code](https://claude.com/claude-code). Not affiliated with
Apple or Home Assistant.

[MIT](LICENSE) · [Changelog](CHANGELOG.md)
