# Real-Snapshot Regional Risk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a source-correct local risk-profile export from the saved PHIVOLCS and USGS snapshots, with reproducible geographic assignment to web regions.

**Architecture:** Keep CSV normalization in `clean_merge.py`, perform geographic assignment in `regions.py` after deduplication, and let `train.py` validate source participation and persist assignment provenance. Use the pinned web boundary asset for names, a 100 km offshore limit, and an ignored local artifact directory.

**Tech Stack:** Python 3.11, pandas, Shapely 2.x, scikit-learn, pytest, Ruff, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-14-real-snapshot-regional-risk-design.md`

---

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Work on `feat/regional-risk-snapshots` in its isolated worktree. Keep the raw CSVs and generated bundle out of Git.
- Use red-green TDD for every behavior change. Do not alter PHIVOLCS Manila time conversion, USGS UTC conversion, or the existing classifier design.
- Run `pytest -v` and `ruff check .` from `ml/`, then `python scripts/verify_structure.py` and `git diff --check` from the repository root. The existing Ruff backlog is non-blocking in ML CI; distinguish old findings from new ones.
- The saved raw files live in the primary checkout, not the worktree. Pass their absolute paths to the final offline training command.

### Task 1: Parse observed PHIVOLCS columns

**Files:**
- Create: `ml/tests/fixtures/phivolcs_kaggle_sample.csv`
- Modify: `ml/tests/test_clean_merge.py`
- Modify: `ml/src/ml/clean_merge.py`

- [ ] **Step 1: Add a small real-header fixture and failing test.** Fixture columns are exactly `Date_Time_PH,Latitude,Longitude,Depth_In_Km,Magnitude,Location,Specific_Location,General_Location`; include two valid records in Bicol and Eastern Visayas with known Manila times. Test:

```python
def test_normalize_csv_accepts_kaggle_phivolcs_headers():
    rows, report = normalize_csv(FIXTURES / "phivolcs_kaggle_sample.csv", "phivolcs")
    assert report.accepted_rows == 2
    assert report.rejected_rows == 0
    assert rows[0]["occurred_at"].isoformat() == "2024-01-01T00:00:00+00:00"
    assert rows[0]["depth_km"] == 34
```

- [ ] **Step 2: Run `pytest tests/test_clean_merge.py::test_normalize_csv_accepts_kaggle_phivolcs_headers -v` from `ml/`.** Expected failure: zero accepted rows because the time and depth aliases are absent.
- [ ] **Step 3: Add the two aliases without changing other mapping.** In `ALIASES`, append `"depth_in_km"` to `depth_km` and `"date_time_ph"` to `occurred_at`. Preserve the existing case-insensitive header lookup.
- [ ] **Step 4: Run the focused test and full `test_clean_merge.py`; both must pass.**
- [ ] **Step 5: Check the diff and commit** `fix: parse observed phivolcs snapshot headers` with only the fixture, test, and parser.

### Task 2: Assign events to web regions with a bounded offshore rule

**Files:**
- Modify: `ml/pyproject.toml`
- Modify: `ml/src/ml/regions.py`
- Create: `ml/tests/test_regions.py`

- [ ] **Step 1: Write synthetic-boundary tests first.** Use `tmp_path` to write a FeatureCollection with two simple square polygons named `First Region` and `Second Region`; test a covered point, a point about 22 km offshore, a point more than 100 km away, and a row with an invalid coordinate. Assert assigned `region_name` values, `assigned_by_source`, and `unassigned_by_source`. Test an empty boundary collection raises `ValueError`. Test the repository's pinned asset resolves regardless of current working directory.

```python
def test_assign_regions_uses_100_km_limit(tmp_path):
    boundary = write_two_square_regions(tmp_path)
    events = [
        {"source": "phivolcs", "latitude": 0.5, "longitude": 0.5},
        {"source": "usgs", "latitude": 0.5, "longitude": 1.2},
        {"source": "usgs", "latitude": 0.5, "longitude": 4.0},
        {"source": "phivolcs", "latitude": "bad", "longitude": 0.5},
    ]
    result = assign_regions(events, regions_path=boundary)
    assert [row["region_name"] for row in result.rows] == ["First Region", "First Region"]
    assert result.assigned_by_source == {"phivolcs": 1, "usgs": 1}
    assert result.unassigned_by_source == {"phivolcs": 1, "usgs": 1}
```

- [ ] **Step 2: Run `pytest tests/test_regions.py -v`.** Expected failure: `RegionAssignment` has no `assigned_by_source`, and the existing helper excludes the nearshore point.
- [ ] **Step 3: Implement one region-assignment rule.** Declare `shapely>=2.1,<3` in `ml/pyproject.toml`. Default `regions_path` to `Path(__file__).resolve().parents[3] / "web/src/data/philippine-regions.json"`. Load and validate nonempty named polygons. Build `STRtree` over geometries; query a point for coverage first. For uncovered points, query a 1.1-degree box, find the closest boundary point for each candidate with `nearest_points`, compute haversine distance in kilometers, and choose the minimum `(distance, region_name)` within `max_offshore_km` (default `100.0`). Count invalid and farther points as unassigned. Return a frozen `RegionAssignment` with rows, total counts, and both per-source count maps. Keep order of input events.
- [ ] **Step 4: Install the declared dependency in the ML virtual environment, then run `pytest tests/test_regions.py -v` and `pytest tests/test_clean_merge.py -v`.** Confirm both pass. Run the region test from the repository root as well to prove path independence.
- [ ] **Step 5: Check the diff and commit** `feat: assign historical events to nearby regions` with only the dependency, module, and test.

### Task 3: Gate training on both sources and record provenance

**Files:**
- Modify: `ml/src/ml/train.py`
- Modify: `ml/tests/test_train.py`

- [ ] **Step 1: Add failing end-to-end fixture tests.** Assert the existing fixture pair still yields two web-region profiles, `metadata["region_assignment"]["max_offshore_km"] == 100.0`, a 64-character lowercase boundary hash, and per-source assigned counts. Add a PHIVOLCS CSV with all malformed depth fields and assert `run_training(download=False, ...)` raises `ValueError` naming PHIVOLCS before an artifact directory exists. Add a synthetic far-offshore pair and assert zero assigned source also fails before writes.
- [ ] **Step 2: Run `pytest tests/test_train.py -v`.** Expected failures: assignment metadata and zero-source gate are absent.
- [ ] **Step 3: Wire the existing stages.** After `load_and_merge_sources`, reject a source with zero `accepted_rows`. Call `assign_regions(merged_rows)` and reject a source with zero assigned rows. Build features from `assignment.rows`. Compute SHA-256 of the pinned boundary asset and include `region_assignment` with `boundary_sha256`, `max_offshore_km: 100.0`, `assigned_by_source`, and `excluded_by_source`. Preserve existing `source_reports`, `input_files`, dataset version, metrics, and export fields. Ensure all gates run before `ArtifactBundle.for_version`.
- [ ] **Step 4: Run the focused test and `pytest -v` from `ml/`; confirm all pass.**
- [ ] **Step 5: Check the diff and commit** `feat: record regional assignment in risk training` with the trainer and test.

### Task 4: Validate a real local export and update operator guidance

**Files:**
- Modify: `README.md`
- Modify: `docs/data-sources.md`
- Modify: `docs/project-status.md`
- Modify: `docs/glossary.md`
- Modify: `docs/runbook.md`
- Local ignored output: `ml/model_artifacts/<version>/`

- [ ] **Step 1: Run offline training with absolute paths to the two saved raw CSVs** from the primary checkout, using `ml.train --offline --phivolcs-csv ... --usgs-csv ... --artifact-version v1 --artifact-dir model_artifacts` from the worktree's `ml/` directory. Use the branch code and the ML virtual environment. Do not copy raw CSVs into Git.
- [ ] **Step 2: Validate the ignored bundle with a read-only script.** Check that all six artifact files exist; both source counts and assigned counts are positive; `input_files` SHA-256 values match the two input files; `boundary_sha256` matches the checked-in asset; all region names in `risk_profiles.json` are among the asset's 17 names; profile JSON parses through `backend.app.schemas.risk_profile.RiskProfile`; metrics and offline `datasets[].version == null` are present. Record measured counts and any warnings. Never treat in-sample accuracy as scientific validation.
- [ ] **Step 3: Update documentation** with the exact 100 km rule, how unassigned records are counted, the accepted-source gate, the saved snapshot provenance limitation, and local export validation result. Keep staging marked unverified because no OCI host/configuration is present.
- [ ] **Step 4: Run final verification:** `pytest -v` and `ruff check .` from `ml/`, then `python scripts/verify_structure.py` and `git diff --check` from root. Inspect `git status --short` to ensure raw files and generated artifacts remain ignored.
- [ ] **Step 5: Commit docs** as `docs: record regional risk snapshot integration`, push the branch, and open a PR with Summary / Testing / Notes. Report any remaining production or staging limits.

## Notes for the executor

- The primary checkout's source paths are `ml/data/raw/bwandowando_philippine-earthquakes-from-phivolcs/phivolcs_earthquake_data.csv` and `ml/data/raw/bwandowando_philippine-earthquakes-1900-2025-from-usgs/Philippine_Earthquakes_USGS.csv`; resolve them to absolute paths when running from the worktree.
- A prior trial was stopped before artifacts because the PHIVOLCS header aliases were missing and free-text places could not join regional boundaries.
- The local snapshots have no Kaggle credential/version record. The input SHA-256 manifest, not a guessed version, identifies the bytes used.
- The first 31 ML tests pass on merged main before this plan. The final export must be validated separately.
