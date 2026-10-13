# Source-Safe Offline Risk Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make offline regional risk training assign each CSV to its correct source and record exact input-file provenance.

**Architecture:** Keep source normalization in `clean_merge.py`. Validate and label input paths at the `train.py` boundary, then pass separate path lists through the existing pipeline. Extend the CLI and PowerShell wrapper to supply those lists, and include file digests in training metadata.

**Tech Stack:** Python 3.11, pandas, scikit-learn, pytest, Ruff, PowerShell, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-14-offline-source-safe-training-design.md`

---

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`,
  `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.
- Work on `feat/offline-source-safe-training` in its isolated worktree.
- Use test-first development for ML behavior. Keep source-specific timestamp
  normalization unchanged in `clean_merge.py`.
- Use Conventional Commits; do not commit raw datasets, secrets, caches, or
  generated model artifacts.
- Run `pytest -v` and `ruff check .` from `ml/`, then
  `python scripts/verify_structure.py` and `git diff --check` from the root.
- The Windows workstation has no saved historical CSVs or Kaggle credentials;
  fixture training verifies this code path, not production model quality.

### Task 1: Validate source assignments and record file provenance

**Files:**
- Modify: `ml/src/ml/train.py`
- Test: `ml/tests/test_train.py`

**Interfaces:**
- Keep `run_training(phivolcs_paths, usgs_paths, ..., download)` unchanged.
- Add `metadata.json.input_files`: ordered records with `source`, `filename`,
  `size_bytes`, and lowercase `sha256`.

- [ ] **Step 1: Add failing tests for source-safe training**

In `ml/tests/test_train.py`, import `hashlib` and `pytest`. Add tests with the
existing `FIXTURES` paths:

```python
def test_offline_training_requires_both_sources_before_writing(tmp_path):
    with pytest.raises(ValueError, match="PHIVOLCS and USGS"):
        run_training(
            phivolcs_paths=[FIXTURES / "phivolcs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )
    assert not (tmp_path / "art").exists()


def test_offline_training_rejects_duplicate_source_assignment(tmp_path):
    path = FIXTURES / "phivolcs_sample.csv"
    with pytest.raises(ValueError, match="more than once"):
        run_training(
            phivolcs_paths=[path],
            usgs_paths=[path],
            artifact_dir=tmp_path / "art",
            download=False,
        )
    assert not (tmp_path / "art").exists()


def test_offline_training_rejects_missing_csv(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(ValueError, match="missing.csv"):
        run_training(
            phivolcs_paths=[missing],
            usgs_paths=[FIXTURES / "usgs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )


def test_download_mode_rejects_explicit_source_paths(tmp_path):
    with pytest.raises(ValueError, match="require offline"):
        run_training(
            phivolcs_paths=[FIXTURES / "phivolcs_sample.csv"],
            artifact_dir=tmp_path / "art",
        )
```

Add a non-CSV file case and extend
`test_run_training_from_existing_csvs_writes_artifacts`:

```python
def test_offline_training_rejects_non_csv_input(tmp_path):
    wrong_type = tmp_path / "input.txt"
    wrong_type.write_text("not a CSV", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a CSV"):
        run_training(
            phivolcs_paths=[wrong_type],
            usgs_paths=[FIXTURES / "usgs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )
```

Then extend the existing artifact test:

```python
    assert metadata["source_reports"] == {
        "phivolcs": {"accepted": 2, "rejected": 0},
        "usgs": {"accepted": 2, "rejected": 0},
    }
    assert metadata["input_files"] == [
        {
            "source": source,
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for source, path in (
            ("phivolcs", FIXTURES / "phivolcs_sample.csv"),
            ("usgs", FIXTURES / "usgs_sample.csv"),
        )
    ]
```

Extend the downloaded-version test to assert that its `input_files` contains
both source names while preserving the existing integer versions.

- [ ] **Step 2: Run focused tests and confirm expected failures**

From `ml/`, run `pytest tests/test_train.py -v`. The new missing-source,
duplicate, missing-file, non-CSV, and explicit-download cases must fail on the
current behavior; the metadata assertion must fail because `input_files` is
absent.

- [ ] **Step 3: Implement validation and the input manifest**

Add `import hashlib` to `ml/src/ml/train.py` and these helpers:

```python
def _validated_source_paths(
    phivolcs_paths: list[Path] | None,
    usgs_paths: list[Path] | None,
) -> tuple[list[Path], list[Path]]:
    if not phivolcs_paths or not usgs_paths:
        raise ValueError("Training requires PHIVOLCS and USGS CSV paths.")
    seen: set[Path] = set()
    groups: list[list[Path]] = []
    for source, paths in (("PHIVOLCS", phivolcs_paths), ("USGS", usgs_paths)):
        validated: list[Path] = []
        for path in paths:
            resolved = path.expanduser().resolve()
            if not resolved.is_file():
                raise ValueError(f"{source} CSV file not found: {path}")
            if resolved.suffix.lower() != ".csv":
                raise ValueError(f"{source} input must be a CSV file: {path}")
            if resolved in seen:
                raise ValueError(f"CSV path assigned more than once: {path}")
            seen.add(resolved)
            validated.append(resolved)
        groups.append(sorted(validated))
    return groups[0], groups[1]


def _input_file_record(path: Path, source: str) -> dict[str, str | int]:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "source": source,
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": digest,
    }
```

At the start of `run_training`, reject explicit paths in download mode before
calling `download_datasets`. After either mode obtains paths, call
`_validated_source_paths`. Build `input_files` from both groups in source order,
sorted by filename within each group, and add it to the existing metadata
payload. Retain all existing metadata keys and dataset version handling.

- [ ] **Step 4: Run focused tests and confirm they pass**

Run `pytest tests/test_train.py -v` from `ml/`. Confirm every new failure case,
per-source count, digest, and downloaded-version assertion passes.

- [ ] **Step 5: Commit the ML behavior**

Run `ruff check .` from `ml/`, then `git diff --check` from the root. Commit only
the ML source and test files:

```bash
git add ml/src/ml/train.py ml/tests/test_train.py
git commit -m "fix: preserve source identity in offline risk training"
```

### Task 2: Expose source-specific CSVs in both training commands

**Files:**
- Modify: `ml/src/ml/train.py`
- Modify: `scripts/train_risk_profile_models.ps1`
- Test: `ml/tests/test_train.py`

**Interfaces:**
- Python CLI: repeatable `--phivolcs-csv PATH` and `--usgs-csv PATH` with
  `--offline`.
- PowerShell wrapper: `-PhivolcsCsv <string[]>` and `-UsgsCsv <string[]>` with
  `-Offline`.

- [ ] **Step 1: Add a failing CLI forwarding test**

Update `test_main_offline_disables_download` to call the command with both
source flags and assert exact `Path` lists. Add a repeated-flag case:

```python
def test_main_forwards_repeated_source_csv_flags(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)
    assert train_module.main([
        "--offline",
        "--phivolcs-csv", "first.csv",
        "--phivolcs-csv", "second.csv",
        "--usgs-csv", "usgs.csv",
    ]) == 0
    assert captured["download"] is False
    assert captured["phivolcs_paths"] == [Path("first.csv"), Path("second.csv")]
    assert captured["usgs_paths"] == [Path("usgs.csv")]
```

Import `Path` at the top of the test file. Add a real CLI failure test that
calls `main(["--offline", "--artifact-dir", str(tmp_path)])`, asserts return
code 1, and asserts stderr names both required sources.

- [ ] **Step 2: Run focused CLI tests and confirm expected failures**

Run `pytest tests/test_train.py -v` from `ml/`. The forwarding assertions must
fail because the CLI does not recognize the new flags yet.

- [ ] **Step 3: Add CLI flags and wrapper forwarding**

In `main`, add the two options before `parse_args`, then forward their parsed
values to `run_training`:

```python
parser.add_argument("--phivolcs-csv", action="append", type=Path)
parser.add_argument("--usgs-csv", action="append", type=Path)
# Inside the existing run_training call:
phivolcs_paths=args.phivolcs_csv,
usgs_paths=args.usgs_csv,
```

The validation from Task 1 makes missing offline groups and paths in download
mode fail safely.

In the PowerShell wrapper, extend `param(...)` and build source arguments before
`Set-Location` changes to `ml/`:

```powershell
param(
  [string]$ArtifactVersion = "v1",
  [switch]$Offline,
  [string[]]$PhivolcsCsv = @(),
  [string[]]$UsgsCsv = @()
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Arguments = @("-m", "ml.train", "--artifact-version", $ArtifactVersion)
if ($Offline) { $Arguments += "--offline" }
foreach ($CsvPath in $PhivolcsCsv) {
  $Arguments += @("--phivolcs-csv", (Resolve-Path -LiteralPath $CsvPath).Path)
}
foreach ($CsvPath in $UsgsCsv) {
  $Arguments += @("--usgs-csv", (Resolve-Path -LiteralPath $CsvPath).Path)
}
Set-Location (Join-Path $RepoRoot "ml")
```

Keep the current Python launcher, `PYTHONPATH`, and exit-code code below this
segment.

- [ ] **Step 4: Run focused tests and commit command changes**

Run `pytest tests/test_train.py -v` and `ruff check .` from `ml/`, then
`git diff --check` from the root. Commit:

```bash
git add ml/src/ml/train.py ml/tests/test_train.py scripts/train_risk_profile_models.ps1
git commit -m "feat: accept source-specific offline training files"
```

### Task 3: Update guidance and verify the complete change

**Files:**
- Modify: `README.md`
- Modify: `docs/data-sources.md`
- Modify: `docs/glossary.md`
- Modify: `docs/project-status.md`

**Interfaces:** The public offline commands now require both source groups.

- [ ] **Step 1: Update user and source-data instructions**

Replace the README's implicit `-Offline` example with a source-specific
PowerShell command such as:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Offline `
  -PhivolcsCsv 'ml\data\raw\phivolcs.csv' `
  -UsgsCsv 'ml\data\raw\usgs.csv'
```

Explain that source paths can be arrays, offline dataset versions remain
`null`, and `metadata.json.input_files` records name, size, source, and SHA-256.
In `docs/data-sources.md`, remove the warning about automatic all-PHIVOLCS
discovery and document the required flags and the equivalent Python CLI. In
`docs/glossary.md`, align the metadata entry with the actual fields. In the
Epic 5 row of `docs/project-status.md`, identify source-safe offline training
as implemented while keeping real-data export and staging unverified.

- [ ] **Step 2: Verify all changed surfaces**

From `ml/`, run `pytest -v` and `ruff check .`. From the repository root, run
`python scripts/verify_structure.py` and `git diff --check`. Check README and
source-data examples against the final CLI and wrapper parameter names.

- [ ] **Step 3: Commit documentation**

```bash
git add README.md docs/data-sources.md docs/glossary.md docs/project-status.md
git commit -m "docs: document source-safe offline risk training"
```

## Notes for the executor

- The fixture reproduction before this plan showed four PHIVOLCS rows and zero
  USGS rows for the default offline route; correct fixture routing yields two
  accepted rows per source before cross-source deduplication.
- The 24-test ML baseline passed in the isolated worktree on 2026-10-14.
- Keep input paths out of `metadata.json`; record file names and digests only.
- A green fixture suite does not establish a trained artifact from real Kaggle
  snapshots. Record that deployment prerequisite separately.
