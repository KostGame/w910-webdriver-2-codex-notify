# K15 Status Lab / Codex Notify

Windows tray helper for VOROTEX K15 Pro that turns Codex lifecycle state into hardware RGB effects.

The core UX model is deliberately simple:

- **profile color identifies the active hardware profile**;
- **lighting effect identifies agent state**;
- Profile A is configured as red and Profile B as blue by default;
- `NORMAL` restores the exact hardware baseline rather than inventing another notification state;
- configuration is human-editable TOML;
- the bundled offline HTML configurator edits the same configuration visually;
- Effect Lab provides bounded physical testing of candidate effects.

This directory is an integration mirror, not the development source of truth. See `SOURCE.md` and `provenance.json`.

## Current maturity

The first mirrored revision may come from the open VOROTEX Status Lab RC while physical Effect Lab acceptance is pending. Check `provenance.json` before treating a mirrored revision as stable.

## Included

- minimal buildable Status Lab application source;
- Codex hook helper/install scripts;
- annotated TOML example;
- offline HTML configurator.

## Intentionally not mirrored

- VOROTEX keyboard profile packages;
- macro libraries;
- HUD sources;
- research fixtures and owner-canary evidence;
- historical JSON configuration;
- unrelated repository documentation.
