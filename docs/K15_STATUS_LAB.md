# K15 Status Lab user guide

K15 Status Lab turns a compatible VOROTEX K15 Pro into a small physical status display for Codex/ChatGPT work.

## Mental model

The notifier uses two orthogonal signals:

- **color = hardware profile**
- **effect = semantic agent state**

This keeps profile identity visible even when the state changes.

Default profile colors:

| Profile | Default color |
| --- | --- |
| A | Red `#FF0000` |
| B | Blue `#0000FF` |

Semantic states:

| State | Meaning |
| --- | --- |
| NORMAL | no notifier override; restore the exact keyboard baseline |
| RUNNING | agent is working |
| WAITING | user/permission/input is needed |
| DONE | bounded completion attention state |
| ERROR | reserved for high-confidence semantic/application error |

A HID transport error is not automatically a semantic `ERROR`.

## Start the app

Run the published `Vorotex.K15.StatusLab.exe`. The app lives in the Windows tray.

The tray exposes the RGB canary, TOML/configurator entry points and Effect Lab. Exact labels may evolve while the preview matures.

## Configure it

Two equivalent configuration paths are provided.

### TOML

Use `extensions/k15-status-lab/status-lab-config.example.toml` as the reference.

The configuration owns:

- wire color order;
- profile A/B colors;
- effect, brightness, speed, direction and duration for each semantic state;
- profile-switch overlay behavior;
- optional activation signal;
- Effect Lab duration.

### Offline HTML configurator

Open `extensions/k15-status-lab/configurator/index.html` in a browser.

It works without a server or network connection. The browser security model intentionally means it does not silently overwrite the application's live config. Instead it loads a TOML file and generates/downloads a validated replacement.

## Controlled-palette policy

Normal notifier configuration allows only modes that can be constrained to the active profile color:

- Constant
- Flowing Water
- Mono Water
- Single-color breathing
- Off

Uncontrolled/rainbow-style modes are excluded from the normal configuration UI even if the low-level HID protocol knows their numeric mode IDs.

## Effect Lab

Effect Lab is the hardware truth-check.

Use it to answer questions such as:

- does this mode stay one color on the real keyboard?
- does it leave a stale effect after switching profiles?
- does RGB Off restore both touched profiles?

Each test is bounded and should restore/resume after the configured test duration.

## Baseline restore

Status Lab distinguishes two concepts:

1. **Device baseline snapshot**: exact bytes read from the physical keyboard before notifier writes.
2. **Profile render policy**: color plus state effect used while notifications are active.

`NORMAL`, RGB Off and application exit rely on the captured baseline rather than synthesizing a guessed normal effect.

## Profile switching

A profile-switch notification uses the **new active profile's color**. After the short overlay, the current semantic state resumes in that same profile color.

The project treats physical observations as authoritative because vendor effect names are not guaranteed to match real device behavior.

## Codex hooks

Status Lab includes helper scripts for Codex lifecycle integration. The current semantic model consumes signals around prompt submission, permission requests, tool use and stop/completion.

The notifier is intentionally small and conservative. It should tell you what the agent is doing without becoming a miniature RGB carnival on the desk.
