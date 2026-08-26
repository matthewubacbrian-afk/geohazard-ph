# Kaggle Risk Profile Pipeline Design

## Goal

Update GeoHazard PH so its core analytical feature is a reproducible full training pipeline for Regional Seismic Risk Profiling in the Philippines using K-Means clustering and Random Forest classification. The pipeline must acquire real historical earthquake datasets from Kaggle, train models from those datasets, persist artifacts and metadata, and expose generated regional risk profiles through backend and web surfaces.

## Source Documents

This design implements the updated repository Markdown requirements from:

- `geohazard-project-overview.md`
- `geohazard-system-architecture.md`
- `geohazard-development-framework.md`
- `geohazard-file-tree.md`
- `docs/data-sources.md`

## Data Sources

The training corpus comes from two Kaggle datasets by `bwandowando`:

- `bwandowando/philippine-earthquakes-from-phivolcs`
- `bwandowando/philippine-earthquakes-1900-2025-from-usgs`

The second dataset URL still uses `1900-2025`, but Kaggle currently displays the title as `1900-2026`. The training pipeline must record the exact download timestamp, dataset slug, extracted filenames, and source license text in model metadata so the project is reproducible even if Kaggle updates the snapshots.

Live USGS feeds and PHIVOLCS scraping remain separate from this training pipeline. They feed monitoring and alerting; they do not retrain the model on request paths.

## Architecture

The implementation will keep ML training in a separate top-level `ml/` package. The backend API will not import scikit-learn or run training. It will read generated regional risk profile exports, and later the same service boundary can be swapped to PostGIS reads when migrations are added.

Pipeline flow:

1. Download both Kaggle datasets using Kaggle API credentials from `KAGGLE_USERNAME` and `KAGGLE_KEY`, or the standard Kaggle config file.
2. Extract CSV files into `ml/data/raw/`.
3. Normalize source-specific columns into a canonical earthquake event schema.
4. Merge PHIVOLCS and USGS historical records and deduplicate likely overlapping events.
5. Aggregate canonical events by region into seismic feature rows.
6. Scale numeric features and choose K for K-Means using silhouette score over a configured range.
7. Fit K-Means and map raw cluster IDs to stable ordered risk labels.
8. Train a Random Forest classifier using K-Means-derived labels.
9. Evaluate clustering and classification outputs.
10. Persist `.joblib` models, metadata, metrics, region feature exports, and risk profile JSON/CSV exports.
11. Serve exported risk profiles from backend endpoints.
12. Display regional risk profile summaries in the web dashboard.

## ML Package

`ml/src/ml/ingest_kaggle.py` will wrap Kaggle API download behavior. It must fail with a clear error if credentials are missing or if the Kaggle package is unavailable. It will not hide failed downloads behind sample data.

`ml/src/ml/clean_merge.py` will load CSVs and normalize flexible column names into these canonical fields:

- `source`
- `source_event_id`
- `region_name`
- `magnitude`
- `depth_km`
- `latitude`
- `longitude`
- `occurred_at`

Rows missing coordinates, magnitude, depth, or region name will be rejected with counts reported in training metadata. Deduplication will use source event IDs where present, otherwise a rounded time/location/magnitude key.

`ml/src/ml/features.py` will aggregate canonical events per region. Feature rows include:

- `region_name`
- `event_count`
- `mean_magnitude`
- `max_magnitude`
- `mean_depth_km`
- `event_density`
- `phivolcs_event_count`
- `usgs_event_count`

`event_density` will initially be a coordinate-spread density proxy based on the bounding box of observed epicenters for each region. This avoids pretending the project has authoritative administrative boundary polygons before those files exist. When boundary data is added, the function can switch to events per square kilometer.

`ml/src/ml/clustering.py` will fit K-Means with standardized numeric features. K will be chosen from a bounded range, defaulting to 3 through 5, using silhouette score when enough regions exist. For small fixture datasets, it will gracefully fall back to the largest valid K. Risk labels will be assigned by sorting cluster centroids by a severity score based on event count, mean magnitude, max magnitude, and event density. Raw K-Means cluster IDs will never be shown directly as risk category meaning.

`ml/src/ml/classifier.py` will train a Random Forest classifier on the feature table with K-Means-derived labels. It will expose prediction confidence and feature importances. The classifier is not an earthquake prediction model; it classifies historical regional risk profiles.

`ml/src/ml/evaluate.py` will compute silhouette score for clustering and accuracy, precision, recall, and a confusion matrix for the classifier when the dataset is large enough to split. For tiny datasets, it will report that full classifier metrics were skipped because the sample is too small.

`ml/src/ml/persist.py` will save and load artifacts:

- K-Means model
- scaler
- Random Forest model
- model metadata
- region features CSV
- risk profiles JSON

`ml/src/ml/train.py` will provide the CLI entrypoint:

```powershell
python -m ml.train --download --artifact-version v1
```

It will also support running from existing raw CSVs:

```powershell
python -m ml.train --artifact-version v1
```

## Backend Surface

The backend will add:

- `backend/app/schemas/risk_profile.py`
- `backend/app/services/risk_profile.py`
- `backend/app/api/v1/risk_profile.py`

Endpoints:

- `GET /api/v1/risk-profile/clusters`
- `GET /api/v1/risk-profile/{region_name}`

The service will read the generated risk profile JSON artifact path configured through settings, defaulting to a repository-local sample/export path suitable for tests. It will return region name, cluster, risk label, confidence, feature importances, model version, generated timestamp, and dataset snapshot summary.

## Web Surface

The web app will add typed risk profile support:

- `web/src/hooks/useRiskProfiles.ts`
- `web/src/components/risk/RiskProfileCard.tsx`
- `web/src/components/risk/RegionLookup.tsx`
- `web/src/pages/RiskProfileExplorer.tsx`

The first implementation will add this to the existing dashboard shell rather than introducing a full router. It will show region lookup, profile confidence, source snapshot metadata, and a clear note that the model is statistical risk profiling, not earthquake prediction.

## Configuration

New environment variables:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `RISK_PROFILE_ARTIFACT_DIR`
- `RISK_PROFILE_EXPORT_PATH`

`.env.example`, `README.md`, and `docs/data-sources.md` will document how to obtain Kaggle credentials and how the Kaggle datasets are used.

## Testing Strategy

Tests will be written before implementation changes.

ML tests will cover:

- Kaggle downloader argument construction and missing-credential failure.
- Canonical CSV normalization from PHIVOLCS-like and USGS-like headers.
- Deduplication of overlapping source records.
- Per-region feature aggregation.
- K selection and stable cluster-to-label mapping.
- Random Forest training output, confidence, and feature importances.
- Artifact metadata and exported risk profile shape.

Backend tests will cover:

- Risk profile summary counts.
- Cluster list endpoint.
- Single-region endpoint.
- Missing-region 404 response.

Web tests will cover:

- Risk profile card renders label, confidence, and top drivers.
- Region lookup filters profiles.

## Error Handling

Kaggle download failures must fail the training command clearly and nonzero. Missing credentials must explain both supported credential paths. Bad CSV rows must be counted and excluded rather than crashing the full run unless no usable rows remain. Training must fail if fewer than two usable regions are available, because clustering would be meaningless.

## Out of Scope

This pass will not add full PostGIS persistence for `region_seismic_features` or `region_risk_profiles`; the backend reads generated artifacts first. It will not build an earthquake forecasting system. It will not scrape historical PHIVOLCS bulletins for training, because the updated docs explicitly require Kaggle historical datasets for the training corpus.

## Acceptance Criteria

- Running the ML test suite passes.
- Running the backend risk-profile tests passes.
- Running the web tests for risk-profile components passes.
- With valid Kaggle credentials, the training command downloads both datasets, trains K-Means and Random Forest models, and writes artifacts plus metadata.
- Without Kaggle credentials, the training command fails with a clear credential setup message.
- Backend endpoints return generated risk profile exports.
- Documentation states that risk labels are descriptive statistical profiles, not earthquake predictions.
