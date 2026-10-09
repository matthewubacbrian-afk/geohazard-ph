# Epic 3 Static-Layer Import Coverage Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make static-layer dry runs report examined, accepted, excluded, and geographic-bounds metrics without changing import semantics.

**Architecture:** Add a detailed parser alongside the existing list-returning parser, then have the importer use the detailed result for its structured log. Keep empty-source protection and transactional persistence unchanged; verify with deterministic fixtures before trying the locally available GEM snapshot.

**Tech Stack:** Python 3.11+, pytest, Shapely, SQLAlchemy logging adapter, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-09-epic3-static-layer-import-coverage-report-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.
- Do not fetch, query, import, or display PHIVOLCS vector geometry. Use deterministic fixtures; use the ignored pinned GEM file only if it already exists locally.
- Preserve `parse_features(...) -> list[StaticFeature]`, the current CRS/geometry checks, API contract, database transaction, and no-empty-replacement guard.
- Report accepted geometry bounds without clipping; order bounds west, south, east, north.
- Keep source inputs and import receipts ignored. Do not add dependencies or migrations.
- Use TDD, Conventional Commits, backend tests, `python scripts\verify_structure.py` for the new tracked test file, and `git diff --check`.

### Task 1: Add a parse report while preserving the existing parser API

**Files:**
- Modify: `backend/ingestion/sources/static_layers.py`
- Test: `backend/tests/unit/test_static_layers.py`

**Interfaces:**
- Add frozen `StaticLayerParseReport` fields: `source_feature_count: int`, `accepted_feature_count: int`, `excluded_outside_bounds_count: int`, and `accepted_bounds: tuple[float, float, float, float] | None`.
- Add `parse_features_with_report(features, *, kind, source, source_url, license_name, dataset_version, bbox=(116, 4, 128, 22)) -> tuple[list[StaticFeature], StaticLayerParseReport]`.
- Keep `parse_features` delegating to the new function and returning only its feature list.

- [ ] **Step 1: Write failing report tests**

Add tests using an iterable of three LineStrings: one wholly inside the box, one crossing its west edge, and one wholly outside. Assert source count `3`, accepted count `2`, excluded count `1`, and un-clipped union bounds `(115, 10, 123, 17)`. Pass a generator to ensure the parser consumes the input once. Add a Polygon fixture case and a valid all-outside case asserting empty rows, excluded count `1`, and null accepted bounds. Assert the compatibility function still returns a list.

- [ ] **Step 2: Run the focused tests and confirm the new behavior fails**

Run from `backend/`:

```powershell
pytest -v tests/unit/test_static_layers.py
```

Expected: existing tests pass; new report tests fail because `StaticLayerParseReport` and `parse_features_with_report` are not implemented.

- [ ] **Step 3: Implement the report in the parser**

Use one parse pass. Count each feature; preserve existing geometry/property validation and identity mapping. Increment the excluded count only after geometry checks when it does not intersect `box(*bbox)`. For accepted rows, accumulate each Shapely geometry's full `.bounds` without clipping. Return null bounds when no feature is accepted. Make `parse_features` return element zero from `parse_features_with_report`.

- [ ] **Step 4: Run the focused parser tests**

Run `pytest -v tests/unit/test_static_layers.py` from `backend/`.

Expected: all parser tests pass, including the new metrics, single-pass generator, Polygon, empty acceptance, and compatibility assertions.

- [ ] **Step 5: Commit the parser and unit tests**

```powershell
git add backend/ingestion/sources/static_layers.py backend/tests/unit/test_static_layers.py
git commit -m "feat: report static layer parse coverage"
```

### Task 2: Emit coverage metrics from the importer

**Files:**
- Modify: `scripts/import_fault_lines.py`
- Create: `backend/tests/unit/test_import_fault_lines.py`

**Interfaces:**
- Successful validation/import log extras include all four report fields plus the existing `count` alias for accepted count, `source`, and `kind`.
- Zero accepted rows log a rejected-validation record with those metrics and exit non-zero before constructing a database session.

- [ ] **Step 1: Write failing CLI tests**

Load `scripts/import_fault_lines.py` using a path derived from the test file, set `sys.argv` to use a temporary GeoJSON FeatureCollection, and run `main()` with `--dry-run`. Assert the `Static layer validated` record contains exact source/accepted/excluded/bounds values, preserves `count`, and never calls `SessionLocal`. For an all-outside FeatureCollection, assert `main()` exits non-zero, logs `Static layer validation rejected` with zero accepted and null bounds, and never constructs a session.

- [ ] **Step 2: Run the new CLI tests and confirm they fail**

Run from `backend/`:

```powershell
pytest -v tests/unit/test_import_fault_lines.py
```

Expected: the tests fail because the CLI does not yet emit parse-report metrics.

- [ ] **Step 3: Integrate the report into the CLI**

Call `parse_features_with_report` once. Log report fields and the compatibility `count` field. If accepted rows are empty, emit the rejected-validation log entry then call the existing `parser.exit(1, ...)`; otherwise preserve the current dry-run and transactional apply behavior.

- [ ] **Step 4: Run parser and CLI tests**

Run from `backend/`:

```powershell
pytest -v tests/unit/test_static_layers.py tests/unit/test_import_fault_lines.py
```

Expected: all focused parser and importer tests pass without a live database or network.

- [ ] **Step 5: Commit the CLI and tests**

```powershell
git add scripts/import_fault_lines.py backend/tests/unit/test_import_fault_lines.py
git commit -m "feat: log static layer import coverage"
```

### Task 3: Document the dry-run metrics and verify the branch

**Files:**
- Modify: `docs/runbook.md`
- Modify: `docs/project-status.md`
- Verify: all changed files

- [ ] **Step 1: Document metric meaning and limits**

Update the Epic 3 import runbook to define source count, accepted count, outside-bounds count, and accepted un-clipped bounds. State that they describe the input and validation run, do not establish national completeness, and do not imply PHIVOLCS permission. Update the Epic 3 status row to mention the new dry-run reporting capability while keeping coverage partial and PHIVOLCS reuse clearance pending.

- [ ] **Step 2: Run focused and package verification**

From `backend/` run:

```powershell
pytest -v tests/unit/test_static_layers.py tests/unit/test_import_fault_lines.py
pytest -v
```

From the repository root run:

```powershell
python scripts\verify_structure.py
git diff --check
```

If the ignored pinned GEM GeoJSON already exists, run the existing importer in `--dry-run` mode with its documented immutable URL, license, and dataset version; report only the metrics it prints. Do not download it to satisfy this optional check.

- [ ] **Step 3: Commit the documentation update and confirm clean state**

```powershell
git add docs/runbook.md docs/project-status.md
git commit -m "docs: explain static layer coverage reports"
git status --short --branch
```

Expected: no uncommitted tracked or untracked files; local source data remains ignored.

## Notes For The Executor

- The fault-first sequence verifies the generic parser with GEM-compatible line fixtures and, only when locally available, the pinned GEM input. Volcano-zone fixtures validate the generic Polygon path; they are synthetic test geometry and not source data.
- Do not update PHIVOLCS metadata, candidate-service counts, or vector-import status as a result of this work.
- This plan does not merge or push the feature branch.
