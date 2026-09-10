# Glossary

**Project**: GeoHazard PH
**Scope**: Canonical domain vocabulary and field names across docs, specs, and code. Read this when naming anything domain-related — models, fields, functions, endpoints.

One rule governs everything else: terms map 1:1 between code and docs. If a term appears in a spec, the same name appears in the schema, the model, the API response, and the frontend type. When you need a new concept, add it here first.

Related contracts:
- `docs/api-contracts.md` — wire-format field naming (snake_case everywhere).
- `CODE` definitions: `backend/app/schemas/hazard_event.py`, `backend/app/schemas/risk_profile.py`, `backend/app/models/hazard_event.py`.

---

## Table Of Contents

1. Field-Naming Rule
2. Hazard Data Concepts
3. Risk Profiling Concepts
4. Ingestion And Sources
5. Pipeline And Artifacts
6. Platform Concepts

---

## 1. Field-Naming Rule

- Wire format and backend/ML code: `snake_case` (`occurred_at`, `region_name`, `feature_importances`) with no exceptions.
- Web types mirror the wire format field-for-field (`web/src/types/hazard.ts`).
- Mobile UI-native types may use camelCase only behind an explicit mapping layer in `mobile/src/services/api.ts` that converts to and from the wire format; the mapping is unit tested.
- Acronyms in identifiers keep their casing when they are established names: `USGS`, `GVP`, `PHIVOLCS`, `API`, `ML`, `CI`.
- Constraint/index names follow `uq_<table>_<columns>` / `idx_<table>_<column>` / `ck_<table>_<column>`.

## 2. Hazard Data Concepts

| Term | Canonical field/source | Meaning |
| --- | --- | --- |
| hazard event | `HazardEvent` (schema/model), endpoint `/events` | One observed geohazard occurrence (earthquake, volcanic, landslide). |
| hazard_type | `hazard_type` | Closed set: `earthquake`, `volcanic`, `landslide`. |
| source | `source` | The provider that reported the event: `usgs`, `phivolcs`, `gvp`. Used with `external_id` for deduplication. |
| external_id | `external_id` | The source's own identifier for the event. Never invented by GeoHazard; `None` when the source has none. |
| source_event_id | `source_event_id` (ML canonical schema) | ML-pipeline alias for `external_id` after normalization. |
| place_name | `place_name` | Human-readable location string as reported (e.g. `"12 km E of Sample, Philippines"`). |
| occurred_at | `occurred_at` | When the event happened, ISO 8601 with timezone. |
| alert_level | `alert_level` | Official advisory level when the source publishes one; nullable, never inferred from magnitude. |
| magnitude | `magnitude` | Reported magnitude; nullable. |
| depth_km | `depth_km` | Depth in kilometers; nullable. |
| latitude / longitude | `latitude`, `longitude` | Decimal degrees, North/East positive. GeoJSON coordinates arrays are `[longitude, latitude]`. |
| location | `location` (model column) | PostGIS `Geography(Point, 4326)` kept in sync with `latitude`/`longitude` for spatial queries. |
| raw_payload | `raw_payload` | The original source payload for the record, preserved for auditability. |
| canonical_id | `canonical_id` | Shared identity UUID linking source rows that represent the same observed event. |
| is_primary | `is_primary` | Display-authority flag; exactly one row in a canonical group should be primary. |
| match_confidence | `match_confidence` | Numeric confidence assigned when cross-source rows are canonicalized. |
| EventChange | `EventChange` | Post-commit event-change payload used by realtime consumers. |
| match_and_link | `match_and_link` | Synchronous ingest operation that matches cross-source rows into canonical groups. |
| event density | `event_density` | Coordinate-spread density proxy; not events per km² until authoritative boundaries exist. |

## 3. Risk Profiling Concepts

Risk labels are descriptive statistical profiles of historical records. They are never forecasts or predictions (see `CODING_STANDARDS.md`).

| Term | Canonical field | Meaning |
| --- | --- | --- |
| risk profile | `RiskProfile`, endpoint `/risk-profile` | Per-region summary produced by the ML pipeline. |
| region_name | `region_name` | Philippine region name; the profile's key. Case-insensitive on lookup. |
| cluster | `cluster` | Raw K-Means cluster index. Never shown to users as a risk meaning by itself. |
| risk label | `label` | Ordered, human-meaningful category derived from cluster severity: `Low`, `Moderate`, `High`, `Very High`. |
| confidence | `confidence` | Classifier confidence for the label, float in `[0, 1]`. |
| feature_importances | `feature_importances` | Random Forest feature importances by feature name (e.g. `event_count`, `max_magnitude`). |
| model_version | `model_version` | Artifact version string that produced the profile (e.g. `v1`). |
| generated_at | `generated_at` | When the profile artifact was generated, ISO 8601. |
| dataset_snapshot | `dataset_snapshot` | Human summary of the source datasets and snapshot captured for reproducibility. |
| event_count | `event_count` | Number of canonical events aggregated for the region. |

## 4. Ingestion And Sources

| Term | Meaning |
| --- | --- |
| adapter | One module per external source under `backend/ingestion/sources/` (`usgs.py`, `phivolcs_earthquake.py`, `gvp.py`). Adapters are unreliable I/O boundaries. |
| ingest | Fetch, parse, deduplicate, and upsert records into the database. |
| dedup_key | A tuple identifying a canonical event: `(source, external_id)`; falls back to a content key derived from `occurred_at` + lat + lon + magnitude when `external_id` is absent. |
| upsert | Insert new rows; update existing rows matched on the dedup key. |
| canonical event schema | The ML-pipeline field set after normalization: `source`, `source_event_id`, `region_name`, `magnitude`, `depth_km`, `latitude`, `longitude`, `occurred_at`. |
| bbox | `ph_bbox` setting, tuple `(west, south, east, north)`, default `(116.0, 4.0, 128.0, 22.0)`, approximating the Philippines. |
| PHIVOLCS / USGS / GVP | Providers: Philippine Institute of Volcanology and Seismology; US Geological Survey; Smithsonian Global Volcanism Program. |

## 5. Pipeline And Artifacts

| Term | Meaning |
| --- | --- |
| training pipeline | `ml/src/ml/*` — ingest, clean/merge, feature-build, cluster, classify, evaluate, persist. The backend never trains models on request paths. |
| artifact bundle | `ArtifactBundle.for_version(root, version)` — versioned output set under `ml/model_artifacts/<version>/`: `metadata.json`, `risk_profiles.json`, `region_features.csv`, `kmeans_model.joblib`, `scaler.joblib`, `random_forest_model.joblib`. |
| metadata | `metadata.json` — artifact version, dataset slugs and licenses, download timestamps, row counts, feature names. Required for reproducibility. |
| event density | See Hazard Data Concepts. |
| K selection | Choosing `k` for K-Means via silhouette score over a bounded range, default 3–5. |

## 6. Platform Concepts

| Term | Meaning |
| --- | --- |
| events summary | `EventSummary`, endpoint `/events/summary` — region/bounding-box rollup: `event_count`, `avg_magnitude`, `max_magnitude`, `latest_occurred_at`. |
| offline cache | `mobile/src/services/offlineCache.ts` — in-memory (currently) key-value store for mobile reads without network. |
| risk profile explorer | `web/src/pages/RiskProfileExplorer.tsx` — dashboard panel for region lookup and profile cards. |
| realtime alerts | Planned push channel; sources are not wired yet (`mobile/src/services/pushNotifications.ts` reports `not-configured`). |
| static layers | Imported fault and volcano reference vectors (Epic 3); landslide and InSAR remain stretch work. |

---

## Adding a term

When a spec or plan introduces a new concept:

1. Add the term here with the exact field/type name it will use.
2. Use that name in the schema/model/type from the first commit.
3. Reference the glossary in the spec (`Related documents`).
## Epic 2 realtime and volcano feed

| Term | Canonical field / meaning |
| --- | --- |
| EventChange | Committed source-row push schema in `app/schemas/event_change.py`; ADR 0002 defines its fields. |
| canonical_id / is_primary | Resolved earthquake group UUID / display-primary flag, assigned inside Person A's ingest transaction. Neither the publisher nor the browser invents these values. |
| events publisher | `app/services/events_publisher.py::publish`, the best-effort `on_committed` callback publishing individual JSON messages to Redis `events:updates`. |
| realtime connection | Browser connection to `/ws/events`; LIVE indicates transport connectivity, not ingest-worker health or an official warning. |
| current_alert_level | PHIVOLCS-published volcano alert integer 0–5; zero is a valid reported level, never a default for missing data. |
| source_url / bulletin_url | Official listing URL / latest linked English bulletin URL. |
| bulletin_at | Observation timestamp printed in the listing's English bulletin heading, converted from Asia/Manila to UTC; not the time the alert level changed. |
| retrieved_at | UTC time of a successful source fetch, retained when serving cached results. |
| stale | Cached volcano data returned after a failed refresh; bounded by the configured maximum cache age. |

## Epic 3 static reference layers

- `FaultLine`: imported LineString/MultiLineString, served by `/faults`.
- `VolcanoZone`: imported Polygon/MultiPolygon, served by `/volcano-zones`.
- `external_id`: source feature identifier; content SHA-256 when no identifier exists.
- `geometry`: validated WGS84 GeoJSON, coordinates `[longitude, latitude]`.
- `source_url`, `license_name`, `dataset_version`: required import provenance.
- `imported_at`: UTC import timestamp; not a source observation time.
- `source_properties`: original source attributes retained without renaming.
- PHIVOLCS volcano overlays: source-rendered base-surge, lava, pyroclastic-density-current
  and lahar reference images used when local `VolcanoZone` vectors are absent.
  These are remotely rendered hazard maps, not imported polygons or live alert levels.
