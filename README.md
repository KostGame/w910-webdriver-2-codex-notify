# W910 WebDriver + K15 Codex Notify

> **KostGame downstream fork of [`luftaquila/w910-webdriver`](https://github.com/luftaquila/w910-webdriver).**
>
> The original browser-based W910 configurator and its history are preserved here. This fork adds a curated **VOROTEX K15 Pro Status Lab** integration that can use keyboard RGB as a compact Codex/ChatGPT activity indicator.

## Download

### Windows x64

**[⬇ Download the latest VOROTEX K15 Status Lab build](https://github.com/KostGame/w910-webdriver-2-codex-notify/releases/download/status-lab-latest/VOROTEX-K15-Status-Lab-latest-win-x64.zip)**

The rolling download is rebuilt automatically from the accepted Status Lab mirror on downstream `main`. The package includes:

- `Vorotex.K15.StatusLab.exe`;
- `Vorotex.K15.LightingLab.exe`;
- TOML configuration example and offline configurator;
- Codex hook helper scripts;
- source provenance and build metadata;
- SHA-256 checksum published beside the ZIP.

When RC1 is first mirrored, an immutable **VOROTEX K15 Status Lab RC1** release is also published under the `status-lab-rc1` tag. The rolling `status-lab-latest` release continues to move forward with later accepted builds.

## What this fork adds

The added component lives under [`extensions/k15-status-lab/`](extensions/k15-status-lab/).

**K15 Status Lab** is a Windows tray application with:

- profile-aware RGB notifications for Codex lifecycle states;
- session-aware foreground-state tracking and bounded restart rehydration;
- human-editable TOML configuration;
- a bundled offline HTML configurator;
- exact keyboard-lighting baseline snapshot/restore;
- Codex hook helpers;
- a separate **Lighting Lab** executable for controlled low-level RGB research;
- revision-level provenance back to the primary VOROTEX repository.

Current RC1 visual defaults use a deliberately small visual language:

| Meaning | RC1 default |
| --- | --- |
| Profile A | red |
| Profile B | blue |
| RGB tracking enabled | short red + blue Cycle breathing |
| RUNNING | Flowing Water in active profile color |
| WAITING / request | Single-color breathing, active profile color |
| STOP signal | short red + blue Cycle breathing |
| DONE pending attention | slower Single-color breathing with a 30-second fallback |
| Profile switch | Status Lab overlay disabled by default; native K15 switch flash remains |
| NORMAL | restore exact keyboard baseline |

Uncontrolled rainbow-style modes remain research-only and are excluded from normal notifier defaults.

## Current maturity

The mirrored Status Lab is on the **release-candidate track**. RC1 in the primary VOROTEX repository adds `PreToolUse` approval recovery, a 30-second DONE fallback, manual attention reset, safer deferred baseline recovery, schema v4 configuration migration, updated lighting defaults, and retained Lighting Lab/configurator tooling.

The downstream mirror remains intentionally conservative: it follows accepted source revisions and does not independently develop another Status Lab implementation.

## Quick start: K15 Status Lab

The mirrored projects are self-contained under:

```text
extensions/k15-status-lab/src/
```

Build/publish Status Lab on Windows with .NET 8:

```powershell
dotnet publish extensions/k15-status-lab/src/Vorotex.K15.StatusLab.csproj -c Release -r win-x64
```

Build/publish Lighting Lab:

```powershell
dotnet publish extensions/k15-status-lab/src/lighting-lab/Vorotex.K15.LightingLab.csproj -c Release -r win-x64
```

Useful files:

- [`extensions/k15-status-lab/README.md`](extensions/k15-status-lab/README.md) - downstream Status Lab usage and architecture
- [`extensions/k15-status-lab/README-RC1.md`](extensions/k15-status-lab/README-RC1.md) - mirrored RC1 notes when available
- [`extensions/k15-status-lab/configurator/index.html`](extensions/k15-status-lab/configurator/index.html) - offline visual TOML configurator
- [`extensions/k15-status-lab/status-lab-config.example.toml`](extensions/k15-status-lab/status-lab-config.example.toml) - annotated current configuration
- [`extensions/k15-status-lab/lighting-lab/README.md`](extensions/k15-status-lab/lighting-lab/README.md) - Lighting Lab notes
- [`extensions/k15-status-lab/provenance.json`](extensions/k15-status-lab/provenance.json) - exact mirrored source revision
- [`docs/REPOSITORY_MODEL.md`](docs/REPOSITORY_MODEL.md) - how upstream and VOROTEX updates stay separate
- [`docs/K15_STATUS_LAB.md`](docs/K15_STATUS_LAB.md) - user-facing Status Lab guide

## Source of truth and automatic sync

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

The Status Lab sync checks the primary repository on a schedule and can also be triggered manually. It copies only an explicit whitelist. A drift guard rejects previously unknown build/runtime source files so a new required file cannot be silently omitted from the mirror.

Two separate review streams keep histories readable:

- W910 upstream updates -> `sync/upstream-w910` -> PR
- Status Lab updates -> `sync/k15-status-lab` -> PR

Neither synchronization path silently overwrites downstream `main`. Once an accepted Status Lab change reaches downstream `main`, the Windows download workflow rebuilds and refreshes the rolling `status-lab-latest` release automatically.

## License and attribution

The original W910 WebDriver is distributed under the repository's GPL-3.0 license and remains attributed to its upstream authors.

The K15 Status Lab component is published under **GPL-3.0-only**. Its component-level licensing and lineage are documented in:

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
