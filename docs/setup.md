# Setup

Two pieces: the bridge (a Home Assistant add-on) and this integration.

## 1. The bridge

The bridge pairs as a HomeKit remote and is what actually reaches Siri.

**Settings → Add-ons → Add-on Store → ⋮ → Repositories**, and add:

```
https://github.com/marcusadolfsson/appletv-siri-voice
```

Then install **Apple TV Siri Voice Bridge** (1.0.2 or newer) and start it. It
builds from source, so give it a few minutes.

Leave **`expose_control_api` off**. Home Assistant reaches the bridge on
`127.0.0.1` — on Home Assistant OS, Supervised and the usual Docker install,
Core shares the host's loopback with the add-on. Turning it on publishes an
unauthenticated "control the TV and talk to Siri" endpoint to your whole LAN,
and buys you nothing here.

### Pairing

1. Read the setup code from the add-on log
2. iPhone → **Home** app → **+** → **Add Accessory** → **More options…** →
   **Voice Remote** → enter the code
3. When the Home app asks, assign the remote to the Apple TV it should drive

That's it. Nothing to switch on or off: 1.0.2 holds its HomeKit recovery until
something is paired, so it no longer restarts itself mid-pairing.

## 2. This integration

**HACS → ⋮ → Custom repositories**, add:

```
https://github.com/b2dmx/ha-siri-passthrough
```

with category **Integration**. Install it, then restart Home Assistant.

Then **Settings → Devices & Services → Add Integration → Siri Passthrough**.

The bridge URL is filled in for you. Setup tries `http://127.0.0.1:8477`
first, which is where the add-on listens, and falls back to the Supervisor host
and Home Assistant's own hostname in case the bridge runs elsewhere.

## 3. A pipeline

**Settings → Voice assistants → Add assistant**

| Stage | Pick |
|---|---|
| Speech-to-text | Siri passthrough |
| Conversation agent | Siri passthrough (silent) |
| Text-to-speech | anything — it is never used on the Siri path |

Point a satellite at it and hold its mic button.

## Routing (optional)

**Siri Passthrough → Configure**:

| Field | Meaning |
|---|---|
| Send to Siri while this entity is… | the entity to check, e.g. `media_player.apple_tv_4k` |
| …in one of these states | comma separated; the default is `on, idle, playing, paused` — `idle` is the Apple TV awake on its home screen, which is where it usually is when you ask for something |
| Otherwise recognise with | a real speech-to-text engine |
| Otherwise answer with | your normal conversation agent |

Leave the entity blank to send everything to Siri.

## If something is wrong

**Setup says it can't connect.** The add-on isn't running, or it isn't the
one at `127.0.0.1:8477` — if you run the bridge on another machine, enter its
address instead.

**Nothing reaches Siri.** Check the add-on log for a `/siri/stream` request. If
there is none, the pipeline isn't using this speech-to-text provider.

**The satellite talks over Siri's reply.** The pipeline's conversation agent
isn't set to *Siri passthrough (silent)*.

**Siri hears nothing but the request arrives.** The Apple TV is asleep, or the
bridge lost its data stream — the bridge exposes a `recover` action for that.

**Check bridge health** from the Home Assistant host itself (the bridge only
listens on loopback): `curl http://127.0.0.1:8477/state`. A healthy bridge
reports your Apple TV under `targets`, `siriAvailable: true`, and a non-empty
`dataStreams`.
