# W910 WebDriver + K15 Codex Notify

> **KostGame downstream fork of [`luftaquila/w910-webdriver`](https://github.com/luftaquila/w910-webdriver).**
>
> The original browser-based W910 configurator and its history are preserved here. This fork adds a curated **VOROTEX K15 Pro Status Lab** integration that can use the keyboard RGB as a compact Codex/ChatGPT activity indicator.

## What this fork adds

The added component lives under [`extensions/k15-status-lab/`](extensions/k15-status-lab/).

**K15 Status Lab** is a Windows tray application with:

- profile-aware RGB notifications for agent lifecycle states;
- human-editable TOML configuration;
- a bundled offline HTML configurator;
- an RGB Effect Lab for controlled hardware testing;
- exact baseline snapshot/restore instead of permanently replacing the user's normal lighting;
- Codex hook helpers;
- revision-level provenance back to the primary VOROTEX repository.

The default model is intentionally simple:

| Meaning | Default |
| --- | --- |
| Profile A | red |
| Profile B | blue |
| Profile identity | color |
| Agent state | lighting effect |
| Normal state | restore exact keyboard baseline |

Notifier modes are limited to controlled one-color/two-color-safe effects. Rainbow-style and uncontrolled multicolor modes are intentionally excluded from the normal configuration surface.

## Quick start: K15 Status Lab

The mirrored project is self-contained under:

```text
extensions/k15-status-lab/src/
```

Build/publish on Windows with .NET 8:

```powershell
dotnet publish extensions/k15-status-lab/src/Vorotex.K15.StatusLab.csproj -c Release -r win-x64
```

Useful files:

- [`extensions/k15-status-lab/README.md`](extensions/k15-status-lab/README.md) - Status Lab usage and architecture
- [`extensions/k15-status-lab/configurator/index.html`](extensions/k15-status-lab/configurator/index.html) - offline visual TOML configurator
- [`extensions/k15-status-lab/status-lab-config.example.toml`](extensions/k15-status-lab/status-lab-config.example.toml) - annotated configuration
- [`extensions/k15-status-lab/provenance.json`](extensions/k15-status-lab/provenance.json) - exact mirrored source revision
- [`docs/REPOSITORY_MODEL.md`](docs/REPOSITORY_MODEL.md) - how upstream and VOROTEX updates stay separate
- [`docs/K15_STATUS_LAB.md`](docs/K15_STATUS_LAB.md) - user-facing Status Lab guide

> **Current maturity:** the first published integration is a working research/preview build. Core Effect Lab behavior is usable, while hardware-specific defaults can still evolve as physical K15 testing continues.

## Source of truth and lineage

There are three deliberately distinct roles:

```text
luftaquila/w910-webdriver
        │ canonical W910 upstream
        ▼
KostGame/w910-webdriver-2-codex-notify
        ▲
        │ curated Status Lab mirror
        │
KostGame/vorotex-kb-profiles-and-macros2vibecoding
```

- **Canonical W910 upstream:** `luftaquila/w910-webdriver`
- **This integration/distribution fork:** `KostGame/w910-webdriver-2-codex-notify`
- **Primary Status Lab development:** `KostGame/vorotex-kb-profiles-and-macros2vibecoding`

Status Lab is not independently developed in this fork. Its mirror records the exact source commit in `provenance.json`.

Two separate review workflows keep histories readable:

- W910 upstream updates -> `sync/upstream-w910` -> PR
- Status Lab updates -> `sync/k15-status-lab` -> PR

Neither synchronization path is intended to silently overwrite downstream `main`.

## License and attribution

The original W910 WebDriver is distributed under the repository's GPL-3.0 license and remains attributed to its upstream authors.

The K15 Status Lab component is also published under **GPL-3.0-only**. Its component-level licensing and lineage are documented in:

- [`extensions/k15-status-lab/LICENSE.md`](extensions/k15-status-lab/LICENSE.md)
- [`extensions/k15-status-lab/NOTICE.md`](extensions/k15-status-lab/NOTICE.md)
- [`extensions/k15-status-lab/SOURCE.md`](extensions/k15-status-lab/SOURCE.md)

---

# Original W910 WebDriver

Open-source browser configurator for the SXS/YXT W910 macro keyboard. It communicates directly with the device through WebHID or Web Bluetooth, without the vendor driver or application.

**[Open the original W910 WebDriver deployment](https://luftaquila.github.io/w910-webdriver/)**

W910 WebDriver provides control of onboard profiles, Normal/Fn key mappings, macros, lighting, and power settings.

## Compatibility

- Desktop Chrome or Edge.
- USB, 2.4 GHz receiver, and Bluetooth configuration supported.
- Bluetooth: switch to `BT`, then hold the bottom RGB light switch for three seconds before connecting.

The browser may identify the keyboard as `YXT K100 Keyboard`.

## Known limits

- Bluetooth reconnection after a page reload requires pairing mode in default Chrome.

## W910 usage

1. Connect the W910 over USB, its 2.4 GHz receiver, or Bluetooth.
2. Open W910 WebDriver and select the matching connection button.
3. Choose the keyboard in the browser permission dialog.

Export a backup before making large changes. Do not run the vendor configurator at the same time.

## Original web configurator development

```sh
npm run serve
```

Open <http://localhost:8000/>.

```sh
npm test
npm run test:python
```

## Reverse engineering references

The upstream project documents its vendor software extraction, protocol reconstruction, HID validation, WebHID implementation and tooling.

Technical references retained from upstream:

- [Protocol reference](PROTOCOL.md)
- [Firmware extraction status](FIRMWARE.md)
- [Protocol tools](tools/README.md)

Vendor binaries, extracted resources, and packet captures are not included.
