# Portable verification baseline - Implementation Plan

> **For agentic workers:** Use the executing-plans skill to implement this bounded plan task by task.

**Goal:** Remove the existing backend and ML Ruff findings and enforce portable lint and mobile TypeScript checks in CI.

**Architecture:** Establish explicit package lint rules, preserve runtime behavior while fixing findings, strengthen failure-path tests, then enable blocking CI and document evidence.

**Tech Stack:** Python 3.11+, Ruff, pytest, TypeScript, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, backend, testing, error-handling, and git contracts.
- Preserve PHIVOLCS UTC+8 parsing and training CLI stderr/nonzero failure behavior.
- Never edit applied migrations. Limit legacy exceptions to the two existing migration files and their current modernization/import findings.
- No endpoint, model artifact, data-quality hold, or deployment behavior changes.
- Use Conventional Commits; do not commit implementation until all package checks and independent review pass.
- Backend integration tests use dedicated PostGIS and Redis test services, never application data.

### Task 1: Reproduce and make lint configuration portable

**Files:**
- Modify: `backend/pyproject.toml`, `ml/pyproject.toml`
- Modify: Python files identified by the reproduced Ruff findings

**Interfaces:**
- Consumes: current Ruff findings and effective settings.
- Produces: explicit package-local lint configuration, clean `ruff check --config pyproject.toml .` in both packages.

- [x] Reproduce 18 backend and 11 ML findings before source edits.
- [x] Inspect effective rule selection and make the intended rule set explicit.
- [x] Fix unused imports/locals, import ordering, redundant conversions, and UTC usage without unrelated changes.
- [x] Preserve immutable migrations through exact-file, exact-rule legacy exceptions.
- [x] Verify both package lint commands pass.

### Task 2: Preserve and strengthen failure-path behavior

**Files:**
- Modify: `backend/tests/unit/test_usgs_fetch.py`
- Modify: `backend/ingestion/sources/phivolcs_earthquake.py`
- Modify: `ml/src/ml/train.py`, `ml/tests/test_train.py`

**Interfaces:**
- Consumes: HTTP failure fake, existing PHIVOLCS fixtures, `ml.train.main(argv)`.
- Produces: HTTP failure assertion requiring `USGSFetchError`; unchanged timezone conversion; CLI failures returning 1 with a short stderr reason.

- [x] Strengthen HTTP-error regression to require the typed error and realistic HTTP failure.
- [x] Add expected/unexpected CLI failure characterization before editing the command boundary.
- [x] Use existing fixture tests for timezone semantics; do not add redundant import-only tests.
- [x] Document the single CLI boundary BLE001 exception instead of changing failure behavior.
- [x] Run targeted tests and full backend/ML suites.

### Task 3: Enforce checks and record delivery

**Files:**
- Modify: `.github/workflows/backend-ci.yml`, `.github/workflows/ml-ci.yml`, `.github/workflows/mobile-ci.yml`
- Create: `mobile/tsconfig.json` (strict `App.tsx` and `src` checking; ES2020, ESNext, Bundler, react-native JSX, noEmit)
- Modify: `CODING_STANDARDS.md`, `docs/testing-standards.md`, `PLAN.md`, `docs/project-status.md`

**Interfaces:**
- Consumes: clean lint baseline and existing CI package installation.
- Produces: blocking backend/ML Ruff commands with explicit config and mobile `npx tsc --noEmit`.

- [x] Enable lint and TypeScript jobs without continue-on-error.
- [x] Document exact local and CI checks and narrow legacy exceptions.
- [x] Run backend/ML full pytest and Ruff; parent verifies source-identical web/mobile CI and the new local TypeScript check.
- [x] Run structure verification and `git diff --check`, inspect final diff, and request independent review.
- [x] Update delivery records with actual evidence and remaining gates.
- [ ] After parent approval, commit implementation with a Conventional Commit; parent owns push/PR/merge.

## Notes for the executor

Baseline branch includes project-plan commit `d4d9301e`. Parent owns frontend checks and integration. This slice establishes verification gates, not overall project completion. Training CLI characterization tests assert preserved behavior and may pass before cleanup; the initial failing Ruff commands are the regression for this lint-only slice.

## Verification evidence

- Backend `pytest -v`: 148 passed, one upstream Starlette/httpx deprecation warning, 103.52 seconds; dedicated PostGIS on 55432 and Redis on 56379.
- ML `pytest -v`: 65 passed, 144.99 seconds, with `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`.
- Backend and ML `ruff check --config pyproject.toml .` from each package: passed, Ruff 0.16.10.
- Mobile `npx tsc --noEmit`: passed (parent verification using the new config).
- Parent verified source-identical web tests/build and mobile Jest/Android CI on PR #39 at `d4d9301e`; redundant local frontend runs stopped during memory pressure. Fresh feature-PR CI remains required.
- `python scripts/verify_structure.py`: all 140 expected paths exist. `git diff --check`: passed. Applied migration version files have no diff.
