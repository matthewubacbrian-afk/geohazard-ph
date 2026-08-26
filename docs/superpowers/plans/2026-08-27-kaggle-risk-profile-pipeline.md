# Kaggle Risk Profile Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full Kaggle-backed regional seismic risk profiling pipeline using K-Means clustering and Random Forest classification, then expose generated risk profiles through the backend and web app.

**Architecture:** The top-level `ml/` package owns download, cleaning, feature engineering, model training, evaluation, and artifact export. The backend reads exported JSON risk profiles and never trains models on request paths. The web app consumes the backend risk-profile endpoints and renders lookup/profile summaries inside the current dashboard shell.

**Tech Stack:** Python 3.11, pandas, scikit-learn, joblib, Kaggle API, pytest, FastAPI, Pydantic, React, TypeScript, Vitest.

---

## File Structure

- Create: `ml/pyproject.toml` - ML package metadata, dependencies, pytest pythonpath.
- Create: `ml/src/ml/__init__.py` - package marker and public version.
- Create: `ml/src/ml/ingest_kaggle.py` - Kaggle credential validation and dataset download.
- Create: `ml/src/ml/clean_merge.py` - CSV normalization, row validation, merge, and deduplication.
- Create: `ml/src/ml/features.py` - region feature dataclasses and aggregation.
- Create: `ml/src/ml/clustering.py` - K-Means feature matrix, K selection, stable risk labels.
- Create: `ml/src/ml/classifier.py` - Random Forest training, prediction confidence, feature importances.
- Create: `ml/src/ml/evaluate.py` - clustering/classifier metrics.
- Create: `ml/src/ml/persist.py` - artifact paths, JSON/CSV/model persistence.
- Create: `ml/src/ml/train.py` - end-to-end CLI.
- Modify: `ml/tests/test_features.py` - expand feature aggregation coverage.
- Modify: `ml/tests/test_clustering.py` - test K choice and stable labels.
- Modify: `ml/tests/test_classifier.py` - test Random Forest training outputs.
- Create: `ml/tests/test_ingest_kaggle.py` - missing credential and download call tests.
- Create: `ml/tests/test_clean_merge.py` - source normalization and dedup tests.
- Create: `ml/tests/test_persist.py` - metadata/export persistence tests.
- Create: `ml/tests/test_train.py` - CLI pipeline from local raw CSV fixtures.
- Create: `ml/tests/fixtures/phivolcs_sample.csv` - PHIVOLCS-like raw CSV fixture.
- Create: `ml/tests/fixtures/usgs_sample.csv` - USGS-like raw CSV fixture.
- Create: `backend/app/schemas/risk_profile.py` - API response models.
- Create: `backend/app/services/risk_profile.py` - artifact-backed profile reader and summary helper.
- Create: `backend/app/api/v1/risk_profile.py` - `/risk-profile` routes.
- Modify: `backend/app/main.py` - register risk profile router.
- Modify: `backend/app/config.py` - add risk profile export path setting.
- Modify: `backend/tests/unit/test_risk_profile_service.py` - cover artifact reading and missing regions.
- Modify: `backend/tests/integration/test_risk_profile_api.py` - cover list and detail endpoints.
- Create: `backend/tests/fixtures/risk_profiles.json` - backend fixture export.
- Modify: `web/src/types/hazard.ts` - add risk profile types.
- Modify: `web/src/api/client.ts` - add risk profile fetchers.
- Create: `web/src/hooks/useRiskProfiles.ts` - fetch profile list.
- Create: `web/src/components/risk/RiskProfileCard.tsx` - render label/confidence/drivers.
- Create: `web/src/components/risk/RegionLookup.tsx` - filter profiles by region.
- Create: `web/src/pages/RiskProfileExplorer.tsx` - dashboard panel for risk profiling.
- Modify: `web/src/pages/Dashboard.tsx` - include risk profile explorer.
- Create: `web/tests/RiskProfile.test.tsx` - Vitest component coverage.
- Modify: `.gitignore` - ignore downloaded Kaggle data and model artifacts.
- Modify: `.env.example` - document Kaggle and risk-profile artifact settings.
- Modify: `README.md` - add training command and Kaggle credential setup.
- Modify: `docs/data-sources.md` - document Kaggle dataset use, licenses, and attribution.
- Create: `scripts/train_risk_profile_models.ps1` - PowerShell wrapper around the ML CLI.

---

### Task 1: ML Package Skeleton and Existing Feature Test

**Files:**
- Create: `ml/pyproject.toml`
- Create: `ml/src/ml/__init__.py`
- Create: `ml/src/ml/features.py`
- Modify: `ml/tests/test_features.py`

- [ ] **Step 1: Write the failing feature tests**

Replace `ml/tests/test_features.py` with:

```python
from pathlib import Path

from ml.features import RegionFeatures, build_region_features, load_region_events


def test_build_region_features_aggregates_region_events():
    events = load_region_events(Path("tests/fixtures/sample_region_events.csv"))

    features = build_region_features(events)
    bicol = features["Bicol Region"]

    assert isinstance(bicol, RegionFeatures)
    assert bicol.event_count == 2
    assert bicol.mean_magnitude == 4.9
    assert bicol.max_magnitude == 5.1
    assert bicol.mean_depth_km == 27.5
    assert bicol.event_density > 0


def test_build_region_features_counts_sources_when_present():
    rows = [
        {
            "source": "phivolcs",
            "region_name": "Bicol Region",
            "magnitude": 5.0,
            "depth_km": 20.0,
            "latitude": 13.0,
            "longitude": 123.0,
        },
        {
            "source": "usgs",
            "region_name": "Bicol Region",
            "magnitude": 6.0,
            "depth_km": 30.0,
            "latitude": 13.2,
            "longitude": 123.2,
        },
    ]

    features = build_region_features(rows)["Bicol Region"]

    assert features.phivolcs_event_count == 1
    assert features.usgs_event_count == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run from repository root:

```powershell
Set-Location ml; pytest tests/test_features.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ml'`.

- [ ] **Step 3: Add the ML package skeleton**

Create `ml/pyproject.toml`:

```toml
[project]
name = "geohazard-ml"
version = "0.1.0"
description = "Regional seismic risk profiling pipeline for GeoHazard PH"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.2.0",
  "scikit-learn>=1.5.0",
  "joblib>=1.4.0",
  "kaggle>=1.6.17"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "ruff>=0.6.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

Create `ml/src/ml/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `ml/src/ml/features.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class RegionFeatures:
    region_name: str
    event_count: int
    mean_magnitude: float
    max_magnitude: float
    mean_depth_km: float
    event_density: float
    phivolcs_event_count: int = 0
    usgs_event_count: int = 0


def load_region_events(path: Path) -> list[dict[str, object]]:
    return pd.read_csv(path).to_dict(orient="records")


def build_region_features(events: Iterable[Mapping[str, object]]) -> dict[str, RegionFeatures]:
    frame = pd.DataFrame(events)
    if frame.empty:
        return {}

    required = {"region_name", "magnitude", "depth_km", "latitude", "longitude"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Region event rows are missing columns: {', '.join(sorted(missing))}")

    features: dict[str, RegionFeatures] = {}
    for region_name, group in frame.groupby("region_name"):
        lat_span = max(float(group["latitude"].max()) - float(group["latitude"].min()), 0.1)
        lon_span = max(float(group["longitude"].max()) - float(group["longitude"].min()), 0.1)
        density = round(float(len(group)) / (lat_span * lon_span), 6)
        source_counts = group.get("source", pd.Series([], dtype=str)).value_counts()
        features[str(region_name)] = RegionFeatures(
            region_name=str(region_name),
            event_count=int(len(group)),
            mean_magnitude=round(float(group["magnitude"].mean()), 2),
            max_magnitude=round(float(group["magnitude"].max()), 2),
            mean_depth_km=round(float(group["depth_km"].mean()), 2),
            event_density=density,
            phivolcs_event_count=int(source_counts.get("phivolcs", 0)),
            usgs_event_count=int(source_counts.get("usgs", 0)),
        )
    return features
```

- [ ] **Step 4: Run the test to verify it passes**

```powershell
Set-Location ml; pytest tests/test_features.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add ml/pyproject.toml ml/src/ml/__init__.py ml/src/ml/features.py ml/tests/test_features.py
git commit -m "feat: add regional feature aggregation"
```

---

### Task 2: Kaggle Download and CSV Normalization

**Files:**
- Create: `ml/src/ml/ingest_kaggle.py`
- Create: `ml/src/ml/clean_merge.py`
- Create: `ml/tests/test_ingest_kaggle.py`
- Create: `ml/tests/test_clean_merge.py`
- Create: `ml/tests/fixtures/phivolcs_sample.csv`
- Create: `ml/tests/fixtures/usgs_sample.csv`

- [ ] **Step 1: Write failing Kaggle ingestion and cleaning tests**

Create `ml/tests/test_ingest_kaggle.py`:

```python
import os
from pathlib import Path

import pytest

from ml.ingest_kaggle import KaggleDataset, KaggleCredentialError, download_datasets


def test_download_datasets_requires_credentials_when_config_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(KaggleCredentialError) as exc:
        download_datasets(tmp_path / "raw", datasets=[])

    assert "KAGGLE_USERNAME" in str(exc.value)
    assert "kaggle.json" in str(exc.value)


def test_download_datasets_calls_kaggle_api(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key")

    class FakeApi:
        def authenticate(self):
            calls.append(("authenticate", ""))

        def dataset_download_files(self, dataset, path, unzip):
            calls.append((dataset, str(path)))
            assert unzip is True

    datasets = [KaggleDataset("owner/example", "Example", "License")]

    downloaded = download_datasets(tmp_path / "raw", datasets=datasets, api=FakeApi())

    assert downloaded[0].slug == "owner/example"
    assert calls == [("authenticate", ""), ("owner/example", os.fspath(tmp_path / "raw" / "owner_example"))]
```

Create `ml/tests/fixtures/phivolcs_sample.csv`:

```csv
Date - Time (Philippine Time),Latitude,Longitude,Depth (km),Magnitude,Location
2024-01-01 08:00:00,13.40,123.30,34,5.1,Bicol Region
2024-01-02 09:30:00,13.80,123.70,21,4.7,Bicol Region
```

Create `ml/tests/fixtures/usgs_sample.csv`:

```csv
time,latitude,longitude,depth,mag,place,id
2024-01-01T00:00:00Z,13.40,123.30,34,5.1,Bicol Region,usgs-001
2024-02-03T11:00:00Z,11.00,125.00,42,6.2,Eastern Visayas,usgs-002
```

Create `ml/tests/test_clean_merge.py`:

```python
from pathlib import Path

from ml.clean_merge import load_and_merge_sources, normalize_csv


def test_normalize_csv_maps_phivolcs_headers():
    rows, report = normalize_csv(Path("tests/fixtures/phivolcs_sample.csv"), source="phivolcs")

    assert report.accepted_rows == 2
    assert report.rejected_rows == 0
    assert rows[0]["source"] == "phivolcs"
    assert rows[0]["region_name"] == "Bicol Region"
    assert rows[0]["magnitude"] == 5.1
    assert rows[0]["depth_km"] == 34.0


def test_normalize_csv_maps_usgs_headers():
    rows, report = normalize_csv(Path("tests/fixtures/usgs_sample.csv"), source="usgs")

    assert report.accepted_rows == 2
    assert rows[0]["source_event_id"] == "usgs-001"
    assert rows[1]["region_name"] == "Eastern Visayas"


def test_load_and_merge_sources_deduplicates_overlapping_events():
    rows, reports = load_and_merge_sources(
        phivolcs_paths=[Path("tests/fixtures/phivolcs_sample.csv")],
        usgs_paths=[Path("tests/fixtures/usgs_sample.csv")],
    )

    assert len(rows) == 3
    assert reports["phivolcs"].accepted_rows == 2
    assert reports["usgs"].accepted_rows == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
Set-Location ml; pytest tests/test_ingest_kaggle.py tests/test_clean_merge.py -v
```

Expected: FAIL because `ml.ingest_kaggle` and `ml.clean_merge` do not exist.

- [ ] **Step 3: Implement Kaggle ingestion and normalization**

Create `ml/src/ml/ingest_kaggle.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PHIVOLCS_DATASET = "bwandowando/philippine-earthquakes-from-phivolcs"
USGS_DATASET = "bwandowando/philippine-earthquakes-1900-2025-from-usgs"


class KaggleCredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class KaggleDataset:
    slug: str
    title: str
    license_name: str


@dataclass(frozen=True)
class DownloadedDataset:
    slug: str
    title: str
    license_name: str
    path: Path


DEFAULT_DATASETS = (
    KaggleDataset(PHIVOLCS_DATASET, "Philippine Earthquakes from PHIVOLCS", "CC0: Public Domain"),
    KaggleDataset(USGS_DATASET, "Philippine Earthquakes 1900-2026 from USGS", "Apache 2.0"),
)


def _has_credentials() -> bool:
    env_credentials = bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))
    config_file = Path.home() / ".kaggle" / "kaggle.json"
    return env_credentials or config_file.exists()


def _load_default_api():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise KaggleCredentialError("Install the kaggle package before downloading datasets.") from exc
    return KaggleApi()


def download_datasets(
    raw_dir: Path,
    datasets: tuple[KaggleDataset, ...] | list[KaggleDataset] = DEFAULT_DATASETS,
    api=None,
) -> list[DownloadedDataset]:
    if not _has_credentials():
        raise KaggleCredentialError(
            "Kaggle credentials are required. Set KAGGLE_USERNAME and KAGGLE_KEY, "
            "or create ~/.kaggle/kaggle.json."
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    kaggle_api = api or _load_default_api()
    kaggle_api.authenticate()

    downloaded: list[DownloadedDataset] = []
    for dataset in datasets:
        dataset_dir = raw_dir / dataset.slug.replace("/", "_")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        kaggle_api.dataset_download_files(dataset.slug, path=dataset_dir, unzip=True)
        downloaded.append(
            DownloadedDataset(dataset.slug, dataset.title, dataset.license_name, dataset_dir)
        )
    return downloaded
```

Create `ml/src/ml/clean_merge.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class SourceReport:
    source: str
    accepted_rows: int
    rejected_rows: int


ALIASES = {
    "source_event_id": ("id", "event_id", "source_event_id"),
    "region_name": ("region_name", "region", "province", "location", "place"),
    "magnitude": ("magnitude", "mag"),
    "depth_km": ("depth_km", "depth", "depth (km)"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng", "long"),
    "occurred_at": ("occurred_at", "time", "date - time (philippine time)", "date_time"),
}


def _canonical_columns(frame: pd.DataFrame) -> pd.DataFrame:
    lower_to_original = {column.strip().lower(): column for column in frame.columns}
    mapped: dict[str, pd.Series] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lower_to_original:
                mapped[canonical] = frame[lower_to_original[alias]]
                break
    return pd.DataFrame(mapped)


def _dedup_key(row: dict[str, object]) -> tuple[object, ...]:
    if row.get("source_event_id"):
        return (row["source"], row["source_event_id"])
    occurred = pd.to_datetime(row["occurred_at"], errors="coerce", utc=True)
    rounded_time = occurred.floor("h").isoformat() if not pd.isna(occurred) else ""
    return (
        rounded_time,
        round(float(row["latitude"]), 1),
        round(float(row["longitude"]), 1),
        round(float(row["magnitude"]), 1),
    )


def normalize_csv(path: Path, source: str) -> tuple[list[dict[str, object]], SourceReport]:
    raw = pd.read_csv(path)
    frame = _canonical_columns(raw)
    frame["source"] = source
    if "source_event_id" not in frame:
        frame["source_event_id"] = None

    required = ["region_name", "magnitude", "depth_km", "latitude", "longitude", "occurred_at"]
    for column in required:
        if column not in frame:
            frame[column] = pd.NA

    for column in ["magnitude", "depth_km", "latitude", "longitude"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["occurred_at"] = pd.to_datetime(frame["occurred_at"], errors="coerce", utc=True)
    frame["region_name"] = frame["region_name"].astype("string").str.strip()

    valid = frame.dropna(subset=required)
    rows = valid[
        ["source", "source_event_id", "region_name", "magnitude", "depth_km", "latitude", "longitude", "occurred_at"]
    ].to_dict(orient="records")
    report = SourceReport(source, accepted_rows=len(rows), rejected_rows=len(frame) - len(rows))
    return rows, report


def load_and_merge_sources(
    phivolcs_paths: Iterable[Path],
    usgs_paths: Iterable[Path],
) -> tuple[list[dict[str, object]], dict[str, SourceReport]]:
    all_rows: list[dict[str, object]] = []
    report_totals = {
        "phivolcs": SourceReport("phivolcs", 0, 0),
        "usgs": SourceReport("usgs", 0, 0),
    }

    for source, paths in (("phivolcs", phivolcs_paths), ("usgs", usgs_paths)):
        accepted = 0
        rejected = 0
        for path in paths:
            rows, report = normalize_csv(path, source)
            all_rows.extend(rows)
            accepted += report.accepted_rows
            rejected += report.rejected_rows
        report_totals[source] = SourceReport(source, accepted, rejected)

    seen: set[tuple[object, ...]] = set()
    merged: list[dict[str, object]] = []
    for row in all_rows:
        key = _dedup_key(row)
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged, report_totals
```

- [ ] **Step 4: Run tests to verify they pass**

```powershell
Set-Location ml; pytest tests/test_ingest_kaggle.py tests/test_clean_merge.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add ml/src/ml/ingest_kaggle.py ml/src/ml/clean_merge.py ml/tests/test_ingest_kaggle.py ml/tests/test_clean_merge.py ml/tests/fixtures/phivolcs_sample.csv ml/tests/fixtures/usgs_sample.csv
git commit -m "feat: add Kaggle source normalization"
```

---

### Task 3: K-Means Clustering and Random Forest Training

**Files:**
- Create: `ml/src/ml/clustering.py`
- Create: `ml/src/ml/classifier.py`
- Create: `ml/src/ml/evaluate.py`
- Modify: `ml/tests/test_clustering.py`
- Modify: `ml/tests/test_classifier.py`

- [ ] **Step 1: Write failing model tests**

Replace `ml/tests/test_clustering.py` with:

```python
from ml.clustering import assign_risk_labels, choose_k, fit_kmeans
from ml.features import RegionFeatures


def _rows():
    return [
        RegionFeatures("Palawan", 2, 3.4, 3.6, 22.0, 0.2),
        RegionFeatures("Bicol Region", 8, 4.9, 5.1, 27.5, 0.6),
        RegionFeatures("Eastern Visayas", 12, 6.0, 6.2, 39.5, 0.8),
        RegionFeatures("Davao Region", 10, 5.8, 6.0, 30.0, 0.7),
    ]


def test_assign_risk_labels_orders_clusters_by_severity():
    labels = assign_risk_labels(_rows())

    assert labels["Palawan"] == "Low"
    assert labels["Bicol Region"] in {"Moderate", "High"}
    assert labels["Eastern Visayas"] in {"High", "Very High"}


def test_choose_k_returns_valid_silhouette_choice():
    selected = choose_k(_rows(), k_values=[2, 3])

    assert selected.k in {2, 3}
    assert selected.silhouette_score > -1


def test_fit_kmeans_returns_region_assignments_and_model():
    result = fit_kmeans(_rows(), k_values=[2, 3], random_state=7)

    assert len(result.assignments) == 4
    assert result.model.n_clusters in {2, 3}
    assert result.scaler is not None
```

Replace `ml/tests/test_classifier.py` with:

```python
from ml.classifier import majority_label, train_random_forest
from ml.features import RegionFeatures


def test_majority_label_returns_most_common_label():
    assert majority_label(["High", "Low", "High", "Moderate"]) == "High"


def test_train_random_forest_returns_confidence_and_feature_importances():
    rows = [
        RegionFeatures("Palawan", 2, 3.4, 3.6, 22.0, 0.2),
        RegionFeatures("Bicol Region", 8, 4.9, 5.1, 27.5, 0.6),
        RegionFeatures("Eastern Visayas", 12, 6.0, 6.2, 39.5, 0.8),
        RegionFeatures("Davao Region", 10, 5.8, 6.0, 30.0, 0.7),
    ]
    labels = {
        "Palawan": "Low",
        "Bicol Region": "Moderate",
        "Eastern Visayas": "High",
        "Davao Region": "High",
    }

    result = train_random_forest(rows, labels, random_state=7)

    assert set(result.predictions) == set(labels)
    assert all(0.0 <= prediction.confidence <= 1.0 for prediction in result.predictions.values())
    assert "event_count" in result.feature_importances
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
Set-Location ml; pytest tests/test_clustering.py tests/test_classifier.py -v
```

Expected: FAIL because `choose_k`, `fit_kmeans`, and `train_random_forest` are missing.

- [ ] **Step 3: Implement clustering, classifier, and metrics**

Create `ml/src/ml/clustering.py`, `ml/src/ml/classifier.py`, and `ml/src/ml/evaluate.py` using these public functions:

```python
# clustering.py exports:
# FEATURE_COLUMNS = ["event_count", "mean_magnitude", "max_magnitude", "mean_depth_km", "event_density"]
# feature_matrix(rows) -> tuple[list[str], pandas.DataFrame]
# choose_k(rows, k_values=(3, 4, 5)) -> KSelection
# assign_risk_labels(rows) -> dict[str, str]
# fit_kmeans(rows, k_values=(3, 4, 5), random_state=42) -> KMeansResult
```

```python
# classifier.py exports:
# majority_label(labels) -> str
# train_random_forest(rows, labels, random_state=42) -> RandomForestResult
```

```python
# evaluate.py exports:
# evaluate_clustering(matrix, cluster_ids) -> dict[str, float | int]
# evaluate_classifier(labels, predictions) -> dict[str, object]
```

Implementation requirements:

- Use `StandardScaler` before K-Means.
- Skip invalid K values where `k < 2` or `k >= number_of_regions`.
- Use `KMeans(n_clusters=k, n_init=10, random_state=random_state)`.
- Sort cluster severity by centroid values for event count, magnitude, and density.
- Use `RandomForestClassifier(n_estimators=100, random_state=random_state, class_weight="balanced")`.
- Return dataclasses for model results so `persist.py` can save them.

- [ ] **Step 4: Run tests to verify they pass**

```powershell
Set-Location ml; pytest tests/test_clustering.py tests/test_classifier.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add ml/src/ml/clustering.py ml/src/ml/classifier.py ml/src/ml/evaluate.py ml/tests/test_clustering.py ml/tests/test_classifier.py
git commit -m "feat: train seismic risk models"
```

---

### Task 4: Artifact Persistence and Training CLI

**Files:**
- Create: `ml/src/ml/persist.py`
- Create: `ml/src/ml/train.py`
- Create: `ml/tests/test_persist.py`
- Create: `ml/tests/test_train.py`

- [ ] **Step 1: Write failing persistence and training tests**

Create `ml/tests/test_persist.py`:

```python
import json

from ml.persist import ArtifactBundle, save_risk_profiles


def test_save_risk_profiles_writes_json_export(tmp_path):
    bundle = ArtifactBundle.for_version(tmp_path, "v-test")
    profiles = [
        {
            "region_name": "Bicol Region",
            "cluster": 1,
            "label": "High",
            "confidence": 0.82,
            "feature_importances": {"event_count": 0.4},
            "model_version": "v-test",
        }
    ]

    save_risk_profiles(bundle, profiles)

    saved = json.loads(bundle.risk_profiles_json.read_text(encoding="utf-8"))
    assert saved[0]["region_name"] == "Bicol Region"
```

Create `ml/tests/test_train.py`:

```python
import json
from pathlib import Path

from ml.train import run_training


def test_run_training_from_existing_csvs_writes_artifacts(tmp_path):
    result = run_training(
        phivolcs_paths=[Path("tests/fixtures/phivolcs_sample.csv")],
        usgs_paths=[Path("tests/fixtures/usgs_sample.csv")],
        artifact_dir=tmp_path,
        artifact_version="v-test",
        download=False,
        k_values=[2],
        random_state=7,
    )

    assert result.profile_count == 2
    metadata = json.loads((tmp_path / "v-test" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["model_version"] == "v-test"
    assert metadata["datasets"][0]["slug"] == "bwandowando/philippine-earthquakes-from-phivolcs"
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
Set-Location ml; pytest tests/test_persist.py tests/test_train.py -v
```

Expected: FAIL because `ml.persist` and `ml.train` do not exist.

- [ ] **Step 3: Implement persistence and CLI orchestration**

Create `ml/src/ml/persist.py` with:

```python
# ArtifactBundle.for_version(root: Path, version: str)
# save_json(path: Path, payload: object)
# save_risk_profiles(bundle: ArtifactBundle, profiles: list[dict[str, object]])
# save_metadata(bundle: ArtifactBundle, metadata: dict[str, object])
# save_models(bundle: ArtifactBundle, kmeans_result, rf_result)
```

Create `ml/src/ml/train.py` with:

```python
# run_training(phivolcs_paths, usgs_paths, artifact_dir, artifact_version, download, k_values, random_state)
# main(argv=None) -> int
```

Implementation requirements:

- If `download=True`, call `download_datasets(Path("data/raw"))` and discover `*.csv` under the returned directories.
- If `download=False`, use the passed CSV paths or discover raw CSVs under `ml/data/raw`.
- Fail with `ValueError("At least two usable regions are required for clustering.")` if feature count is under two.
- Write `metadata.json`, `risk_profiles.json`, `region_features.csv`, `kmeans_model.joblib`, `scaler.joblib`, and `random_forest_model.joblib`.
- Include dataset slugs and license names from `DEFAULT_DATASETS` in metadata.
- Return a dataclass with `profile_count`, `artifact_dir`, and `model_version`.

- [ ] **Step 4: Run tests to verify they pass**

```powershell
Set-Location ml; pytest tests/test_persist.py tests/test_train.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add ml/src/ml/persist.py ml/src/ml/train.py ml/tests/test_persist.py ml/tests/test_train.py
git commit -m "feat: persist risk profile training artifacts"
```

---

### Task 5: Backend Risk Profile API

**Files:**
- Create: `backend/app/schemas/risk_profile.py`
- Create: `backend/app/services/risk_profile.py`
- Create: `backend/app/api/v1/risk_profile.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/unit/test_risk_profile_service.py`
- Modify: `backend/tests/integration/test_risk_profile_api.py`
- Create: `backend/tests/fixtures/risk_profiles.json`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/fixtures/risk_profiles.json`:

```json
[
  {
    "region_name": "Bicol Region",
    "cluster": 2,
    "label": "High",
    "confidence": 0.82,
    "feature_importances": {"event_count": 0.42, "max_magnitude": 0.31},
    "model_version": "v-test",
    "generated_at": "2026-08-27T00:00:00Z",
    "dataset_snapshot": "Kaggle PHIVOLCS and USGS fixture"
  },
  {
    "region_name": "Palawan",
    "cluster": 0,
    "label": "Low",
    "confidence": 0.91,
    "feature_importances": {"event_count": 0.39, "mean_magnitude": 0.22},
    "model_version": "v-test",
    "generated_at": "2026-08-27T00:00:00Z",
    "dataset_snapshot": "Kaggle PHIVOLCS and USGS fixture"
  }
]
```

Replace `backend/tests/unit/test_risk_profile_service.py` with:

```python
from pathlib import Path

import pytest

from app.schemas.risk_profile import RiskProfile
from app.services.risk_profile import RiskProfileNotFound, get_profile, load_profiles, summarize_profiles


FIXTURE = Path("tests/fixtures/risk_profiles.json")


def test_summarize_profiles_counts_labels():
    profiles = [
        RiskProfile(region_name="Bicol Region", cluster=2, label="High", confidence=0.82),
        RiskProfile(region_name="Eastern Visayas", cluster=2, label="High", confidence=0.79),
        RiskProfile(region_name="Palawan", cluster=0, label="Low", confidence=0.91),
    ]

    assert summarize_profiles(profiles) == {"High": 2, "Low": 1}


def test_load_profiles_reads_generated_artifact():
    profiles = load_profiles(FIXTURE)

    assert profiles[0].region_name == "Bicol Region"
    assert profiles[0].feature_importances["event_count"] == 0.42


def test_get_profile_is_case_insensitive():
    profile = get_profile("bicol region", load_profiles(FIXTURE))

    assert profile.label == "High"


def test_get_profile_raises_for_missing_region():
    with pytest.raises(RiskProfileNotFound):
        get_profile("Unknown Region", load_profiles(FIXTURE))
```

Replace `backend/tests/integration/test_risk_profile_api.py` with:

```python
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_risk_profile_clusters_endpoint_returns_profiles(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/clusters")

    assert response.status_code == 200
    assert response.json()[0]["region_name"] == "Bicol Region"


def test_risk_profile_detail_endpoint_returns_region(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/Bicol%20Region")

    assert response.status_code == 200
    assert response.json()["label"] == "High"


def test_risk_profile_detail_endpoint_returns_404(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/Unknown")

    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
Set-Location backend; pytest tests/unit/test_risk_profile_service.py tests/integration/test_risk_profile_api.py -v
```

Expected: FAIL because risk-profile schema, service, and router are missing.

- [ ] **Step 3: Implement backend API**

Create the schema with `RiskProfile` and optional `RiskProfileSummary` Pydantic models. Create the service with `load_profiles(path)`, `get_profile(region_name, profiles)`, `summarize_profiles(profiles)`, and `RiskProfileNotFound`. Create the router:

```python
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.services.risk_profile import RiskProfileNotFound, get_profile, load_profiles

router = APIRouter(prefix="/risk-profile", tags=["risk-profile"])


@router.get("/clusters")
def list_risk_profiles():
    return load_profiles(get_settings().risk_profile_export_path)


@router.get("/{region_name}")
def retrieve_risk_profile(region_name: str):
    profiles = load_profiles(get_settings().risk_profile_export_path)
    try:
        return get_profile(region_name, profiles)
    except RiskProfileNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
```

Modify `backend/app/config.py` to add:

```python
from pathlib import Path

risk_profile_export_path: Path = Path("tests/fixtures/risk_profiles.json")
```

Modify `backend/app/main.py` to import and include `risk_profile.router`.

- [ ] **Step 4: Run tests to verify they pass**

```powershell
Set-Location backend; pytest tests/unit/test_risk_profile_service.py tests/integration/test_risk_profile_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/schemas/risk_profile.py backend/app/services/risk_profile.py backend/app/api/v1/risk_profile.py backend/app/config.py backend/app/main.py backend/tests/unit/test_risk_profile_service.py backend/tests/integration/test_risk_profile_api.py backend/tests/fixtures/risk_profiles.json
git commit -m "feat: expose regional risk profiles"
```

---

### Task 6: Web Risk Profile Explorer

**Files:**
- Modify: `web/src/types/hazard.ts`
- Modify: `web/src/api/client.ts`
- Create: `web/src/hooks/useRiskProfiles.ts`
- Create: `web/src/components/risk/RiskProfileCard.tsx`
- Create: `web/src/components/risk/RegionLookup.tsx`
- Create: `web/src/pages/RiskProfileExplorer.tsx`
- Modify: `web/src/pages/Dashboard.tsx`
- Create: `web/tests/RiskProfile.test.tsx`

- [ ] **Step 1: Write failing web component tests**

Create `web/tests/RiskProfile.test.tsx`:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import RiskProfileCard from '../src/components/risk/RiskProfileCard';
import RegionLookup from '../src/components/risk/RegionLookup';
import type { RiskProfile } from '../src/types/hazard';

const profiles: RiskProfile[] = [
  {
    region_name: 'Bicol Region',
    cluster: 2,
    label: 'High',
    confidence: 0.82,
    feature_importances: { event_count: 0.42, max_magnitude: 0.31 },
    model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z',
    dataset_snapshot: 'Kaggle fixture',
  },
  {
    region_name: 'Palawan',
    cluster: 0,
    label: 'Low',
    confidence: 0.91,
    feature_importances: { event_count: 0.39 },
    model_version: 'v-test',
    generated_at: '2026-08-27T00:00:00Z',
    dataset_snapshot: 'Kaggle fixture',
  },
];

describe('Risk profile components', () => {
  it('renders risk label confidence and feature drivers', () => {
    const html = renderToStaticMarkup(<RiskProfileCard profile={profiles[0]} />);

    expect(html).toContain('Bicol Region');
    expect(html).toContain('High');
    expect(html).toContain('82%');
    expect(html).toContain('event_count');
  });

  it('filters region lookup by query', () => {
    const html = renderToStaticMarkup(<RegionLookup profiles={profiles} query="pal" />);

    expect(html).toContain('Palawan');
    expect(html).not.toContain('Bicol Region');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
Set-Location web; npm test -- RiskProfile.test.tsx
```

Expected: FAIL because risk components and types do not exist.

- [ ] **Step 3: Implement web risk profile components**

Add `RiskProfile` type to `web/src/types/hazard.ts`. Add `fetchRiskProfiles()` and `fetchRiskProfile(regionName)` to `web/src/api/client.ts`. Create `useRiskProfiles.ts` with TanStack Query. Create the components so they render:

- region name
- risk label
- confidence as a percentage
- top feature drivers sorted descending
- model version and dataset snapshot
- a visible statement that the label is statistical profiling, not prediction

Modify `Dashboard.tsx` to render `<RiskProfileExplorer />` alongside the existing event/map panels.

- [ ] **Step 4: Run test to verify it passes**

```powershell
Set-Location web; npm test -- RiskProfile.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Run web build**

```powershell
Set-Location web; npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add web/src/types/hazard.ts web/src/api/client.ts web/src/hooks/useRiskProfiles.ts web/src/components/risk/RiskProfileCard.tsx web/src/components/risk/RegionLookup.tsx web/src/pages/RiskProfileExplorer.tsx web/src/pages/Dashboard.tsx web/tests/RiskProfile.test.tsx
git commit -m "feat: add risk profile explorer"
```

---

### Task 7: Configuration, Documentation, and Training Wrapper

**Files:**
- Modify: `.gitignore`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/data-sources.md`
- Create: `scripts/train_risk_profile_models.ps1`

- [ ] **Step 1: Write failing structure/config test**

Modify `scripts/verify_structure.py` to require:

```python
"ml/pyproject.toml",
"ml/src/ml/train.py",
"ml/src/ml/ingest_kaggle.py",
"backend/app/api/v1/risk_profile.py",
"web/src/pages/RiskProfileExplorer.tsx",
"scripts/train_risk_profile_models.ps1",
```

Run:

```powershell
python scripts/verify_structure.py
```

Expected: FAIL until the wrapper and docs/config changes are complete.

- [ ] **Step 2: Update gitignore and env example**

Add to `.gitignore`:

```gitignore
ml/data/raw/
ml/data/processed/
ml/model_artifacts/
!ml/data/raw/.gitkeep
!ml/data/processed/.gitkeep
!ml/model_artifacts/.gitkeep
```

Add to `.env.example`:

```env
KAGGLE_USERNAME=
KAGGLE_KEY=
RISK_PROFILE_ARTIFACT_DIR=ml/model_artifacts
RISK_PROFILE_EXPORT_PATH=backend/tests/fixtures/risk_profiles.json
```

- [ ] **Step 3: Add training wrapper**

Create `scripts/train_risk_profile_models.ps1`:

```powershell
param(
  [string]$ArtifactVersion = "v1",
  [switch]$Download
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $RepoRoot "ml")

$Arguments = @("-m", "ml.train", "--artifact-version", $ArtifactVersion)
if ($Download) {
  $Arguments += "--download"
}

python @Arguments
```

- [ ] **Step 4: Update documentation**

Update `README.md` with:

```markdown
## Regional Seismic Risk Profiling

The ML module trains K-Means clusters and a Random Forest classifier from two Kaggle historical earthquake datasets:

- `bwandowando/philippine-earthquakes-from-phivolcs`
- `bwandowando/philippine-earthquakes-1900-2025-from-usgs`

Set `KAGGLE_USERNAME` and `KAGGLE_KEY`, then run:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
```

The generated risk labels are descriptive statistical profiles based on historical records. They are not earthquake predictions.
```

Update `docs/data-sources.md` with the two Kaggle slugs, observed licenses, access method, and attribution note.

- [ ] **Step 5: Run structure verification**

```powershell
python scripts/verify_structure.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add .gitignore .env.example README.md docs/data-sources.md scripts/train_risk_profile_models.ps1 scripts/verify_structure.py
git commit -m "docs: document Kaggle risk profile training"
```

---

### Task 8: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run all ML tests**

```powershell
Set-Location ml; pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run backend tests**

```powershell
Set-Location backend; pytest -v
```

Expected: PASS.

- [ ] **Step 3: Run web tests**

```powershell
Set-Location web; npm test
```

Expected: PASS.

- [ ] **Step 4: Run web build**

```powershell
Set-Location web; npm run build
```

Expected: PASS.

- [ ] **Step 5: Run training without credentials and confirm useful failure**

```powershell
Set-Location ml; python -m ml.train --download --artifact-version credential-check
```

Expected without Kaggle credentials: nonzero exit and a message mentioning `KAGGLE_USERNAME`, `KAGGLE_KEY`, and `kaggle.json`.

- [ ] **Step 6: Run real Kaggle training when credentials are present**

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
```

Expected with Kaggle credentials: downloads both datasets, writes `ml/model_artifacts/v1/metadata.json`, `risk_profiles.json`, `region_features.csv`, `kmeans_model.joblib`, `scaler.joblib`, and `random_forest_model.joblib`.

- [ ] **Step 7: Inspect git status**

```powershell
git status --short
```

Expected: only intentionally untracked large data/model artifacts are ignored; source, tests, docs, and config changes are committed.
