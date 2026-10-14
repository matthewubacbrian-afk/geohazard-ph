# Regional Risk Sparse-Region Sensitivity — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the held-bundle validation report with data-derived event-count cutoff scenarios that quantify region inclusion and label sensitivity without selecting a sparse-region policy.

**Architecture:** Build shared-window features once from the already verified event rows. Feed those features and the per-region shared-window source counts to a pure sensitivity helper. Add deterministic JSON and Markdown output, then document the full-data evidence while preserving the export hold.

**Tech Stack:** Python 3.11, pandas, scikit-learn, pytest, Ruff, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-14-regional-risk-sparse-region-sensitivity-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md` only if backend is touched, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep Python lines within 100 columns; type-hint public functions; use Conventional Commits.
- Keep the held artifact, local CSVs, models, and generated reports unchanged or ignored. Do not commit raw data or generated artifacts.
- Cutoffs are derived from observed shared-window counts and are not policy recommendations. Keep report state `requires_domain_review` and the staging hold.
- Work in `feat/regional-risk-sensitivity`. Use fixture-only unit tests, then run full ML verification and one local full-data report run.

---

### Task 1: Add the pure cutoff sensitivity calculation

**Files:**
- Modify: `ml/tests/test_validate_profiles.py`
- Modify: `ml/src/ml/validate_profiles.py`

**Interfaces:**
- Add `_sparse_region_sensitivity(region_coverage: list[dict[str, object]], saved_labels: dict[str, str], shared_features: list[RegionFeatures]) -> dict[str, object]`.
- Return `count_basis`, `thresholds_are_policy`, `comparison_parameters`, and ordered `scenarios` as specified in the design.

- [ ] **Step 1: Write a failing test for observed breakpoints, inclusive eligibility, comparisons, and no-fit scenarios.** Append this test to `ml/tests/test_validate_profiles.py`:

```python
def test_sparse_region_sensitivity_uses_shared_window_breakpoints(monkeypatch):
    from types import SimpleNamespace

    import ml.validate_profiles as validation

    counts = [
        {"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 2}},
        {"region_name": "B", "shared_window_count_by_source": {"phivolcs": 2, "usgs": 2}},
        {"region_name": "C", "shared_window_count_by_source": {"phivolcs": 3, "usgs": 3}},
    ]
    features = [
        RegionFeatures("A", 3, 4.0, 5.0, 10.0, 1.0),
        RegionFeatures("B", 4, 4.5, 6.0, 20.0, 2.0),
        RegionFeatures("C", 6, 5.0, 7.0, 30.0, 3.0),
    ]
    saved = {"A": "Low", "B": "Moderate", "C": "Moderate"}
    fit_sizes = []

    def fake_fit(rows, k_values, random_state):
        names = [row.region_name for row in rows]
        fit_sizes.append(len(names))
        labels = {"A": "Low", "B": "Moderate", "C": "High"}
        return SimpleNamespace(risk_labels={name: labels[name] for name in names})

    monkeypatch.setattr(validation, "fit_kmeans", fake_fit)
    result = validation._sparse_region_sensitivity(counts, saved, features)

    assert result["count_basis"] == "combined_sources_in_shared_window"
    assert result["thresholds_are_policy"] is False
    scenarios = result["scenarios"]
    assert [item["minimum_shared_window_events"] for item in scenarios] == [0, 4, 5, 7]
    assert scenarios[1]["included_regions"] == ["B", "C"]
    assert scenarios[1]["excluded_regions"] == ["A"]
    assert scenarios[1]["changed_regions"] == ["C"]
    assert scenarios[1]["change_count"] == 1
    assert scenarios[1]["exclusion_reason_by_region"] == {
        "A": "below_minimum_event_count"
    }
    assert scenarios[-1]["labels"] is None
    assert scenarios[-1]["unavailable_reason"] == "insufficient_regions"
    assert fit_sizes == [3, 2]
```

Also add these two tests:

```python
def test_sparse_region_sensitivity_treats_missing_coverage_as_zero():
    from ml.validate_profiles import _sparse_region_sensitivity

    result = _sparse_region_sensitivity(
        [{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 0}}],
        {"A": "Low", "No events": "Moderate"},
        [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
    )

    first = result["scenarios"][0]
    assert first["excluded_regions"] == ["No events"]
    assert first["exclusion_reason_by_region"] == {
        "No events": "no_shared_window_observations"
    }


@pytest.mark.parametrize(
    "coverage, saved, features",
    [
        ([{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1}}],
         {"A": "Low"}, [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)]),
        ([{"region_name": "A", "shared_window_count_by_source": {"phivolcs": -1, "usgs": 2}}],
         {"A": "Low"}, [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)]),
        ([{"region_name": "B", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 0}}],
         {"A": "Low"}, [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)]),
        ([{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 1}}],
         {"A": "Low"}, [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)]),
    ],
)
def test_sparse_region_sensitivity_rejects_malformed_counts(coverage, saved, features):
    from ml.validate_profiles import _sparse_region_sensitivity

    with pytest.raises(ValueError):
        _sparse_region_sensitivity(coverage, saved, features)
```

- [ ] **Step 2: Run the focused test and confirm it fails because the helper is not defined.**

```powershell
Set-Location ml
pytest -q tests/test_validate_profiles.py::test_sparse_region_sensitivity_uses_shared_window_breakpoints
```

Expected: one failure naming missing `_sparse_region_sensitivity`.

- [ ] **Step 3: Implement the helper in `ml/src/ml/validate_profiles.py` using this control flow.** Validate one coverage row per known saved region; require nonnegative integer `phivolcs` and `usgs` counts. A saved region with no coverage row has zero counts. Reject coverage rows for unknown regions and shared features with duplicate or unknown names. Reject a positive shared-window count without a feature row and reject a feature `event_count` that differs from the combined source count. The helper body should follow this complete structure:

```python
def _sparse_region_sensitivity(
    region_coverage: list[dict[str, object]],
    saved_labels: dict[str, str],
    shared_features: list[RegionFeatures],
) -> dict[str, object]:
    names = sorted(saved_labels)
    coverage_by_name: dict[str, int] = {}
    for region in region_coverage:
        name = region.get("region_name")
        if not isinstance(name, str) or name not in saved_labels:
            raise ValueError("Coverage includes a region absent from saved labels.")
        if name in coverage_by_name:
            raise ValueError(f"Coverage repeats region: {name}")
        source_counts = region.get("shared_window_count_by_source")
        if not isinstance(source_counts, dict):
            raise ValueError(  # noqa: TRY004
                f"Coverage counts are missing for region: {name}"
            )
        values = [source_counts.get(source) for source in ("phivolcs", "usgs")]
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise ValueError(f"Coverage counts are invalid for region: {name}")
        coverage_by_name[name] = sum(values)

    features_by_name: dict[str, RegionFeatures] = {}
    for feature in shared_features:
        name = feature.region_name
        if name not in saved_labels or name in features_by_name:
            raise ValueError(f"Shared-window features have an invalid region: {name}")
        features_by_name[name] = feature

    counts = {name: coverage_by_name.get(name, 0) for name in names}
    for name, feature in features_by_name.items():
        if feature.event_count != counts[name]:
            raise ValueError(f"Shared-window count does not match features for region: {name}")
    if any(count > 0 and name not in features_by_name for name, count in counts.items()):
        raise ValueError("Positive shared-window count has no feature row.")

    thresholds = [0, *sorted({count + 1 for count in counts.values()})]
    scenarios: list[dict[str, object]] = []
    for threshold in thresholds:
        included = sorted(
            name for name in names
            if name in features_by_name and counts[name] >= threshold
        )
        excluded = sorted(set(names).difference(included))
        reasons = {
            name: (
                "no_shared_window_observations"
                if name not in features_by_name
                else "below_minimum_event_count"
            )
            for name in excluded
        }
        labels = None
        changed = None
        change_count = None
        unavailable_reason = "insufficient_regions"
        if len(included) >= 2:
            rows = [features_by_name[name] for name in included]
            labels = fit_kmeans(
                rows,
                k_values=REFIT_K_CANDIDATES,
                random_state=REFIT_RANDOM_STATE,
            ).risk_labels
            labels = dict(sorted(labels.items()))
            changed = sorted(name for name in included if labels[name] != saved_labels[name])
            change_count = len(changed)
            unavailable_reason = None
        scenarios.append({
            "minimum_shared_window_events": threshold,
            "included_regions": included,
            "excluded_regions": excluded,
            "exclusion_reason_by_region": reasons,
            "labels": labels,
            "changed_regions": changed,
            "change_count": change_count,
            "unavailable_reason": unavailable_reason,
        })

    return {
        "count_basis": "combined_sources_in_shared_window",
        "thresholds_are_policy": False,
        "comparison_parameters": {
            "k_candidates": list(REFIT_K_CANDIDATES),
            "random_state": REFIT_RANDOM_STATE,
            "parameter_match_verified": False,
        },
        "scenarios": scenarios,
    }
```

The threshold list is `0` plus `count + 1` for every distinct combined count.
Each scenario therefore records one data-derived inclusion transition.

- [ ] **Step 4: Run the focused test and confirm it passes.**

```powershell
Set-Location ml
pytest -q tests/test_validate_profiles.py::test_sparse_region_sensitivity_uses_shared_window_breakpoints
```

Expected: one passing test.

- [ ] **Step 5: Commit the helper and focused test.**

```powershell
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py
git commit -m "feat: analyze sparse region cutoff sensitivity"
```

---

### Task 2: Add sensitivity scenarios to JSON and Markdown reports

**Files:**
- Modify: `ml/src/ml/validate_profiles.py`
- Modify: `ml/tests/test_validate_profiles.py`

**Interfaces:**
- Build shared-window `RegionFeatures` once in `build_validation_report` and pass them to both `_label_stability` and `_sparse_region_sensitivity`.
- Add `sparse_region_sensitivity` to the validation report object.
- Render a `Sparse-region cutoff sensitivity` Markdown section with a scenario table and region inclusion/exclusion details.

- [ ] **Step 1: Add integration assertions to `test_cli_writes_json_and_markdown_on_success`.** After parsing `payload` and `markdown`, assert:

```python
    sensitivity = payload["sparse_region_sensitivity"]
    assert sensitivity["thresholds_are_policy"] is False
    assert sensitivity["count_basis"] == "combined_sources_in_shared_window"
    assert sensitivity["scenarios"][0]["minimum_shared_window_events"] == 0
    assert "Sparse-region cutoff sensitivity" in markdown
    assert "not a policy cutoff" in markdown.lower()
```

- [ ] **Step 2: Run the CLI test and confirm it fails because the report field is absent.**

```powershell
Set-Location ml
pytest -q tests/test_validate_profiles.py::test_cli_writes_json_and_markdown_on_success
```

Expected: failure on missing `sparse_region_sensitivity`.

- [ ] **Step 3: Wire shared features into report generation and rendering.** In `build_validation_report`, after `shared_rows` is calculated, build `shared_features` with `list(build_region_features(shared_rows).values())` and sort it by `region_name`. Change `_label_stability` to accept `shared_features: list[RegionFeatures]` instead of raw rows and use it directly for `shared_window_refit`. Update `test_label_stability_runs_seed_and_leave_one_out_comparisons` to keep its empty feature list, and rename `test_label_stability_refits_shared_window_rows` to `test_label_stability_refits_shared_window_features`; the renamed test passes `rows[:2]` as the shared features and no longer constructs raw shared event dictionaries. Add the helper result:

```python
"sparse_region_sensitivity": _sparse_region_sensitivity(
    coverage["regions"], saved_labels, shared_features
),
```

In `_render_markdown`, add a table with columns `Minimum shared-window events`,
`Included regions`, `Excluded regions`, `Changed labels`, and `Fit status`. Add
one line per scenario showing sorted included and excluded names, and state
that data-derived breakpoints are exploratory, are not policy recommendations,
and do not equalize source completeness. Render `unavailable_reason` for
scenarios that were not fitted. Keep the existing report review state unchanged.

- [ ] **Step 4: Run the full focused module and confirm it passes.**

```powershell
Set-Location ml
pytest -q tests/test_validate_profiles.py
```

Expected: all tests in `test_validate_profiles.py` pass.

- [ ] **Step 5: Commit report integration.**

```powershell
git add ml/src/ml/validate_profiles.py ml/tests/test_validate_profiles.py
git commit -m "feat: include cutoff scenarios in validation reports"
```

---

### Task 3: Document terminology, evidence, and held status

**Files:**
- Modify: `docs/glossary.md`
- Modify: `docs/risk-profile-quality-review-2026-10-14.md`
- Modify: `docs/project-status.md`
- Modify: `README.md`

- [ ] **Step 1: Add the glossary definition.** Under Pipeline and Artifacts, add `event-count cutoff sensitivity` with the spec definition: an exploratory comparison of regional inclusion and label changes across minimum shared-window counts; it does not determine policy.

- [ ] **Step 2: Regenerate the ignored report from the held local bundle and saved CSVs.** From the repository root, run:

```powershell
Set-Location ml
$mlRoot = (Get-Location).Path
$artifactDir = Join-Path $mlRoot 'model_artifacts\snapshots\2026-10-14\v1'
$phivolcsCsv = Join-Path $mlRoot 'data\raw\bwandowando_philippine-earthquakes-from-phivolcs\phivolcs_earthquake_data.csv'
$usgsCsv = Join-Path $mlRoot 'data\raw\bwandowando_philippine-earthquakes-1900-2025-from-usgs\Philippine_Earthquakes_USGS.csv'
$reportDir = Join-Path $mlRoot 'model_artifacts\validation\2026-10-14\v1'
$beforeHashes = Get-ChildItem $artifactDir -File -Recurse | Get-FileHash -Algorithm SHA256 | Select-Object Path, Hash
$env:PYTHONPATH = 'src'
py -3.11 -m ml.validate_profiles `
  --artifact-dir $artifactDir `
  --phivolcs-csv $phivolcsCsv `
  --usgs-csv $usgsCsv `
  --output-dir $reportDir
if ($LASTEXITCODE -ne 0) { throw 'Validation report command failed.' }
$afterHashes = Get-ChildItem $artifactDir -File -Recurse | Get-FileHash -Algorithm SHA256 | Select-Object Path, Hash
if (Compare-Object $beforeHashes $afterHashes -Property Path, Hash) { throw 'Held artifact files changed.' }
Set-Location ..
```

Expected: exit code 0 and both ignored report files are written. Confirm JSON
has every threshold scenario, all 17 saved region names appear in at least one
included/excluded list, and `review_state` remains `requires_domain_review`.
Compare SHA-256 hashes of all held bundle files before and after the command;
they must be identical.

- [ ] **Step 3: Record actual scenario evidence in the quality review and status register.** Summarize the data-derived threshold range, which regions are excluded at the first nonzero transition and later transitions, the refit label changes, and the limitation that these are not approved cutoffs. Keep the hold language. In `docs/project-status.md`, update Epic 5 evidence and retain the next action for domain review; do not describe a sparse policy as decided.

- [ ] **Step 4: Update README report description.** Say that the offline command includes data-derived shared-window count breakpoints and label sensitivity, and that the cutoffs are exploratory rather than recommended policy. Preserve the existing command because there is no new CLI option.

- [ ] **Step 5: Run required verification.**

```powershell
Set-Location ml
pytest -v
ruff check src/ml/validate_profiles.py tests/test_validate_profiles.py
Set-Location ..
python scripts/verify_structure.py
git diff --check
```

Expected: the complete ML suite passes, Ruff reports no errors, all expected
scaffold paths exist, and `git diff --check` produces no output.

- [ ] **Step 6: Commit documentation and final evidence.**

```powershell
git add README.md docs/glossary.md docs/project-status.md docs/risk-profile-quality-review-2026-10-14.md
git commit -m "docs: record sparse region sensitivity evidence"
```

## Notes for the executor

- The reviewed spec is the source for threshold semantics and report fields.
- The current module test suite has a passing baseline of 57 tests in this worktree.
- The fixture bundle in `saved_bundle` uses a tiny sample and no network access; the held production-like snapshot and CSVs exist only in ignored local artifacts.
- Do not commit the generated `ml/model_artifacts/validation/2026-10-14/v1` reports or any snapshot inputs.
- After implementation, use the previously approved inline execution workflow with checkpoints and normal code review/CI before merging.
