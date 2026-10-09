# Epic 3 Static-Layer Import Coverage Report — Design

**Date:** 2026-10-09

## Problem

The Epic 3 importer currently emits only the accepted feature count. It silently
skips valid source features that do not intersect the configured Philippines
bounds, so an operator cannot tell from one dry run how many source features were
examined, how many were accepted, or what geographic extent the accepted (unclipped)
geometries cover. This makes source-neutral coverage review harder and weakens the
reproducibility of otherwise auditable local imports.

## Goals

- Report source, accepted, and out-of-bounds feature counts for every dry-run import.
- Report the aggregate bounds of accepted, un-clipped geometries in
  `(west, south, east, north)` order, or `null` when none are accepted.
- Keep the current parser behavior, validation rules, import transaction, and
  protection against empty source replacement.
- Exercise the generic report first with the already permitted, pinned GEM fault
  snapshot; support either existing static-layer kind without PHIVOLCS source use.

## Non-goals

- Fetch or import PHIVOLCS geometry, or imply that its reuse clearance is complete.
- Change the `FaultLine` or `VolcanoZone` schemas, database, API, map, or import
  provenance requirements.
- Clip geometry to project bounds, infer hazard geometry, or claim complete coverage.
- Add a web dashboard, persistent coverage history, source download, or dependency.

## Context And Constraints

- `backend/ingestion/sources/static_layers.py::parse_features` validates GeoJSON
  geometry and provenance, retains intersecting geometries without clipping, and
  currently returns accepted `StaticFeature` rows.
- `scripts/import_fault_lines.py` is source-neutral for the `faults` and
  `volcano_zones` kinds, supports `--dry-run`, and blocks an empty accepted result
  before database replacement.
- `gem_faults.py` and `phivolcs_fault_atlas.py` are thin wrappers over the parser;
  integration tests also call `parse_features` directly. Preserve that function's
  return type and behavior for these consumers.
- The pinned GEM snapshot is documented as CC-BY-SA-4.0. Its source file and local
  import receipt remain ignored under `data/fault_lines/local/`.
- PHIVOLCS fault and volcano-zone vector candidates remain gated on reuse clearance,
  as recorded in `docs/data-sources.md`; this work must not contact those services.
- Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/glossary.md`, and
  `docs/testing-standards.md`. No endpoint or persistence change is in scope.

## Alternatives Considered

1. **Add counts only to the CLI.** Rejected because the CLI cannot accurately
   reconstruct accepted bounds or out-of-bounds counts after the parser filters
   source features.
2. **Change `parse_features` to return a report object.** Rejected because it would
   break existing wrappers and route-level tests that depend on its list return.
3. **Persist coverage reports or render them in a dashboard.** Rejected because
   operators need a pre-import check first; storage and UI add unrelated scope.

## Design

### Architecture and data flow

Add `parse_features_with_report` alongside `parse_features`. The new function
performs the existing single-pass validation and returns both accepted rows and a
`StaticLayerParseReport`. Keep `parse_features` as a compatibility wrapper that
returns only the rows. The CLI calls the reporting function once, logs the report,
and passes the same accepted rows to the existing transactional replacement when
not in dry-run mode. No source file is read twice and no database is needed for a
dry run.

The report counts each input feature once. A feature that passes the existing
geometry checks but does not intersect the configured bounds increments
`excluded_outside_bounds_count`. An intersecting feature that passes the existing
geometry and property checks increments `accepted_feature_count`. Invalid input continues to fail the entire parse before
any import. `accepted_bounds` is the union of accepted geometries' bounds and is
not clipped to the project box. An empty accepted set has `accepted_bounds: null`;
the existing CLI guard still rejects it before replacement.

### Components and interfaces

- Add an immutable `StaticLayerParseReport` dataclass with:
  - `source_feature_count: int`
  - `accepted_feature_count: int`
  - `excluded_outside_bounds_count: int`
  - `accepted_bounds: tuple[float, float, float, float] | None`
- Add `parse_features_with_report(features, *, kind, source, source_url,
  license_name, dataset_version, bbox=(116, 4, 128, 22))`, returning a pair of
  `(list[StaticFeature], StaticLayerParseReport)`.
- Preserve `parse_features(...) -> list[StaticFeature]` as a wrapper over the new
  implementation.
- On successful CLI validation/import, emit structured fields
  `source_feature_count`, `accepted_feature_count`,
  `excluded_outside_bounds_count`, and `accepted_bounds`; retain the existing
  `count` log field as an alias for accepted count for current operator scripts.
- For a zero accepted result, emit the report with a rejected-validation message,
  then exit non-zero with the existing no-features error. Never call
  `replace_layer` for that result.

### Configuration

No new environment variables, command-line arguments, or dependencies. The report
uses the existing `--kind` and parser `bbox` values.

### Error handling

Malformed features, invalid coordinates, duplicate IDs, and unsupported geometry
continue to raise `ValueError` and stop the whole import. The report does not turn
invalid features into skipped features. Filesystem and database errors retain their
existing handling. A zero accepted count remains a hard failure before persistence.

### Data considerations

Bounds are WGS84 decimal degrees ordered west, south, east, north. Because import
retains whole intersecting source geometries, reported bounds may extend beyond
`(116, 4, 128, 22)`. The report describes only this input file and validation run;
it does not establish national hazard completeness, source licensing, or what an
API/client currently displays. The GEM input is used for local verification only.

## Rollout

Implement and test on a dedicated feature branch. First verify the report with
small deterministic fixtures, then run the dry-run against the existing pinned GEM
input if that ignored local file is available. Do not download or substitute a live
source. Update the importer runbook and Epic 3 status only with metrics actually
observed during verification. PHIVOLCS vector work remains a separate, permission-
gated follow-up.

## Files

- `backend/ingestion/sources/static_layers.py` — add the report type and reporting
  parser while preserving `parse_features` compatibility.
- `scripts/import_fault_lines.py` — emit structured coverage metrics and preserve
  the no-empty-import guard.
- `backend/tests/unit/test_static_layers.py` — count, bounds, and zero-accepted
  report cases for line and polygon layers.
- `backend/tests/unit/test_import_fault_lines.py` — CLI report fields and no-write
  behavior for empty accepted results, using local fixtures and a fake session.
- `docs/glossary.md` — define `StaticLayerParseReport` and its coverage limits.
- `docs/runbook.md` — explain the dry-run metrics and un-clipped bounds.
- `docs/project-status.md` — record the source-neutral verification capability
  without changing the partial-coverage status.

## Testing Strategy

- Unit tests pass generators to prove a single-pass source count and assert accepted,
  excluded, and bounds results for both line and polygon fixtures.
- An empty accepted set reports zero and null bounds, then the CLI exits non-zero
  without opening a database session or calling `replace_layer`.
- A successful dry run logs the exact report metrics without database access.
- Existing parser, adapter, integration, and static-layer tests continue to pass.
- Run the backend test suite and `python scripts\\verify_structure.py` if the
  tracked file tree changes; run `git diff --check` before commit.

## Acceptance Criteria

- [ ] Existing `parse_features` callers still receive `list[StaticFeature]`.
- [ ] One reporting parse gives exact source, accepted, excluded, and accepted-bounds
  values for the supplied feature collection.
- [ ] Bounds are un-clipped and ordered `(west, south, east, north)`.
- [ ] Zero accepted features cannot replace an existing source snapshot.
- [ ] The dry-run JSON log exposes all report fields without database access.
- [ ] The pinned GEM dry-run, when the ignored local input exists, reports measured
  values; no PHIVOLCS geometry is fetched or imported.
- [ ] Backend tests and applicable structure/whitespace checks pass.

## Out Of Scope (backlog)

- Persistent, version-to-version coverage history and map visualization.
- Display/API comparison counts beyond the existing import verification procedure.
- Any PHIVOLCS vector import until applicable reuse clearance is documented.
- Volcano-specific data coverage analysis after the fault-first slice is reviewed.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-09-epic3-static-layer-import-coverage-report.md`.
- Terminology: `docs/glossary.md`.
- Existing source and reuse records: `docs/data-sources.md`.
