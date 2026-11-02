# Ambilight TV + Hue Sync

Home Assistant integration that streams the colours of a **Philips Ambilight TV** to the lights of a
**Philips Hue Entertainment area**, with low latency (50 Hz) and a sidebar panel with presets.

It reads the TV's own Ambilight measurement (the colours Ambilight sees at the screen edge) and drives the
Hue lights through the Hue **Entertainment API** (DTLS streaming), instead of sending one REST command per light.
That removes the ~1 s lag of REST-based setups, which are limited by the bridge to roughly 10 commands per second.

> Not affiliated with Philips, TP Vision, Signify or Home Assistant. Philips, Ambilight and Hue are trademarks of their owners.

## Features

- Streams to a Hue Entertainment area at 50 Hz over DTLS (own pure-Python DTLS 1.2 PSK client, no extra libraries).
- Sidebar panel with **presets** (Movie, Movie Intensive, Game, Game Intensive, Relax, Native, TV Ambilight Style) and a live editor.
- **Lights follow** (per preset): smooth blend around the light, nearest edge zone on its side, average of several zones on its side, average of the whole side, or the TV's own 10 Ambilight zones.
- Tone controls: gain, curve, min/max brightness, saturation, "Ambilight on dark content" (Off / Low / Medium / High).
- **Smoothing** with separate time constants for colour and brightness, or an experimental filter that mimics the TV's own.
- **Native preset**: reproduces the look of the TV's built-in Ambilight+Hue, including an adjustable "native delay" that emulates its slower, REST-like behaviour.
- **TV Ambilight Style** preset: follows the style selected on the TV (Standard, Cinema, Sports, Game), its Ambilight brightness and saturation.
- Optional **non-Hue lights** per preset (any `light.*` entity), driven with a rate-limited `light.turn_on` and restored to their previous state when the stream stops.
- Entities: a `switch` to start/stop the stream, a `select` for the active preset, sensors for the average screen colour and the active TV input, a button to refresh the light positions.
- Service `ambilight_hue_stream.activate_preset` for automations.

## Requirements

- A **Philips Android / Google TV with Ambilight** that exposes the JointSpace API on port 1926 (`/6/ambilight/measured`).
  Developed and tested on a 2024 Philips Google TV (TA5 platform); other models may work but are untested.
  TVs without Ambilight are **not supported** (they have no Ambilight measurement to read).
- A **Hue Bridge (v2)** with an **Entertainment area** that contains the lights you want to stream to.
- Home Assistant **2025.1** or newer (developed and tested on 2026.10; older versions are untested).
- Optional: ADB over network enabled on the TV, only used for the "TV source" sensor (HDMI input vs. apps).

## Installation

### Home Assistant Marketplace / HACS

1. Open the **Marketplace** (HACS on older Home Assistant versions), add a **custom repository**:
   `https://github.com/MadDinu93/ambilight-tv-hue-sync` (type *Integration*).
2. Install **Ambilight TV + Hue Sync** and restart Home Assistant.

### Manual

Copy `custom_components/ambilight_hue_stream` into your Home Assistant `config/custom_components` folder and restart.

## Setup

1. **Settings → Devices & services → Add integration → Ambilight TV + Hue Sync**.
2. Enter the TV and Hue bridge IP addresses. A **PIN** appears on the TV; enter it to pair.
3. Press the **link button** on the Hue bridge and submit within 30 seconds.
4. Pick the **Entertainment area** to stream to. Position the lights in that area with the Hue app
   (the panel shows their positions and uses them to decide what each light follows).
5. Open **Ambilight TV + Hue Sync** in the sidebar, choose a preset and press **Start**.

## Presets and settings

| Setting | What it does |
|---|---|
| Lights follow | Which screen-edge pixels each light follows (see below). |
| Smoothing | Standard (two sliders) or the experimental TV filter. |
| Native delay | 0 % = as fast as possible, 100 % = like the TV's own Ambilight+Hue (slow Hue transitions, one light updated at a time). |
| Gain / Curve | How strongly the TV's (low) measured values are boosted, and the brightness response. |
| Min / Max brightness | The range the lights use on lit scenes. |
| Saturation | Above 1 = more vivid, below 1 = more pastel. |
| Ambilight on dark content | Glow kept on near-black scenes (Off / Low / Medium / High). |
| Non-Hue lights | Extra `light.*` entities with their own position on the screen. |

### Lights follow

- **Smooth (around the light):** each light blends the whole screen edge, weighted by distance (the *Spread* slider sets how wide).
- **Nearest zone on its side:** only the single edge zone closest to the light.
- **Average of several zones on its side:** the *N* zones nearest to the light along its side.
- **Average of the whole side:** the whole left, right, top or bottom edge.
- **TV zones:** the TV's own 10 Ambilight zones. By default each light uses the zone closest to its position; you can pick a zone per light in the panel.

### Automations

```yaml
action: ambilight_hue_stream.activate_preset
data:
  preset: Game
```

Switch the preset by name or id, then turn `switch.ambilight_tv_hue_sync_stream` on or off
(the exact entity id depends on the name Home Assistant registered).

## How it works

- The TV's JointSpace endpoint `/6/ambilight/measured` returns the colours at the screen edge (a ring of 21 pixels on the tested TV).
  It is polled at about 25 Hz; the raw values are low (often 10–25 % of full scale), hence the gain.
- Each light's colour is computed from that ring, smoothed, tone-mapped and sent as an Entertainment frame (50 Hz) to the bridge.
- The Native preset and the TV filter come from analysing the behaviour of one TV firmware (its zones, gain and temporal filter),
  validated against recordings of that TV. They reproduce measured behaviour; no Philips code or binaries are included.

## Known limitations

- Philips Ambilight TVs only, and only one model/firmware has been tested.
- The *TV Ambilight Style* preset reads the TV's settings menu by node id, which can differ between firmware versions; if it cannot be read the integration falls back to *Standard*.
- The *TV zones* layout assumes the 3 / 7 / 3 / 8 pixel ring of the tested TV; on a differently sized ring it falls back to the nearest zone on the light's side.
- On this firmware the TV's own Ambilight output is not exposed, so the style presets emulate it instead of copying it.
- A TV that is short on memory can answer slowly; the stream stops if the TV does not answer for 15 seconds.

## License

GNU General Public License v3.0, see [LICENSE](LICENSE).

Copyright (C) 2026 MadDinu93. This program is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, version 3. It is distributed in the hope that
it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.
