# K15 Status Lab / Codex Notify

Windows tray helper for **VOROTEX K15 Pro** that maps Codex/ChatGPT lifecycle events to controlled hardware RGB effects.

This directory is a curated downstream mirror. Primary implementation work happens in `KostGame/vorotex-kb-profiles-and-macros2vibecoding/status-lab`.

## The idea

Status Lab separates **identity** from **state**:

- profile chooses the color;
- agent state chooses the effect;
- temporary overlays may change the effect, but not the profile color;
- `NORMAL` means restore the exact hardware baseline captured from the keyboard.

Default profile identity:

- Profile A: `#FF0000` red
- Profile B: `#0000FF` blue

Default semantic states:

- `RUNNING`
- `WAITING`
- `DONE`
- `ERROR`
- `NORMAL` / exact baseline restore

## Why controlled colors only

Physical testing showed that some OEM effect names can produce unexpected multicolor behavior. The normal Status Lab configuration therefore only exposes modes whose palette can be kept controlled:

- Constant
- Flowing Water
- Mono Water
- Single-color breathing
- Off

Cycle breathing, Tetris blocks, Neon and Ambilight may remain documented in the low-level HID research layer, but are deliberately excluded from normal notifier configuration.

## Build

Requirements:

- Windows
- .NET 8 SDK for building from source
- compatible VOROTEX K15 Pro / related hardware for RGB control

Publish a self-contained win-x64 build:

```powershell
dotnet publish src/Vorotex.K15.StatusLab.csproj -c Release -r win-x64
```

The project keeps all publish inputs beside the `.csproj`, including the hook scripts, TOML example and offline configurator.

## Configuration

Start from:

[`status-lab-config.example.toml`](status-lab-config.example.toml)

or open:

[`configurator/index.html`](configurator/index.html)

The configurator is intentionally local/offline. It loads TOML, exposes the safe settings as dropdowns/checks/color controls, validates them and generates a normalized `config.toml`.

Important configuration rules:

1. color belongs to a hardware profile, not to a semantic state;
2. state sections select effect/brightness/speed/duration;
3. RGB notifier is disabled by default until explicitly enabled;
4. malformed user TOML should not be silently overwritten;
5. `NORMAL` restores the exact captured device state.

## Codex integration

The package includes:

- `codex-hook-logger.ps1`
- `install-codex-hooks.ps1`

The reducer uses lifecycle signals such as `UserPromptSubmit`, `PermissionRequest`, `PostToolUse` and `Stop` to derive a small semantic state model. Transport/HID failures are not promoted into semantic `ERROR` states.

## Effect Lab

Effect Lab exists for physical keyboard classification. A test applies one candidate effect using the active profile color for a bounded period and then restores/resumes the previous state.

Use it when validating a new device/effect mapping rather than assuming the OEM effect name describes the physical output accurately.

## Safety / rollback model

Before the first notifier write to a profile, Status Lab captures the exact lighting baseline from the device. All touched profiles are tracked so RGB Off / application exit can restore them best-effort.

The notifier does not intentionally write macros, key mappings, firmware or power settings.

## Mirror provenance

[`provenance.json`](provenance.json) records:

- primary repository;
- source path;
- mirrored ref;
- exact source commit;
- protocol foundation;
- mirror policy.

[`SOURCE.md`](SOURCE.md) explains the development boundary. Do not make an independent Status Lab implementation in this fork and then try to reconcile it manually later.

## License

Status Lab is published under **GPL-3.0-only**. See [`LICENSE.md`](LICENSE.md) and [`NOTICE.md`](NOTICE.md).
