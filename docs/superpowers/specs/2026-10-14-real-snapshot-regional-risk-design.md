# Real-Snapshot Regional Risk Integration — Design

**Date:** 2026-10-14

## Problem

The saved PHIVOLCS snapshot has `Date_Time_PH` and `Depth_In_Km` columns that `ml.clean_merge` does not recognize. It therefore rejects all of that source's rows while the USGS file can still train a model. Both snapshots use free-text places as `region_name`, producing thousands of names that do not join the web map's 17 regional boundaries. A stopped trial run exposed this before an export was written.

## Goals

- Accept the observed PHIVOLCS headers without changing its Manila-to-UTC conversion.
- Assign canonical events to the 17 named web-map regions by epicenter coordinates. Include offshore events whose nearest regional boundary is no more than 100 km away; exclude farther events.
- Record the assignment rule, boundary-file digest, and per-source assigned/excluded counts in artifact metadata. Preserve parser accepted/rejected counts separately.
- Fail before writing artifacts when either source has no usable parsed or region-assigned events.
- Train from the two saved source-separated snapshots, then validate a local export against the backend profile schema and web-region names. Keep the raw files and generated bundle out of Git.

## Non-goals

- No claim of a forecast, authoritative hazard assessment, or validated model quality.
- No Kaggle version claim for offline files; their exact bytes remain identified by SHA-256.
- No OCI deployment without a configured host, credentials, DNS, and staging environment.
- No changes to the backend API, web rendering, or clustering algorithm.

## Context And Constraints

The local snapshots contain 142,538 PHIVOLCS rows and 27,671 USGS rows. A one-in-ten sample placed about 32% and 16% inside the 17 boundaries; a 100 km offshore limit would retain about 95% and 81% respectively. These are sample estimates, not final training counts. The checked-in `web/src/data/philippine-regions.json` is a simplified, version-pinned ADM1 asset. `ml/src/ml/regions.py` already sketches coordinate assignment but is unused, assumes an unsuitable working directory, and imports Shapely without declaring it in `ml/pyproject.toml`. Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.

## Alternatives Considered

1. **Boundary-only:** unambiguous but discards most offshore earthquake history.
2. **Bounded nearest region (chosen):** retains nearby offshore records while stating a reproducible distance rule and excluding remote records.
3. **Unbounded nearest region:** retains all records but can attach remote events to an unrelated region.

## Design

### Architecture and data flow

`normalize_csv` maps the observed source headers to canonical fields. `load_and_merge_sources` retains its source-specific timestamp conversion and existing deduplication. `assign_regions` then replaces free-text `region_name` with a name from the pinned boundary asset, using polygon coverage first and nearest coastline/boundary distance for offshore points. `build_region_features` consumes only assigned events, so model outputs join the web asset exactly.

### Components and interfaces

- `ml/src/ml/clean_merge.py`: add `date_time_ph` and `depth_in_km` aliases. Existing fixture headers remain supported.
- `ml/src/ml/regions.py`: resolve the boundary asset from the module location by default; expose `assign_regions(events, regions_path=..., max_offshore_km=100.0) -> RegionAssignment`. Use Shapely's spatial index for candidate polygons and a haversine distance to each candidate's closest boundary point. Return rows plus assigned and excluded counts by source. Invalid coordinates count as excluded. Polygon boundaries count as inside.
- `ml/pyproject.toml`: declare Shapely 2.x as an ML runtime dependency.
- `ml/src/ml/train.py`: reject zero accepted rows for either source, call `assign_regions` after merging, reject zero assigned rows for either source, and save `region_assignment` metadata with `boundary_sha256`, `max_offshore_km`, `assigned_by_source`, and `excluded_by_source`.
- `ml/tests/fixtures` and `ml/tests`: use small representative real-header CSV and synthetic region polygons. Tests remain offline and do not depend on the saved raw snapshots.
- README and data-source/status docs: state the 100 km rule, assignment counts, version limitation, and local export state.

### Configuration

The 100 km limit is a fixed documented training rule in this integration; no new CLI flag or environment variable. A later threshold change should be a reviewed model-version change. Boundary lookup uses the repository asset, independent of the process working directory.

### Error handling

Missing or malformed boundary data and zero-source assignment raise a clear error before `ArtifactBundle.for_version` creates output files. The CLI retains its existing nonzero failure behavior. Invalid source rows are counted by the parser; invalid or remote coordinates are counted by region assignment.

### Data considerations

The boundary asset is simplified, so distances are approximate. The maximum distance is measured from an offshore epicenter to the nearest point on a regional polygon. Assignment is a modeling convention, not a claim that a region owns that earthquake. Metadata identifies the exact boundary bytes and input CSV bytes. Source reports count rows before deduplication; region assignment counts rows after deduplication. The map's existing ARMM name is preserved until its pinned boundary asset is intentionally updated.

## Rollout

Implement the parser regression first, then geographic assignment, then training integration and metadata. Run the ML suite and required repository checks. Train into an ignored, versioned local bundle using the two existing snapshots; inspect source counts, 17 names, metrics, and backend schema parsing before marking the local export ready. Open a PR for source and documentation changes. Do not publish raw inputs or model artifacts.

## Files

- `ml/src/ml/clean_merge.py` — real source header aliases.
- `ml/src/ml/regions.py` — deterministic regional assignment.
- `ml/src/ml/train.py` — assignment gate and metadata.
- `ml/pyproject.toml` — Shapely dependency.
- `ml/tests/fixtures/phivolcs_kaggle_sample.csv` — small observed-header input.
- `ml/tests/test_clean_merge.py`, `ml/tests/test_regions.py`, `ml/tests/test_train.py` — regression coverage.
- `README.md`, `docs/data-sources.md`, `docs/project-status.md`, `docs/glossary.md` — operator guidance and current status.
- `docs/superpowers/plans/2026-10-14-real-snapshot-regional-risk.md` — execution plan.

## Testing Strategy

Watch new parser and assignment tests fail on the old behavior, then pass after each focused change. Exercise inside, nearshore, far, invalid-coordinate, and missing-boundary cases with synthetic polygons. Run an end-to-end fixture training test that asserts region names and metadata counts, plus a zero-source fail-before-write case. Run `pytest -v` from `ml/`, Ruff as the existing non-blocking report, structure verification, and diff checks. The final local export is validated against `RiskProfile` and the 17 boundary names; no network or live staging test is claimed.

## Acceptance Criteria

- [ ] Real PHIVOLCS header fixture parses with accepted rows and correct UTC time.
- [ ] Inside and at-most-100-km offshore events map to one of the pinned region names; farther or invalid events are excluded with counts.
- [ ] Either source contributing zero parsed or assigned rows stops before artifact writes.
- [ ] Metadata records input and boundary hashes, assignment limit, and source counts.
- [ ] A local snapshot run produces a parseable export whose names join the boundary asset.
- [ ] ML tests and repository structure/diff checks pass; Ruff baseline findings are reported accurately.

## Out Of Scope (backlog)

- Kaggle refresh/version retrieval and OCI staging require external credentials and infrastructure.
- Scientific validation of the clustering labels and a geographic exposure model need separate review before any authoritative use.

---

## Spec self-review

- The observed headers, boundary source, 100 km rule, count timing, and validation gates are explicit.
- Each goal has a test or artifact check. No raw or generated data is included in the change.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-real-snapshot-regional-risk.md`.
- Terminology: `docs/glossary.md`.
