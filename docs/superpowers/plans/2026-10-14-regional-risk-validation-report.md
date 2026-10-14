# Regional Risk Validation Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate reproducible coverage and label-stability evidence for a held regional risk-profile bundle without changing or publishing its labels.

**Architecture:** A single offline ML command verifies saved provenance, replays source parsing and regional assignment, computes pure coverage and comparison summaries, then writes JSON and Markdown. Validation precedes output creation. The existing training and serving paths remain unchanged.

**Tech Stack:** Python 3.11+, pandas, scikit-learn, Shapely through existing ML modules, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-regional-risk-validation-report-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep Python lines within 100 columns and type-hint public functions. Use Conventional Commits.
- Raw source CSVs, saved models, and generated reports stay ignored. Do not embed raw rows or local paths in report output.
- Preserve the quality hold; a successful command means an analysis ran, not that labels are approved.
- Work in `feat/regional-risk-validation`; commit focused tasks. Run `pytest -v` from `ml/`, `python scripts/verify_structure.py`, and `git diff --check` before PR.
- Tests use only tiny fixtures and `tmp_path`, no network or credentials. The local full-data run is separate from unit tests.

---

### Task 1: Validate artifact and source provenance before analysis

**Files:**
- Create: `ml/src/ml/validate_profiles.py`
- Create: `ml/tests/test_validate_profiles.py`

**Interfaces:**
- `build_validation_report(artifact_dir: Path, phivolcs_paths: list[Path], usgs_paths: list[Path]) -> dict[str, object]`
- Internal `_load_verified_inputs(...) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]` returns metadata, saved profiles, and assigned canonical rows. The exact private return type may use a dataclass if it improves clarity.

- [ ] **Step 1: Write failing fixture tests.** Build a small temporary bundle with `metadata.json`, `risk_profiles.json`, and `region_features.csv`. Supply two tiny source CSVs. Assert that a changed source byte, changed boundary digest, missing file, duplicate source path, malformed metadata, and mismatched source or assignment count each raise `ValueError`. Assert no output directory is created by the CLI on these failures. Use `hashlib.sha256(path.read_bytes()).hexdigest()` for fixture records.
- [ ] **Step 2: Run the focused tests to observe the expected import or assertion failures.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
```

- [ ] **Step 3: Implement provenance verification.** Reuse `_validated_source_paths` and `_input_file_record` from `ml.train`, `load_and_merge_sources`, and `assign_regions`. Check `metadata["input_files"]` against the supplied files by `(source, filename, size_bytes, sha256)` after deterministic sorting. Compare `metadata["region_assignment"]["boundary_sha256"]` to `DEFAULT_REGIONS_PATH` and its `max_offshore_km` to `MAX_OFFSHORE_KM`; call `assign_regions` with the recorded distance. Compare parser accepted/rejected and assignment assigned/excluded dictionaries to metadata. Reject malformed fields explicitly before subscripting. Read the saved profiles and feature CSV, require unique `region_name` values, and require their name sets to match. Do not create report outputs here.
- [ ] **Step 4: Run the focused tests and fix only failures in this task.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
```

- [ ] **Step 5: Commit the focused change.**

```powershell
Set-Location ..
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py
git commit -m "feat: verify regional profile report inputs"
```

---

### Task 2: Compute source and regional coverage

**Files:**
- Modify: `ml/src/ml/validate_profiles.py`
- Modify: `ml/tests/test_validate_profiles.py`

**Interfaces:**
- Internal `_coverage(assigned_rows: list[dict[str, object]]) -> dict[str, object]` returns `source_coverage`, `shared_window`, and sorted `regions` data for the report.
- `source_coverage[source]`: `assigned_count`, `first_occurred_at`, `last_occurred_at`.
- `regions[]`: `region_name`, `assigned_by_source`, `first_occurred_at_by_source`, `last_occurred_at_by_source`, `shared_window_count_by_source`.

- [ ] **Step 1: Add failing tests with a few UTC event timestamps in two regions.** Assert exact source and region counts and ISO timestamps, inclusive shared-window endpoints, sorted region order, zero counts for absent sources, and an explicit empty-overlap reason. Keep fixture data inline or in small `ml/tests/fixtures/*.csv` files with resolved absolute paths.
- [ ] **Step 2: Run the focused tests and confirm coverage assertions fail.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
```

- [ ] **Step 3: Implement coverage.** Group assigned deduplicated rows by `source` and `region_name`. Convert `occurred_at` to timezone-aware UTC; reject a row with an invalid timestamp instead of silently shifting it. Define `window_start = max(source minima)` and `window_end = min(source maxima)`. Count rows with `window_start <= occurred_at <= window_end`. If either source has no assigned row or `window_start > window_end`, represent the window as unavailable with a stable reason and zero shared-window counts. Use `None` for a missing per-source span. Never calculate event rates or claim equal reporting sensitivity.
- [ ] **Step 4: Run the focused tests, then commit.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
Set-Location ..
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py
git commit -m "feat: report regional source coverage"
```

---

### Task 3: Record label sensitivity without approval thresholds

**Files:**
- Modify: `ml/src/ml/validate_profiles.py`
- Modify: `ml/tests/test_validate_profiles.py`

**Interfaces:**
- Internal `_label_stability(saved_features: list[RegionFeatures], saved_labels: dict[str, str], shared_rows: list[dict[str, object]]) -> dict[str, object]`.
- Report `shared_window_refit`, `seed_sweep`, and `leave_one_region_out`. Each section records parameters, included regions, `labels` or per-region `change_count`, and `unavailable_reason` when a fit cannot run.

- [ ] **Step 1: Add failing tests for a deterministic four-region feature fixture.** Assert 20 seed fits, one leave-out fit per region, 16 comparable leave-outs for each retained region in a 17-region fixture, saved labels are never modified, and a shared window with fewer than two represented regions records `unavailable_reason`. Build sample `RegionFeatures` directly for pure-function checks; monkeypatch `fit_kmeans` only when isolating loop counting.
- [ ] **Step 2: Run focused tests and verify the new assertions fail.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
```

- [ ] **Step 3: Implement comparisons.** Read `region_features.csv` into `RegionFeatures` including the saved five feature columns, sorted by `region_name`; verify the set matches profiles and saved labels. For shared-window rows, call `build_region_features` then `fit_kmeans` on regions with events if at least two remain. For seed sweep, call `fit_kmeans(saved_features, random_state=seed)` for seeds 0 through 19. For each omitted region, call `fit_kmeans` on the remaining saved features and compare only retained names with saved labels. Record all included names and fit counts; catch only expected insufficient-region conditions and mark them unavailable. Do not treat the Random Forest's in-sample accuracy or `confidence` as validation.
- [ ] **Step 4: Run focused tests, then commit.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
Set-Location ..
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py
git commit -m "feat: report regional label stability"
```

---

### Task 4: Add CLI, report serialization, and guidance

**Files:**
- Modify: `ml/src/ml/validate_profiles.py`
- Modify: `ml/tests/test_validate_profiles.py`
- Modify: `README.md`
- Modify: `docs/data-sources.md`

**Interfaces:**
- CLI arguments: `--artifact-dir PATH`, repeatable `--phivolcs-csv PATH`, repeatable `--usgs-csv PATH`, and `--output-dir PATH`, all required.
- Outputs: `<output-dir>/validation-report.json` and `<output-dir>/validation-report.md`.
- The JSON root includes `artifact_version`, `input_files`, `boundary_sha256`, `assignment_rule`, `source_coverage`, `shared_window`, `regions`, `label_stability`, `review_state`, and `limitations`.

- [ ] **Step 1: Add failing CLI tests.** Run `main([...])` against the small bundle, assert both files are written only on success, JSON has `review_state == "requires_domain_review"`, Markdown has coverage and stability tables and the hold statement, and both omit absolute input paths. Assert missing required arguments and invalid inputs exit nonzero with a concise stderr reason.
- [ ] **Step 2: Run focused tests and confirm expected failures.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
```

- [ ] **Step 3: Implement CLI and serializers.** Use `argparse` required flags and the existing CLI style in `ml.train.main`. Assemble the JSON payload after input and analysis checks. Include `review_state: "requires_domain_review"` and limitations for windowing, catalog completeness, coordinate-spread density, and in-sample classifier metrics. Render a concise Markdown table with escaped region names and counts; write to `--output-dir` only after payload construction succeeds. Document one absolute-path PowerShell invocation in README and explain the coverage caveats in data-source notes.
- [ ] **Step 4: Run focused tests and commit.**

```powershell
Set-Location ml
pytest -v tests/test_validate_profiles.py
Set-Location ..
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py README.md docs/data-sources.md
git commit -m "feat: write offline regional validation reports"
```

---

### Task 5: Run the held snapshot, inspect evidence, and update status

**Files:**
- Modify: `docs/risk-profile-quality-review-2026-10-14.md`
- Modify: `docs/project-status.md`

**Interfaces:**
- Local ignored input bundle: `ml/model_artifacts/snapshots/2026-10-14/v1` in the primary checkout.
- Local ignored input CSVs: `ml/data/raw/bwandowando_philippine-earthquakes-from-phivolcs/phivolcs_earthquake_data.csv` and `ml/data/raw/bwandowando_philippine-earthquakes-1900-2025-from-usgs/Philippine_Earthquakes_USGS.csv` in the primary checkout.
- Local ignored output directory: `ml/model_artifacts/validation/2026-10-14/v1` in the primary checkout.

- [ ] **Step 1: Run full ML package verification and structure checks.**

```powershell
Set-Location ml
pytest -v
Set-Location ..
python scripts/verify_structure.py
git diff --check
```

- [ ] **Step 2: Run the CLI against the exact saved bundle and source paths.** Resolve each primary-checkout path to an absolute path before passing it to the worktree command; avoid copying raw data into the worktree or Git. The command must generate both reports in the ignored output directory.

```powershell
Set-Location ml
$primaryCheckout = 'C:\Users\matth\Documents\WebDevelopment - HTML\PROJECT DEVELOPMENT\geohazard-ph'
$artifactPath = Join-Path $primaryCheckout 'ml\model_artifacts\snapshots\2026-10-14\v1'
$phivolcsPath = Join-Path $primaryCheckout 'ml\data\raw\bwandowando_philippine-earthquakes-from-phivolcs\phivolcs_earthquake_data.csv'
$usgsPath = Join-Path $primaryCheckout 'ml\data\raw\bwandowando_philippine-earthquakes-1900-2025-from-usgs\Philippine_Earthquakes_USGS.csv'
$reportPath = Join-Path $primaryCheckout 'ml\model_artifacts\validation\2026-10-14\v1'
$env:PYTHONPATH = 'src'
py -3.11 -m ml.validate_profiles --artifact-dir $artifactPath --phivolcs-csv $phivolcsPath --usgs-csv $usgsPath --output-dir $reportPath
```

- [ ] **Step 3: Inspect JSON and Markdown.** Confirm input and boundary hashes, source and assignment totals, all 17 regions, NCR counts, shared-window dates and counts, 20 seed fits, and 17 leave-one-out fits. Confirm `requires_domain_review`, no raw rows or local paths, and no modifications to the held `risk_profiles.json` or model files. Record observed values accurately in the quality review and status register. Keep the export held.
- [ ] **Step 4: Run final verification and commit the documentation update.**

```powershell
Set-Location ml
pytest -v
Set-Location ..
python scripts/verify_structure.py
git diff --check
git add docs/risk-profile-quality-review-2026-10-14.md docs/project-status.md
git commit -m "docs: record regional validation evidence"
```

- [ ] **Step 5: Open a PR with Summary, Testing, and Notes; request code review, resolve findings, wait for CI, then merge using the repository workflow.** Report generated evidence as local and ignored; do not attach source CSVs or model artifacts to the PR.

## Notes for the executor

- Tasks 1–4 are sequential because they extend the same report module and tests. Task 5 needs all prior tasks.
- Existing `ml.train._validated_source_paths` and `_input_file_record` are private; importing them is a focused reuse decision for this integration. If that creates a cycle, extract only the common path/hash helpers into a small ML module with tests, keeping training behavior unchanged.
- The held bundle's `input_files` contain filenames and hashes, but no Kaggle version. Do not infer versions from the file names.
- `fit_kmeans` picks K using the current silhouette selection. A fit on a changed region set may change category ordering; record that as sensitivity, not predictive error.
- Keep report fields and terminology aligned with the approved spec and glossary. No threshold in this plan lifts the quality hold.
