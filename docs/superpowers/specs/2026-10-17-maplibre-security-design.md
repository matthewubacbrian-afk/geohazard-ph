# MapLibre dependency security — Design

**Date:** 2026-10-17

## Problem

The web dashboard's `maplibre-gl` 4.x dependency is covered by a critical
attribution cross-site scripting advisory affecting releases through 6.4.0.
`web/src/components/map/MapView.tsx` renders map styles with third-party
attribution, so this production dependency blocks a responsible release.

## Goals

- Lock a MapLibre release newer than 6.4.0 and prove the production dependency
  path is no longer reported by `npm audit --omit=dev`.
- Preserve event selection, basemap switching, and reference overlays in the
  existing map tests and production build.
- Configure the Vite-bundled map worker before map construction.
- Give users an accessible explanation if their device cannot initialize the
  WebGL2 map required by MapLibre v6.
- Record remaining development-tool audit findings separately in `PLAN.md`.

## Non-goals

This slice does not change source-data attribution text, add new map layers,
upgrade Vite/Vitest, or claim physical-browser/device validation.

## Context And Constraints

The map currently uses a default MapLibre import, which v6 removes. The
[upstream migration guide](https://github.com/maplibre/maplibre-gl-js/blob/main/docs/guides/v5-to-v6-migration-guide.md)
requires an explicit worker URL for Vite and WebGL2 for rendering. The
[advisory](https://github.com/advisories/GHSA-jrc7-96c5-q579) lists 6.4.1 as
the first patched release. Existing `MapView` tests mock the rendering library;
web test/build plus CI are needed, and a browser smoke check is desirable.
Follow `CODING_STANDARDS.md`, `docs/testing-standards.md`, and the glossary.

## Alternatives Considered

- Sanitize attribution downstream while retaining v4: difficult to prove every
  style path is covered, and the vulnerable dependency remains installed.
- Disable third-party attribution: removes source credit and still leaves the
  vulnerable library in the bundle.
- Upgrade all web build tooling in the same PR: expands the migration surface and
  obscures a production fix behind unrelated development dependencies.

## Design

Pin `maplibre-gl` at a patched v6 release in `web/package.json` and lockfile.
Use a namespace or named ESM import in `MapView.tsx`; import the worker with
Vite's `?worker&url` suffix and call `setWorkerUrl` once before the first map
constructor. Preserve the current public map API, layers, and controls.

When the constructor throws MapLibre's `GPUInitializationError`, show an
accessible message in the map region explaining that this map needs a browser
with WebGL2 support. Leave the rest of the dashboard usable. Other unexpected
constructor errors remain visible to error reporting rather than being silently
treated as device incompatibility. No configuration or data schema changes.

## Rollout

One isolated web feature branch and PR. Record the priority in `PLAN.md` before
code work. Run tests/build and a production dependency audit locally; merge only
after all repository CI checks pass. Note the WebGL2 browser requirement in
user-facing setup documentation.

## Files

- `PLAN.md`, `docs/project-status.md`: queue and actual delivery state.
- `docs/superpowers/plans/2026-10-17-maplibre-security.md`: execution steps.
- `web/package.json`, `web/package-lock.json`: patched dependency.
- `web/src/components/map/MapView.tsx`, `MapView.module.css`: v6 worker,
  compatibility fallback, styling.
- `web/tests/MapView.test.tsx`: worker configuration and WebGL2 failure coverage.
- `README.md`: browser compatibility note if the existing requirements section
  is the clearest location.

## Testing Strategy

In `web/tests/MapView.test.tsx`, first reproduce missing worker configuration
and the unhandled GPU initialization failure on the old code. Keep all existing
interaction tests green after the migration. Run `npm test`, `npm run build`,
`npm audit --omit=dev`, and repository structure/whitespace checks. Repository
CI provides backend, ML, web, Android/mobile, and iOS simulator checks.

## Acceptance Criteria

- [ ] Locked production MapLibre version is patched and production audit has no
  MapLibre finding.
- [ ] Web tests and production build pass; worker configuration is tested.
- [ ] WebGL2 initialization failure renders an accessible explanation.
- [ ] All five PR CI checks pass before merge; branch/worktree removed afterward.

## Out Of Scope (backlog)

Vite/Vitest audit remediation is the next separate web security slice. Physical
browser/device smoke evidence and deployment verification remain external gates.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-17-maplibre-security.md`.
- Terminology: `docs/glossary.md`.
