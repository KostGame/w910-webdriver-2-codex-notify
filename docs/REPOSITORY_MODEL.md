# Repository model

This repository has two independent sources of change and deliberately keeps them separate.

## Roles

### Canonical W910 upstream

`luftaquila/w910-webdriver`

Owns the original browser configurator, protocol documentation, tools and upstream project history.

### Downstream integration fork

`KostGame/w910-webdriver-2-codex-notify`

Preserves the W910 lineage and adds the curated public K15 Status Lab integration.

### Primary Status Lab development

`KostGame/vorotex-kb-profiles-and-macros2vibecoding`

Owns Status Lab implementation work, K15-specific research and the broader VOROTEX profile/macro project.

## Why not develop Status Lab twice?

Two editable copies create drift quickly. The fork therefore treats `extensions/k15-status-lab/` as a **curated mirror**, not a second source of truth.

The mirror records an exact source commit in `provenance.json`.

## Update stream A: W910 upstream

Workflow:

`.github/workflows/sync-upstream-w910.yml`

Conceptual flow:

```text
luftaquila/w910-webdriver:main
        ↓ fetch / verify
sync/upstream-w910
        ↓ review PR
KostGame fork main
```

Rules:

- use a dedicated upstream-sync branch;
- keep upstream changes separate from Status Lab sync commits;
- fail on merge conflicts rather than guessing a resolution;
- review before merging.

## Update stream B: K15 Status Lab

Workflow:

`.github/workflows/sync-k15-status-lab.yml`

Conceptual flow:

```text
VOROTEX source ref / exact SHA
        ↓ curated whitelist
sync/k15-status-lab
        ↓ review PR
KostGame fork main
```

The sync job copies only the explicit Status Lab surface needed by the downstream package:

- application source;
- project file;
- hook helper scripts;
- TOML example;
- offline configurator;
- component license;
- generated source/provenance metadata.

It does not import VOROTEX macro/profile packages, HUD code, research fixtures or unrelated documentation.

## Pinning a source revision

For stable downstream updates, use both:

- `source_ref`
- `expected_source_sha`

The second value makes the job fail closed if a moving branch resolves to a different commit than the reviewed one.

## Fork-specific documentation

README/NOTICE files in this fork are maintained here. Status Lab sync must not regenerate them from the primary repository.

This separation matters because the primary repository explains development, while the fork must explain distribution, upstream lineage and the two-stream maintenance model.

## Commit hygiene

Keep these histories visually distinct:

```text
sync(upstream): ...
sync(k15-status-lab): ...
docs: ...
```

Do not combine canonical upstream changes and Status Lab mirror changes in the same synchronization commit.

## Conflict policy

If upstream W910 changes conflict with downstream integration files:

1. stop the automatic merge;
2. inspect the conflict in a normal PR/branch;
3. preserve upstream behavior unless a downstream modification is intentional and documented;
4. rerun W910 tests and K15 Status Lab CI before merge.

The point is traceability, not clever automation.
