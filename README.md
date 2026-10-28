<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/siri_passthrough/brand/dark_icon@2x.png">
    <img src="custom_components/siri_passthrough/brand/icon@2x.png" width="140" alt="Siri Passthrough logo">
  </picture>
</p>

<h1 align="center">Siri Passthrough</h1>

<p align="center"><b>Talk to Siri on your Apple TV through any Home Assistant voice satellite, live.</b></p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistantcommunitystore&logoColor=white" alt="HACS Custom"></a>
  <a href="https://ko-fi.com/goobis2dmx"><img src="https://img.shields.io/badge/Ko--fi-Support-FF5E5B?logo=kofi&logoColor=white" alt="Support on Ko-fi"></a>
</p>

A Home Assistant integration. Your voice goes straight to Siri while you're still talking, with no transcribe-then-speak delay.

> Also built into [appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice) (*Option 3*). Use this standalone version if you only want the passthrough.

## What it does

- **Streams your voice to Siri** as you speak. Siri answers on the TV.
- **One pipeline for both:** Siri while the Apple TV is on, normal Assist otherwise.
- **Tells you what broke** in **Repairs**, instead of silently doing nothing.

## Installation

You need an Apple TV (tvOS 12+), Home Assistant 2024.6+, the [appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice) bridge add-on (1.0.2+), and an iPhone or iPad to pair it.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=b2dmx&repository=ha-siri-passthrough&category=integration)

1. Open in HACS (button above), download **Siri Passthrough**, restart.
2. **Settings → Devices & services → Add integration → Siri Passthrough**. The bridge address fills in for you.

## Onboarding

1. **Bridge:** install the add-on, then pair it in the iPhone **Home** app as a **Voice Remote** using the code from the add-on log.
2. **Integration:** add it (above).
3. **Pipeline:** **Settings → Voice assistants → Add assistant**. Speech-to-text: *Siri passthrough*. Conversation agent: *Siri passthrough (silent)*.
4. Point a satellite at the pipeline and hold its mic button.

## Tips

- Route by state under **Configure**, e.g. `media_player.apple_tv` is `on, idle, playing, paused`. Routing adds no delay.
- Leave the add-on's `expose_control_api` **off**. It isn't needed and exposes the TV to your LAN.
- The Apple TV must be awake. One activation at a time, and no transcript comes back.
- Satellite talking over Siri? The conversation agent isn't set to *Siri passthrough (silent)*.

## More

[Full setup guide →](docs/setup.md) · [Changelog →](CHANGELOG.md)

Credit to [marcusadolfsson/appletv-siri-voice](https://github.com/marcusadolfsson/appletv-siri-voice) for the HomeKit bridge.

---

<p align="center">
  <a href="LICENSE">MIT</a> · <a href="https://ko-fi.com/goobis2dmx">Support on Ko-fi</a> · Not affiliated with Apple or Home Assistant<br><br>
  Siri Passthrough v0.4.2 by Goobis<br>
  AI was used to help develop this application
</p>
