# K15 Status Lab user guide

K15 Status Lab turns a compatible VOROTEX K15 Pro into a small physical status display for Codex/ChatGPT work.

## Mental model

The notifier separates two signals:

- **color = hardware profile**
- **effect = semantic agent state**

Default profile colors:

| Profile | Default color |
| --- | --- |
| A / TOOLS-AUTH | Red `#FF0000` |
| B / MAIN-VIBECODING | Blue `#0000FF` |

The current schema also supports two palette sources:

- `profile` - use the physically active profile color;
- `profile_pair` - use the canonical A+B pair, currently red then blue.

## Current beta / release-candidate defaults

| Event/state | Current default |
| --- | --- |
| RGB tracking ON | short Flowing Water, red + blue (`profile_pair`) |
| RUNNING | Flowing Water, active profile color |
| WAITING / request | Single-color breathing, speed 7, active profile color |
| STOP signal | short Cycle breathing, red + blue |
| DONE pending attention | Single-color breathing, speed 5, active profile color |
| Physical A/B switch | short Flowing Water in the new profile color |
| NORMAL | restore exact keyboard baseline |
| ERROR | reserved until a high-confidence semantic error source exists |

A HID transport failure, reconnect problem, or unrelated Windows notification must not automatically become semantic `ERROR`.

## Hardware safety model

Status Lab is intentionally lighting-only.

It does not write:

- macros;
- key mappings;
- power settings;
- firmware.

The current implementation also follows an observe-only hardware-profile policy while reacting to physical profile changes. It writes the overlay to the already selected profile instead of programmatically switching A/B slots behind the user's back.

## Baseline restore

Status Lab distinguishes:

1. **Device baseline snapshot**: exact lighting bytes read from the keyboard before notifier writes.
2. **Notifier render policy**: palette + effect used while tracking is active.

`NORMAL`, RGB tracking Off and application exit restore from captured device state rather than synthesizing a guessed normal effect.

Inactive-profile restoration may be deferred until that profile is physically selected, avoiding hidden hardware profile switches.

## Codex session-aware state tracking

The beta baseline tracks Codex state per session rather than using one global bit of state.

Hook metadata such as `sessionId`, `turnId` and `cwd` is preserved. Internal memory/background sessions are kept from stealing semantic foreground focus from the actual task session.

On startup, Status Lab performs a bounded replay of recent hook events so an active Codex session can be rehydrated instead of blindly returning to `NORMAL` after an app restart.

Windows notifications remain supplemental. They are not the primary semantic source.

## Tray UI

The Windows tray exposes:

- RGB tracking On/Off;
- normalized semantic state;
- focused Codex session short ID;
- TOML/configurator entry points;
- bounded RGB test tooling.

The tray icon itself distinguishes tracking Off vs On so you do not need to open the menu to see whether tracking is enabled.

## Configuration

The canonical configuration is commented TOML, currently schema v3.

Use:

`extensions/k15-status-lab/status-lab-config.example.toml`

The configuration controls:

- wire color order;
- profile A/B colors;
- palette source (`profile` / `profile_pair`);
- effect, brightness, speed, direction and duration;
- profile-switch overlay;
- tracking activation signal;
- STOP signal behavior;
- Effect Lab duration.

Legacy schema v2 is accepted/migrated in memory and is not silently rewritten over the user's file.

Malformed TOML is preserved unchanged; safe defaults are used only for the current run.

## Offline HTML configurator

Open:

`extensions/k15-status-lab/configurator/index.html`

It works without a server or network connection. The browser intentionally does not overwrite the live application config automatically. Load a TOML file, edit it visually, then generate/download the validated replacement.

## Production-safe effect set

Physical K15 testing currently supports these notifier-safe modes:

- Constant;
- Flowing Water;
- Mono Water;
- Single-color breathing;
- Cycle breathing with an explicitly controlled one- or two-color palette;
- Off / baseline restore.

Research-only modes include Tetris, Neon, Ambilight and OEM `Horse race` (`0x83`) where physical output is distracting or internally/uncontrollably multicolor.

## Lighting Lab

The downstream package also carries a separate project:

`extensions/k15-status-lab/src/lighting-lab/Vorotex.K15.LightingLab.csproj`

Lighting Lab is for low-level RGB research rather than day-to-day semantic notification. It is useful for:

- testing raw effect modes;
- one- and two-color palette masks;
- brightness/speed/direction experiments;
- exact restore behavior;
- recording owner observations.

Keeping this separate prevents experimental hardware probing from leaking into the normal notifier UI.

## Build

Status Lab:

```powershell
dotnet publish extensions/k15-status-lab/src/Vorotex.K15.StatusLab.csproj -c Release -r win-x64
```

Lighting Lab:

```powershell
dotnet publish extensions/k15-status-lab/src/lighting-lab/Vorotex.K15.LightingLab.csproj -c Release -r win-x64
```

## Source and maturity

Primary development happens in:

`KostGame/vorotex-kb-profiles-and-macros2vibecoding/status-lab`

This fork is a curated integration/distribution mirror. `provenance.json` identifies the exact source commit used for each mirrored revision.
