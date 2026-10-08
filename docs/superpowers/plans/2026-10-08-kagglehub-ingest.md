# Kagglehub Ingest Swap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `kaggle` package with `kagglehub` in the ML ingest, make fresh download the default training behavior (`--offline` for local CSVs), and record the Kaggle dataset version in `metadata.json` so retrains are distinguishable.

**Architecture:** `ingest_kaggle.py` keeps its public shape (`download_datasets` → `list[DownloadedDataset]`) but swaps the internal call to `kagglehub.dataset_download(..., output_dir=..., force_download=True)` and gains a `version` field sourced from kagglehub's completion marker. The `api=` seam becomes a `downloader=` callable seam so tests inject fakes. `train.py` flips its default to download and adds `--offline`.

**Tech Stack:** Python 3.11, `kagglehub~=1.0.2`, pandas, scikit-learn, pytest, ruff.

**Spec:** Session requirements (items 1-8; scheduled monthly retraining is explicitly out of scope) + `docs/superpowers/specs/2026-08-27-kaggle-risk-profile-pipeline-design.md` (provenance: dataset snapshot must be recorded) + `geohazard-development-framework.md:152` (cluster→label pinning is P0).

## Global Constraints

- Branch: `feat/kagglehub-ingest`; Conventional Commits, imperative, one logical change per commit.
- Python line length 100 (ruff); type hints on public functions.
- **Credentials unchanged:** `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars or `~/.kaggle/kaggle.json` (verified: kagglehub 1.0.2 `config.py` reads all three).
- **No network in tests** — fake downloader / monkeypatch only (`docs/testing-standards.md:94`).
- Verification per task: `pytest -v` and `ruff check .` from `ml/`; final: `python scripts\verify_structure.py` + `git diff --check` from root.
- Dependency pin `kagglehub~=1.0.2` (not `>=`): our code reads kagglehub's internal `.complete` marker layout; `~=` allows 1.0.x patches but blocks a 1.1 layout change from silently breaking version capture.
- `force_download=True` on every run is mandatory (see Verified API Facts) — do not "optimize" it away.

## Verified API Facts (confirmed against installed kagglehub 1.0.2 — do not re-derive)

- Installed: **kagglehub 1.0.2** on Python 3.11 (`C:\Users\matth\AppData\Local\Programs\Python\Python311\Lib\site-packages`).
- Signature: `dataset_download(handle: str, path: str | None = None, *, force_download: bool | None = False, output_dir: str | None = None) -> str` — **`output_dir` supported**.
- Returns **only the path**; the internal resolver returns `(path, version)` but the public function discards the version.
- With `output_dir`: files extract **flat** into `output_dir` (no `versions/N` path segment). The version appears only in the completion marker: `output_dir/.complete/datasets/<owner>/<slug>/<version>/bundle.complete`.
- **Trap:** with `output_dir` non-empty and no marker for the current version, `force_download=False` raises `FileExistsError` — a Kaggle monthly version bump hits exactly this path. **`force_download=True` is mandatory**; it also clears legacy dirs from the old `kaggle` package and leaves exactly one version marker (code therefore reads `max()` over markers defensively).
- `dataset_load`/`load_dataset` (DataFrame adapter) is **not** used — the pipeline is path-based (`train.py:41` glob → `clean_merge.py:51`), so `dataset_download` is the drop-in.
- **train.py reads CSVs from downloader-returned paths:** `train.py:41` does `list(dataset.path.rglob("*.csv"))` and routes by `"phivolcs" in dataset.slug` (line 42). The fake-download test in Task 3 depends on this and asserts `profile_count == 2` to prove it.

## Review Focus

1. **Kaggle publishes a new version while `data/raw/<slug>` is non-empty** → kagglehub `FileExistsError` without force. Design: always `force_download=True`. Test: `_read_dataset_version` returns the **max** marker version when multiple marker dirs exist (Task 1).
2. **Slug → directory naming and version propagation through the seam** must survive the refactor (`train.py:42` routes on `"phivolcs" in slug`). Test: `test_download_datasets_calls_downloader` asserts slug, `raw/owner_example` path, and `version == 7` from the fake (Task 1).
3. **Default-on download must never hit the network in tests.** Tests only reach the download branch through monkeypatched `ml.train.download_datasets`. Tests: CLI wiring tests for default vs `--offline` (Task 2) and fake-download data-flow test (Task 3).
4. **Offline runs must not silently claim a dataset version** (thesis provenance). Test: offline metadata asserts `"version" is None` (Task 3).
5. **Cluster IDs reshuffle between retrains → silent mislabel (P0).** Enforcement exists (`clustering.py:64-88` pins by centroid severity, independent of KMeans IDs) but is **untested for the fit_kmeans path** (existing `test_assign_risk_labels_orders_clusters_by_severity` exercises the non-KMeans `assign_risk_labels` branch; the consistency test only checks same-cluster agreement). Tests: two added in Task 4, mutation-verified.

## Seed analysis for Task 4 (read-only verified)

Fixture rows through `fit_kmeans(k_values=[3])` cluster IDs:

```
seed 0 : Palawan id 1, Eastern id 0    seed 7 : Palawan id 0, Eastern id 2
seed 1 : Palawan id 1, Eastern id 0    seed 42: Palawan id 2, Eastern id 1
```

`random_state=7` is a **bad choice**: Palawan lands in cluster id 0, so an identity (broken) mapping would still yield "Low" and the test would falsely pass. `random_state=42`: under identity mapping Palawan (id 2) → "High" → test **deterministically fails** if severity ordering is removed. Use **42**.

---

### Task 1: Swap `ingest_kaggle.py` to kagglehub

**Files:**
- Modify: `ml/src/ml/ingest_kaggle.py`
- Modify: `ml/pyproject.toml:10`
- Test: `ml/tests/test_ingest_kaggle.py`

**Interfaces:**
- Produces (Task 3 relies on these):
  - `DownloadedDataset(slug: str, title: str, license_name: str, path: Path, version: int)` — new field appended last.
  - `download_datasets(raw_dir: Path, datasets: tuple[KaggleDataset, ...] | list[KaggleDataset] = DEFAULT_DATASETS, downloader: Callable[[str, Path], tuple[str, int]] | None = None) -> list[DownloadedDataset]`
  - `_kagglehub_download(slug: str, output_dir: Path) -> tuple[str, int]`
  - `_read_dataset_version(output_dir: Path, slug: str) -> int`

- [ ] **Step 1: Rewrite the failing tests**

Keep `test_download_datasets_requires_credentials_when_config_missing` unchanged (credential behavior untouched). Replace `test_download_datasets_calls_kaggle_api` with:

```python
def test_download_datasets_calls_downloader(tmp_path):
    calls: list[tuple[str, str]] = []

    def fake_downloader(slug: str, output_dir: Path) -> tuple[str, int]:
        calls.append((slug, str(output_dir)))
        return str(output_dir), 7

    datasets = [KaggleDataset("owner/example", "Example", "License")]

    downloaded = download_datasets(
        tmp_path / "raw", datasets=datasets, downloader=fake_downloader
    )

    assert downloaded[0].slug == "owner/example"
    assert downloaded[0].version == 7
    assert downloaded[0].path == tmp_path / "raw" / "owner_example"
    assert calls == [("owner/example", os.fspath(tmp_path / "raw" / "owner_example"))]
```

Add marker-parsing tests (file-only, no network):

```python
def test_read_dataset_version_returns_marker_version(tmp_path):
    marker = (tmp_path / ".complete" / "datasets" / "owner" / "example" / "7")
    marker.mkdir(parents=True)
    (marker / "bundle.complete").touch()

    assert _read_dataset_version(tmp_path, "owner/example") == 7


def test_read_dataset_version_returns_highest_when_markers_accumulate(tmp_path):
    for version in (3, 11):
        d = (tmp_path / ".complete" / "datasets" / "owner" / "example" / str(version))
        d.mkdir(parents=True)
        (d / "bundle.complete").touch()

    assert _read_dataset_version(tmp_path, "owner/example") == 11
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ingest_kaggle.py -v` (from `ml/`)
Expected: FAIL — `download_datasets() got an unexpected keyword argument 'downloader'` / import of `_read_dataset_version` fails.

- [ ] **Step 3: Update `ml/pyproject.toml`**

Replace line 10 `"kaggle>=1.6.17"` with `"kagglehub~=1.0.2"`. Then reinstall: `pip install -e ".[dev]"` (from `ml/`, Python 3.11).

- [ ] **Step 4: Implement in `ml/src/ml/ingest_kaggle.py`**

- Delete `_load_default_api` and the `kaggle` import; keep `KaggleCredentialError`, `KaggleDataset`, `DownloadedDataset` (add `version: int`), `DEFAULT_DATASETS`, `_has_credentials` exactly as they are.
- Add `_read_dataset_version(output_dir, slug)`: split slug on `"/"`, list `<output_dir>/.complete/datasets/<owner>/<slug>/*/` dirs whose `bundle.complete` exists, return `max(int(name))`; raise `RuntimeError(f"Could not determine Kaggle dataset version for {slug}.")` if none.
- Add `_kagglehub_download(slug, output_dir)` → lazy `import kagglehub` (raise `KaggleCredentialError("Install the kagglehub package before downloading datasets.")` on `ImportError`, matching the existing pattern) → `kagglehub.dataset_download(slug, output_dir=str(output_dir), force_download=True)` → `return Path(path), _read_dataset_version(output_dir, slug)`.
- `download_datasets`: keep the credential check and `dataset_dir.mkdir(parents=True, exist_ok=True)` (an existing-but-empty dir is safe for kagglehub); resolve `dl = downloader or _kagglehub_download`; in the loop `path, version = dl(dataset.slug, dataset_dir)`; append `DownloadedDataset(dataset.slug, dataset.title, dataset.license_name, Path(path), version)`.
- `force_download=True` is load-bearing (Verified API Facts) — do not "optimize" it away.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_ingest_kaggle.py -v` (from `ml/`) → PASS; then `ruff check .` → clean.

- [ ] **Step 6: Commit**

```bash
git add ml/src/ml/ingest_kaggle.py ml/pyproject.toml ml/tests/test_ingest_kaggle.py
git commit -m "feat: use kagglehub for kaggle dataset downloads"
```

---

### Task 2: Default download in `train.py`, add `--offline`

**Files:**
- Modify: `ml/src/ml/train.py:32,36-50,147,155`
- Modify: `scripts/train_risk_profile_models.ps1:1-13`
- Modify: `README.md:251-255,345` and `README.md:88` (command examples only — narrative belongs to Task 5)
- Modify: `CODING_STANDARDS.md:702`
- Test: `ml/tests/test_train.py`

**Interfaces:**
- `run_training(..., download: bool = True, ...)` — parameter keeps its name, default flips.
- CLI: `--offline` replaces `--download`; `run_training(download=not args.offline)`.
- PS script: `[switch]$Offline` replaces `[switch]$Download`; adds `--offline` when set.

- [ ] **Step 1: Write the failing CLI wiring tests**

```python
def test_main_offline_flag_passes_download_false(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)

    assert train_module.main(["--offline"]) == 0
    assert captured["download"] is False


def test_main_defaults_to_download(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)

    assert train_module.main([]) == 0
    assert captured["download"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_train.py -v` (from `ml/`)
Expected: FAIL — `main([])` yields `download is False` (old `--download` default).

- [ ] **Step 3: Implement**

- `train.py`: `download: bool = True` in `run_training` signature; delete the `--download` argument; add `parser.add_argument("--offline", action="store_true", help="Train from local data/raw CSVs instead of downloading")`; pass `download=not args.offline`.
- `train_risk_profile_models.ps1`: rename switch to `$Offline`, append `--offline` instead of `--download`.
- `README.md` + `CODING_STANDARDS.md:702`: swap `-Download` examples to the bare command and add an `-Offline` example (`.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Offline`). README line 88 → "Kaggle credentials are needed for training unless you pass `--offline`."

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -v` (from `ml/`) → all PASS (existing tests already pass `download=False` explicitly); `ruff check .` → clean.

- [ ] **Step 5: Commit**

```bash
git add ml/src/ml/train.py scripts/train_risk_profile_models.ps1 ml/tests/test_train.py README.md CODING_STANDARDS.md
git commit -m "feat: download datasets by default and add offline flag"
```

---

### Task 3: Record dataset version in `metadata.json`

**Files:**
- Modify: `ml/src/ml/train.py:36-50,96-112`
- Test: `ml/tests/test_train.py`

**Interfaces:**
- Consumes: `DownloadedDataset.version` (Task 1).
- Produces: `metadata.json` → `datasets[i]` gains `"version": int | None`.

- [ ] **Step 1: Write the failing metadata tests**

```python
def test_run_training_records_dataset_versions_in_metadata(tmp_path, monkeypatch):
    import shutil
    from ml import train as train_module
    from ml.ingest_kaggle import DownloadedDataset

    phivolcs_dir = tmp_path / "raw" / "bwandowando_philippine-earthquakes-from-phivolcs"
    usgs_dir = tmp_path / "raw" / "bwandowando_philippine-earthquakes-1900-2025-from-usgs"
    phivolcs_dir.mkdir(parents=True)
    usgs_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "phivolcs_sample.csv", phivolcs_dir)
    shutil.copy(FIXTURES / "usgs_sample.csv", usgs_dir)

    fake = [
        DownloadedDataset(
            "bwandowando/philippine-earthquakes-from-phivolcs",
            "Philippine Earthquakes from PHIVOLCS",
            "CC0: Public Domain",
            phivolcs_dir,
            12,
        ),
        DownloadedDataset(
            "bwandowando/philippine-earthquakes-1900-2025-from-usgs",
            "Philippine Earthquakes 1900-2026 from USGS",
            "Apache 2.0",
            usgs_dir,
            31,
        ),
    ]
    monkeypatch.setattr(train_module, "download_datasets", lambda raw_dir: fake)

    result = train_module.run_training(
        artifact_dir=tmp_path / "art",
        artifact_version="v-test",
        k_values=[2],
        random_state=7,
    )

    # Proves train.py read the CSVs from the downloader-returned paths
    # (train.py:41 globs dataset.path; the fixtures exist only in those dirs).
    assert result.profile_count == 2

    metadata = json.loads(
        (tmp_path / "art" / "v-test" / "metadata.json").read_text(encoding="utf-8")
    )
    versions = {d["slug"]: d["version"] for d in metadata["datasets"]}
    assert versions["bwandowando/philippine-earthquakes-from-phivolcs"] == 12
    assert versions["bwandowando/philippine-earthquakes-1900-2025-from-usgs"] == 31


def test_run_training_offline_metadata_has_null_version(tmp_path):
    from ml.train import run_training

    result = run_training(
        phivolcs_paths=[(FIXTURES / "phivolcs_sample.csv")],
        usgs_paths=[(FIXTURES / "usgs_sample.csv")],
        artifact_dir=tmp_path,
        artifact_version="v-test",
        download=False,
        k_values=[2],
        random_state=7,
    )

    assert result.profile_count == 2
    metadata = json.loads(
        (tmp_path / "v-test" / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["datasets"][0]["version"] is None
    assert all(entry["version"] is None for entry in metadata["datasets"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_train.py -v` (from `ml/`)
Expected: FAIL — `datasets[0]` has no `"version"` key.

- [ ] **Step 3: Implement in `train.py`**

In `run_training`, build `dataset_entries` once:
- download branch: after `downloaded = download_datasets(Path("data/raw"))`, build entries from `downloaded` including `"version": dataset.version`.
- else (offline) branch: build entries from `DEFAULT_DATASETS` with `"version": None`.
Then `save_metadata(..., "datasets": dataset_entries, ...)` (replacing the current `DEFAULT_DATASETS` comprehension at lines 102-105). Leave `dataset_snapshot` (line 91) untouched.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -v` (from `ml/`) → PASS; `ruff check .` → clean.

- [ ] **Step 5: Commit**

```bash
git add ml/src/ml/train.py ml/tests/test_train.py
git commit -m "feat: record dataset version in training metadata"
```

---

### Task 4: Pin cluster→label mapping tests (P0)

**Files:**
- Test: `ml/tests/test_clustering.py` (no source change — enforcement confirmed at `clustering.py:64-79` + `82-88`)

- [ ] **Step 1: Add the two failing tests**

`random_state=42` is mandatory here — see "Seed analysis for Task 4": with seed 7 the first test would pass even against broken (identity) ordering.

```python
def test_fit_kmeans_pins_labels_by_ascending_mean_magnitude():
    from ml.clustering import RISK_LABELS

    result = fit_kmeans(_rows(), k_values=[3], random_state=42)
    labels = result.risk_labels

    assert labels["Palawan"] == "Low"  # lowest mean magnitude (3.4)
    assert RISK_LABELS.index(labels["Eastern Visayas"]) > RISK_LABELS.index(labels["Palawan"])


def test_cluster_severity_order_ignores_cluster_id_numbering():
    import numpy as np
    import pandas as pd
    from ml.clustering import FEATURE_COLUMNS, _cluster_severity_order

    matrix = pd.DataFrame(
        [
            [2, 3.4, 3.6, 22.0, 0.2],
            [3, 3.6, 3.8, 23.0, 0.3],
            [12, 6.0, 6.2, 39.5, 0.8],
            [10, 5.8, 6.0, 30.0, 0.7],
        ],
        columns=FEATURE_COLUMNS,
    )
    # Low-magnitude regions deliberately carry the HIGH cluster id (1).
    severity_map = _cluster_severity_order(matrix, np.array([1, 1, 0, 0]), 2)

    assert severity_map[1] == 0  # id numbering cannot flip the label order
    assert severity_map[0] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clustering.py -v` (from `ml/`)
Expected: FAIL — the ordering assertion is new (or `_cluster_severity_order` import rejected if missing — it exists at `clustering.py:64`).

- [ ] **Step 3: Verify they pass without source changes**

Run: `pytest tests/test_clustering.py -v` → PASS. If the first test fails on partition surprise, fix the assertion (keep `k_values=[3]` — `choose_k` is forced to 3 there; `random_state=42` was pre-verified), **not** `clustering.py`. Changing label logic is out of scope; the task proves the existing pin.

- [ ] **Step 4: Mutation verification (proves the tests detect removed ordering)**

Temporarily change `_cluster_severity_order` (`clustering.py:64`) to return `{cluster_id: cluster_id for cluster_id in range(n_clusters)}` (identity — i.e., severity ordering removed). Run `pytest tests/test_clustering.py -v`. **Expected: both new tests FAIL** (seed 42 → Palawan cluster id 2 → "High"; adversarial → `severity_map[1] == 1`). Revert the mutation (never commit it), run again → all PASS. If either new test *passes* under the mutation, strengthen that test before proceeding.

- [ ] **Step 5: Commit**

```bash
git add ml/tests/test_clustering.py
git commit -m "test: pin cluster label mapping to cluster severity"
```

---

### Task 5: Documentation

**Files:**
- Modify: `docs/data-sources.md:12-21`
- Modify: `docs/testing-standards.md:94`
- Modify: `README.md:239-272` (narrative; command lines already done in Task 2)
- Modify: `docs/superpowers/specs/2026-08-27-kaggle-risk-profile-pipeline-design.md:95`
- Modify: `docs/superpowers/plans/2026-08-27-kaggle-risk-profile-pipeline.md:1175,1183-1184,1205,1270,1278`

- [ ] **Step 1: Update `docs/data-sources.md`**

In the Kaggle section add: downloads go through `kagglehub` (`dataset_download`), which resolves the **latest dataset version** on every run and extracts into `ml/data/raw/<slug>/` (force-replaced each run, so the local tree always matches the recorded version); the resolved **version number is written to each artifact's `metadata.json`** under `datasets[].version` (`null` when training `--offline` from local CSVs); credentials unchanged (`KAGGLE_USERNAME`/`KAGGLE_KEY` or `~/.kaggle/kaggle.json`).

- [ ] **Step 2: Update `docs/testing-standards.md:94`**

"tested with a fake API object" → "tested with a fake downloader".

- [ ] **Step 3: Update README narrative**

In the Regional Seismic Risk Profiles section: training **downloads the latest Kaggle data by default** (fresh monthly data requires no manual step); `--offline` / `-Offline` trains from local `ml/data/raw/` CSVs for reproducibility; `metadata.json` records the dataset version per dataset so runs months apart are distinguishable.

- [ ] **Step 4: Fix remaining `--download` / `-Download` hits in historical superpowers docs**

- `docs/superpowers/specs/2026-08-27-kaggle-risk-profile-pipeline-design.md:95`: `python -m ml.train --download --artifact-version v1` → `python -m ml.train --artifact-version v1` (default now downloads).
- `docs/superpowers/plans/2026-08-27-kaggle-risk-profile-pipeline.md`:
  - `:1205`, `:1278`: `.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download` → drop `-Download`.
  - `:1270`: `python -m ml.train --download --artifact-version credential-check` → drop `--download`.
  - `:1175,1183-1184`: PS-script snapshot → `[switch]$Offline` / `$Arguments += "--offline"`.
- Do **not** touch `download_datasets(...)` function-name or `download=True/False` kwarg references — those remain correct.

- [ ] **Step 5: Verify zero flag hits remain and run full verification**

Repo-wide grep for `--download`, `-Download`, `$Download` → **assert zero hits** (expected remaining matches: none; `download_datasets`/`download=` are out of pattern). CI (`.github/workflows/`) was already verified clean.
Run: `pytest -v` and `ruff check .` (from `ml/`), then from root: `python scripts\verify_structure.py`, `git diff --check`.

- [ ] **Step 6: Commit**

```bash
git add docs/data-sources.md docs/testing-standards.md README.md docs/superpowers/specs/2026-08-27-kaggle-risk-profile-pipeline-design.md docs/superpowers/plans/2026-08-27-kaggle-risk-profile-pipeline.md
git commit -m "docs: document kagglehub download behavior and offline flag"
```

---

## Self-review

- **Spec coverage:** user items 1-8 → Tasks 1-5 (1 verified pre-plan and recorded above; 2-3 Task 1; 4 Task 2; 5 Task 3; 6 Task 4; 7 Task 5; 8 Tasks 1/3). Item 9 (scheduled retraining) explicitly out of scope.
- **Type consistency:** `DownloadedDataset.version: int` (Task 1) consumed in Task 3; `downloader: Callable[[str, Path], tuple[str, int]]`; metadata key `"version": int | None` everywhere.
- **Mutation safety:** Task 4 Step 4 runs a deliberate mutation — must be reverted before the commit; never stage `clustering.py`.
- **Out of scope:** scheduled monthly retraining (GitHub Actions / cron wrapper around `train_risk_profile_models.ps1`) — separate task after this lands.
