# Status Lab release lanes

The downstream fork deliberately keeps accepted builds and prerelease candidates separate.

## Stable lane

Source:

`KostGame/vorotex-kb-profiles-and-macros2vibecoding:main`

Workflow:

`.github/workflows/sync-k15-status-lab.yml`

Flow:

```text
primary main
  -> curated whitelist + drift guard
  -> sync/k15-status-lab
  -> review PR
  -> downstream main
  -> status-lab-latest
```

`status-lab-latest` is the recommended rolling download. A primary prerelease must never replace it merely because a release candidate exists.

## Prerelease lane

Source:

The newest published, non-draft primary prerelease whose tag matches `status-lab-rc*`, or an explicitly selected prerelease tag during manual dispatch.

Workflow:

`.github/workflows/sync-k15-status-lab-prerelease.yml`

Flow:

```text
primary GitHub prerelease
  -> exact release target SHA
  -> public status-lab subtree safety guard
  -> prerelease/k15-status-lab
  -> build four independent Windows applications
  -> downstream prerelease with the same RC tag
```

The prerelease branch is a distribution mirror and is not a merge queue. Publishing a candidate there does not authorize merging the candidate into either primary or downstream `main`.

## RC2 four-application contract

The prerelease lane requires and independently publishes:

- `Vorotex.K15.StatusTray-win-x64.zip`
- `Vorotex.K15.ControlCenter-win-x64.zip`
- `Vorotex.K15.LightingLab-win-x64.zip`
- `Vorotex.K15.HidResearchLab-win-x64.zip`
- `SHA256SUMS.txt`

The source mirror records the exact primary release tag, release URL and source SHA in `extensions/k15-status-lab/provenance.json` on the prerelease branch.

## Safety and drift behavior

Stable and prerelease lanes intentionally use different mirror policies.

The stable lane keeps a strict curated whitelist because it feeds downstream `main`.

The prerelease lane mirrors the exact public `status-lab/` subtree because RC candidates may introduce new application projects and linked source directories before the stable whitelist is updated. Before mirroring, it fails closed if required four-app source files are missing, common secret/database file types are present, or an unexpectedly large file appears in the public subtree.

No prerelease workflow changes `status-lab-latest`. Stable promotion still happens only after the candidate is accepted into primary `main`, reviewed through the stable sync path and merged into downstream `main`.
