# Roadmap

This fork is intentionally narrow. It is not meant to absorb the entire VOROTEX project.

## Current baseline

The first downstream Status Lab integration provides:

- Windows tray application;
- profile-color / state-effect renderer;
- exact baseline restore model;
- controlled-color Effect Lab;
- TOML configuration;
- offline HTML configurator;
- Codex lifecycle hook helpers;
- curated mirror provenance;
- Windows build/publish CI;
- independent upstream-W910 and Status-Lab sync workflows.

## Near term

### Stabilize physical effect defaults

Continue classifying real K15 behavior and keep only calm, predictable effects in defaults.

### Better install/update experience

Potential improvements:

- packaged release ZIP from the downstream fork;
- version display in the tray app;
- simple install/update helper that preserves user config;
- explicit migration notes when the TOML schema changes.

### Configurator quality

Potential improvements:

- clearer effect descriptions based on physical observation rather than vendor naming;
- config diff preview;
- import/export presets;
- validation explanations close to each field;
- device/profile discovery where browser/runtime constraints allow it safely.

## Later

### Broader device compatibility

The W910/K15 family appears to share useful protocol concepts, but compatibility must be proven device by device. Do not label a device supported solely because a packet layout looks similar.

### More notification sources

Codex/ChatGPT is the initial target. Other local agent/dev-tool integrations are possible if they can feed the same small semantic state model without coupling the lighting layer to one application.

### Release discipline

A future stable release process should attach:

- exact VOROTEX source SHA;
- downstream fork SHA;
- artifact digest;
- supported/tested hardware list;
- config schema version;
- concise physical-test notes.

## Explicit non-goals

Unless the scope changes deliberately, this fork should not become:

- a mirror of all VOROTEX profiles and macros;
- a generic RGB animation collection;
- a second independent Status Lab development tree;
- a storage area for vendor binaries or private packet captures;
- a place for unbounded rainbow/multicolor notifier effects.

The useful shape is small: original W910 lineage plus a clean, traceable K15/Codex integration.
