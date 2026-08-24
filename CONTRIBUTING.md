# Contributing

This fork has a deliberately split maintenance model. Before opening a change, first decide **which project owns it**.

## Changes to the original W910 WebDriver

If the change belongs to the original browser configurator, protocol tools or upstream documentation, prefer contributing it to:

`luftaquila/w910-webdriver`

This fork should normally receive those changes later through the dedicated upstream-sync path.

## Changes to K15 Status Lab

Implementation changes to K15 Status Lab belong in:

`KostGame/vorotex-kb-profiles-and-macros2vibecoding`

The accepted Status Lab source is then mirrored here through `.github/workflows/sync-k15-status-lab.yml`.

Do not maintain a divergent second implementation directly under `extensions/k15-status-lab/src/`.

## Fork-specific changes

Changes that are specific to this downstream integration are welcome here, for example:

- fork README and user documentation;
- provenance/attribution presentation;
- sync workflows;
- downstream build/release packaging;
- integration CI.

## Hardware claims

Treat physical-device observations as evidence. Do not claim a W910/K15-family device or effect is supported solely because its packet layout looks similar.

For RGB behavior, prefer reproducible observations such as:

- device/profile tested;
- effect mode;
- configured color(s);
- actual physical output;
- restore behavior after the test.

## Safety boundaries

Status Lab is intended to touch notifier lighting only. Changes that start writing macros, key mappings, power settings or firmware need explicit review and should not be smuggled into an RGB/notifier PR.

## Pull requests

Keep PRs single-purpose where practical:

- upstream W910 sync;
- Status Lab mirror sync;
- downstream docs/CI/release infrastructure.

Mixing these makes lineage much harder to audit later.
