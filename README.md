# Siri Passthrough

Talk to **Siri on your Apple TV** through any Home Assistant voice satellite —
live, while you're still speaking.

Home Assistant can already send Siri a *transcript*: recognise your speech, then
read it back out through text-to-speech. It works, but it can't be quick — the
sentence has to be played to Siri in real time, after recognition and synthesis.

This skips all of that. It registers a speech-to-text provider that doesn't
transcribe. It forwards the pipeline's audio to Siri as the chunks arrive, so
the only delay is two LAN hops.

Works with any satellite Home Assistant supports — an ESPHome voice device, a
remote with a mic button, the companion app.

## Requirements

- The [appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice)
  bridge, paired with your Apple TV
- Home Assistant 2024.6 or newer

## Install

1. HACS → ⋮ → **Custom repositories** → add this repo as an **Integration**
2. Install **Siri Passthrough**, restart Home Assistant
3. **Settings → Devices & Services → Add Integration → Siri Passthrough**
4. Enter the bridge URL (default port `8477`)

> If setup can't connect, the bridge's control API is probably still
> loopback-only. Home Assistant runs in its own container, so it counts as a
> different machine — enable `expose_control_api` on the add-on, or set
> `CTRL_BIND=0.0.0.0` on the container. It has no authentication, so keep it off
> the open internet.

## Use it

Make a pipeline for Siri:

**Settings → Voice assistants → Add assistant**

| Stage | Pick |
|---|---|
| Speech-to-text | **Siri passthrough** |
| Conversation agent | **Siri passthrough (silent)** |
| Text-to-speech | anything (unused) |

Point a satellite at that pipeline and hold its mic button. Siri answers on the
TV, exactly as it would from the Siri Remote.

Keep your normal assistant as a second pipeline and switch between them to
choose who you're talking to — the house, or the television.

## How it works

Home Assistant hands a speech-to-text provider a *live* stream of audio, not a
finished recording. This provider pipes those chunks into the bridge's
`/siri/stream` endpoint, and the bridge holds the HomeKit SIRI button down for
as long as the body keeps coming.

Nothing is recognised, so the transcript is a fixed sentinel string. The bundled
silent conversation agent exists to swallow it — otherwise the default agent
would fail to match it and say "sorry, I didn't understand" over Siri's reply.

Audio is 16 kHz 16-bit mono PCM end to end. Nothing resamples.

## Limitations

- One utterance at a time, across all Apple TVs — a bridge limit
- No transcript comes back; Siri replies on the TV, not in Home Assistant
- The Apple TV has to be awake
- Whatever your satellite does for endpointing still applies

## Credits

The hard part — HomeKit Target Control, pairing, and the data stream that
carries Siri audio — is all
[marcusadolfsson/appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice).
This is a thin adapter onto it.

Built with [Claude Code](https://claude.com/claude-code). Not affiliated with
Apple or Home Assistant.

## License

[MIT](LICENSE)
