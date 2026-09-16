# Siri Passthrough

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/goobis2dmx)

Talk to **Siri on your Apple TV** through any Home Assistant voice satellite —
live, while you're still speaking.

Home Assistant can already send Siri a *transcript*: recognize your speech, then
read it back through text-to-speech. It works, but it isn't quick.

This adds a speech-to-text option that never transcribes anything. It passes
your voice straight through to Siri while you are still talking.

## Requirements

- The [appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice)
  bridge, paired with your Apple TV
- Home Assistant 2024.6 or newer

## Install

1. HACS → ⋮ → **Custom repositories** → add this repo as an **Integration**
2. Install, restart Home Assistant
3. **Settings → Devices & Services → Add Integration → Siri Passthrough**

**[Full setup guide →](docs/setup.md)**

## Use it

Point a satellite at the pipeline and hold its dedicated mic button. Siri answers on the
TV.

If anything in the chain breaks later — it shows up in **Repairs** saying why,
rather than silently doing nothing.

## One pipeline for both

Optional. Under **Configure**, set an entity and the states it should be in —
`media_player.apple_tv` being `on`. While conditions pass, the mic goes to
Siri; otherwise the same audio becomes an ordinary Assist command.

A state read taken before any audio is consumed, so the Siri path
is exactly as fast with routing on as off.

## Limitations

- One activation at a time, across all Apple TVs if multiple paired.
- No transcript comes back; Siri replies on the TV, not in Home Assistant
- The Apple TV has to be awake

## Credits

The hard part — HomeKit Target Control, pairing, and the data stream that
carries Siri audio — is
[marcusadolfsson/appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice).

Built with [Claude Code](https://claude.com/claude-code). Not affiliated with
Apple or Home Assistant.

[MIT](LICENSE) · [Changelog](CHANGELOG.md)
