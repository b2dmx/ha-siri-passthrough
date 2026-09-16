# Setup

Two pieces: the bridge (a Home Assistant add-on) and this integration.

## 1. The bridge

The bridge pairs as a HomeKit remote and is what actually reaches Siri.

**Settings → Add-ons → Add-on Store → ⋮ → Repositories**, and add:

```
https://github.com/b2dmx/appletv-siri-voice
```

Then install **Apple TV Siri Voice Bridge**. It builds from source, so give it
a few minutes.

> **Why that address and not the original project?** The original add-on cannot
> currently be built by Home Assistant — its Dockerfile refers to files that are
> not in the build folder, so installing it fails immediately. It also cannot be
> paired, because it restarts its own HomeKit accessory partway through pairing.
> Both fixes are offered upstream in
> [PR #2](https://github.com/marcusadolfsson/appletv-siri-voice/pull/2); the
> address above is the same project with those two fixes applied. Once the
> upstream project merges them, use
> `https://github.com/marcusadolfsson/appletv-siri-voice` instead.

### Before you start it

Open the add-on's **Configuration** tab and set **`expose_control_api: true`**. Home Assistant runs in its own container, so
it counts as "a different machine" for that setting, and without it this
integration cannot reach the bridge.

The endpoint has no authentication. Keep it off the open internet.

### Pairing

1. Set **`pairing_mode: true`**, save, restart the add-on
2. Read the setup code from the add-on log
3. iPhone → **Home** app → **+** → **Add Accessory** → **More options…** →
   **Voice Remote** → enter the code
4. Set `pairing_mode` back to **false**, save, restart

Pairing mode matters. The bridge repairs a dead HomeKit data stream by
unpublishing and re-publishing itself, and on a fresh install it always does
that shortly after boot — there cannot be a data stream until an Apple TV is
paired as a target. That re-publish lands in the middle of Home app pairing and
fails it with **OSStatus -6718 (kNotInitializedErr)**. Pairing mode holds the
timers off so you can get through it. Turn it off afterwards; recovery is what
reopens the stream when tvOS drops it in normal use.

## 2. This integration

**HACS → ⋮ → Custom repositories**, add:

```
https://github.com/b2dmx/ha-siri-passthrough
```

with category **Integration**. Install it, then restart Home Assistant.

Then **Settings → Devices & Services → Add Integration → Siri Passthrough**.

The bridge URL is filled in for you: setup probes Home Assistant's own host,
`homeassistant.local`, loopback and the Supervisor host, and keeps the first
that answers. Nothing in the Home Assistant UI exposes this address, because a
host-networked add-on has no address of its own and no port-mapping page — the
control API is on the *host's* interfaces, port `8477`.

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
| …in one of these states | comma separated, e.g. `on, playing, paused` |
| Otherwise recognise with | a real speech-to-text engine |
| Otherwise answer with | your normal conversation agent |

Leave the entity blank to send everything to Siri.

## If something is wrong

**Setup says it can't connect.** `expose_control_api` is off, or the add-on
isn't running.

**Nothing reaches Siri.** Check the add-on log for a `/siri/stream` request. If
there is none, the pipeline isn't using this speech-to-text provider.

**The satellite talks over Siri's reply.** The pipeline's conversation agent
isn't set to *Siri passthrough (silent)*.

**Siri hears nothing but the request arrives.** The Apple TV is asleep, or the
bridge lost its data stream — the bridge exposes a `recover` action for that.

**Check bridge health** at `http://<home-assistant-host>:8477/state`. A healthy
bridge reports your Apple TV under `targets`, `siriAvailable: true`, and a
non-empty `dataStreams`.
