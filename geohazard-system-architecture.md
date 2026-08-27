# GeoHazard PH — System Architecture & Tech Stack
*A Project NOAH–inspired multi-hazard monitoring platform (Earthquake · Landslide · Volcanic Activity · Active Faults / Ground Movement), extended with a Regional Seismic Risk Profiling module (K-Means Clustering + Random Forest Classification)*

---

## 1. What Project NOAH actually did (for reference)

Project NOAH (DOST, 2012–2017, now continued as UP NOAH) was built around three layers:
1. **Data ingestion** — sensors (rain gauges, water-level sensors), satellite imagery, weather models
2. **Hazard modeling/processing** — flood simulation models, hazard map generation (GIS)
3. **Public-facing delivery** — web GIS dashboard + early-warning bulletins

You're adapting this pattern to **seismic, volcanic, and mass-movement hazards**, using only **public APIs** (no private sensor network) — which is very feasible since USGS, PHIVOLCS, and Smithsonian all publish usable public data.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (public)                     │
│  USGS Earthquake API · EMSC · PHIVOLCS bulletins (scraped) ·     │
│  Smithsonian GVP (volcanoes) · PHIVOLCS Fault Atlas / GEM faults │
│  · Copernicus Sentinel-1 InSAR (ground deformation)              │
└───────────────────────────┬───────────────────────────────────────┘
                             │ scheduled pull / webhook / scrape
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION & ETL LAYER                        │
│   Scheduled workers (cron/queue) → normalize → validate →        │
│   deduplicate → write to DB. Alerts trigger events.              │
└───────────────────────────┬───────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE DATA STORE                                │
│   PostgreSQL + PostGIS (spatial data: faults, hazard zones,      │
│   events) + Redis (cache / pub-sub for real-time alerts)         │
└───────────────────────────┬───────────────────────────────────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────────────┐  ┌─────────────────────────────────┐
│  ANALYTICS / ML LAYER          │  │   APPLICATION / API LAYER        │
│  (offline/batch, not request-  │  │   REST + WebSocket API           │
│  serving)                      │  │   (Node/NestJS or Python/FastAPI)│
│  - Historical data prep from   │  │   - /events, /hazards/:type,     │
│    Kaggle PHIVOLCS + USGS      │  │     /faults, /alerts, /subscribe │
│    (1900–2025) datasets        │  │   - /risk-profile/:region,       │
│  - K-Means clustering →        │  │     /risk-profile/clusters       │
│    regional risk clusters      │◄─┤     (reads model output stored   │
│  - Random Forest classifier    │  │     back in PostGIS)             │
│    trained on cluster labels   │  │                                  │
│  - Model artifacts (joblib)    │  │                                  │
└───────────────┬─────────────────┘  └──────────────┬─────────────────────┘
                │ writes region risk labels back to DB                │
                └──────────────────────────┬─────────────────────────┘
                                            ▼
                             ┌──────────────┴───────────────┐
                             ▼                               ▼
                    ┌─────────────────┐          ┌──────────────────────┐
                    │   WEB DASHBOARD   │          │   MOBILE APP           │
                    │   React + MapLibre│          │   React Native/Flutter │
                    │   /Leaflet GIS map │          │   + push notifications │
                    │   + risk profile   │          │   + risk profile view  │
                    │     layer          │          │                        │
                    └─────────────────┘          └──────────────────────┘
```

**Why the ML layer is separate from the API layer:** clustering and classifier training are **batch/offline jobs** (run once initially, then re-run periodically as historical datasets are refreshed), not something computed per-request. The API layer only ever *reads* the resulting risk labels/cluster assignments that the ML layer has already written back into PostGIS — it never trains or re-clusters on a live request path.

---

## 3. Recommended Tech Stack

### Data ingestion / backend workers
- **Language:** Python (best ecosystem for geospatial + scientific data: `geopandas`, `shapely`, `rasterio`)
- **Scheduler:** Celery + Redis, or simpler: cron + a queue (BullMQ if you go Node) — start simple with cron jobs, graduate to a queue once you have >5 data sources
- **Scraping (for PHIVOLCS, which has no formal API):** `requests` + `BeautifulSoup`, or Playwright if their bulletin pages are JS-rendered. Cache raw HTML so you can re-parse without re-hitting their site.

### Core API layer
Pick one:
- **FastAPI (Python)** — great if your ingestion layer is also Python; you can share models/validation code (Pydantic) across ingestion and API.
- **NestJS (Node/TypeScript)** — great if your frontend/mobile team is JS-heavy and you want one language end-to-end.

Either way, expose:
- REST endpoints for hazard queries (`GET /events?type=earthquake&since=...`)
- WebSocket or Server-Sent Events channel for real-time push (new earthquake detected, volcano alert level change)
- REST endpoints for the risk-profiling module, which only ever **read** what the ML layer has already computed and stored (`GET /risk-profile/:region`, `GET /risk-profile/clusters`) — no on-request training or inference happens here

### Database
- **PostgreSQL + PostGIS extension** — this is the single most important choice. PostGIS gives you spatial queries out of the box: "find all events within 20km of this fault," "which barangays intersect this landslide-susceptibility polygon," etc.
- **Redis** — cache hot queries (e.g., "latest 50 earthquakes") and act as pub/sub broker for push notifications.
- **Object storage (S3-compatible, e.g., Cloudflare R2 or Backblaze B2 — cheaper than AWS S3):** for hazard map tiles, satellite imagery snapshots, PDF bulletins.

### GIS / mapping
- **MapLibre GL JS** (open-source fork of Mapbox GL, no vendor lock-in) or **Leaflet** if you want something lighter and simpler
- **Tile serving:** if you generate your own hazard-zone tiles, use `tippecanoe` to build vector tiles, served via a lightweight tile server (`martin`, written in Rust, serves PostGIS tables directly as vector tiles — very good fit here)
- **Geospatial processing:** `GDAL`, `geopandas`, `shapely`, `rasterio` for handling shapefiles (PHIVOLCS fault atlases, GEM fault database) and satellite raster data

### Web frontend
- **React + TypeScript**, **Vite** for build tooling
- **MapLibre GL JS** for the map
- **TanStack Query** for data fetching/caching against your API
- **Tailwind CSS** for styling

### Mobile app
- **React Native** (if you want to share code/patterns with the React web app) or **Flutter** (if you want a more native feel and don't mind a separate codebase)
- Push notifications: **Firebase Cloud Messaging** (free tier is generous, cross-platform)
- Offline-first consideration: cache last-known hazard data locally (important for disaster scenarios where connectivity drops) — `WatermelonDB` or simple `SQLite` on-device

### Analytics / ML (Regional Seismic Risk Profiling)
- **Language:** Python — same runtime as the ingestion layer, so historical data prep can reuse existing parsing/normalization code
- **Data prep:** `pandas` for aggregation (per-region feature engineering: event count, mean/max magnitude, mean depth, spatial density), `geopandas` for joining raw lat/lon points to province/region boundaries
- **Clustering:** `scikit-learn`'s `KMeans` — used unsupervised on the regional feature table to derive risk clusters; `k` chosen via elbow method / silhouette score, not hardcoded
- **Classification:** `scikit-learn`'s `RandomForestClassifier` — trained on the K-Means cluster labels as target classes, so risk level can be predicted for a region/time-window without re-running clustering; also gives feature-importance output for interpretability
- **Model evaluation:** `scikit-learn.metrics` (silhouette score for clustering; accuracy, precision/recall, confusion matrix, cross-validation for the classifier)
- **Experimentation:** Jupyter notebooks for exploration, kept separate from the productionized training script that runs on a schedule
- **Model persistence:** `joblib` to serialize the trained KMeans + RandomForest models; versioned artifacts stored alongside a small metadata file (training date, dataset snapshot version, metrics)
- **Model refresh cadence:** re-run training when the Kaggle dataset snapshots are updated, or on a manual trigger — not on every new live earthquake event (the live feed is for the real-time map, not for retraining)

### Infrastructure / deployment
- Start simple: a single VPS (DigitalOcean, Linode/Akamai, or Philippine-friendly options) running Docker Compose (API + Postgres + Redis + worker)
- Once it grows: split into managed Postgres (e.g., Supabase or Neon — both have generous free/cheap tiers and give you PostGIS + realtime out of the box, which could actually replace a chunk of your custom backend)
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (errors) + simple uptime checks (UptimeRobot free tier)

> 💡 **Shortcut worth considering:** Supabase (Postgres + PostGIS + realtime subscriptions + auth + storage, all managed) could replace a large chunk of the "Core Data Store" + parts of the "API Layer" above, especially for an MVP. You'd still write your own ingestion workers, but your API surface and real-time push could come almost for free.

---

## 4. Public Data Sources (matched to your hazards)

| Hazard | Source | Access method | Notes |
|---|---|---|---|
| **Earthquake** | USGS Earthquake Catalog (`earthquake.usgs.gov/fdsnws/event/1/`) | REST/GeoJSON, free, no key | Global coverage including PH; real-time feeds updated every 1–5 min; can filter by bounding box for PH |
| **Earthquake (local detail/intensity)** | PHIVOLCS bulletins | Web scraping (no official public API) | PHIVOLCS gives PH-specific intensity (PEIS scale) that USGS won't have — worth the scraping effort |
| **Volcanic activity** | Smithsonian Global Volcanism Program (GVP) | REST API, free | Good for eruption history/status globally, including PH volcanoes (Mayon, Taal, Pinatubo, etc.) |
| **Volcanic alert levels (PH-specific)** | PHIVOLCS volcano bulletins | Web scraping | Alert level 0–5 system is PHIVOLCS-specific, not on GVP |
| **Active faults** | PHIVOLCS Active Fault Atlases (PDF, per-fault) + GEM Global Active Faults Database (shapefile, includes PH) | Manual digitization for PHIVOLCS atlases; direct shapefile download for GEM | This is your biggest "not really an API" gap — see below |
| **Ground movement/deformation** | Copernicus Sentinel-1 (via ESA Copernicus Data Space) or ASF (Alaska Satellite Facility) InSAR data | REST API, free registration | Genuinely advanced — InSAR processing (detecting cm-level ground deformation) is a research-grade pipeline. Treat as a stretch goal, not MVP. |
| **Landslide susceptibility** | NASA Global Landslide Hazard Assessment, or PHIVOLCS/MGB landslide susceptibility maps (often released as static maps/PDFs per province) | Static datasets, manual ingestion | Less "real-time," more a base layer you overlay |
| **Historical earthquake training data (PHIVOLCS)** | [Kaggle: Philippine Earthquakes from PHIVOLCS](https://www.kaggle.com/datasets/bwandowando/philippine-earthquakes-from-phivolcs) | Bulk CSV download via Kaggle (API or manual export), one-time/periodic import | Used as the **training corpus** for K-Means/Random Forest, not for live ingestion — sidesteps re-scraping years of PHIVOLCS bulletins just to get historical volume |
| **Historical earthquake training data (USGS, 1900–2025)** | [Kaggle: Philippine Earthquakes 1900–2025 from USGS](https://www.kaggle.com/datasets/bwandowando/philippine-earthquakes-1900-2025-from-usgs) | Bulk CSV download via Kaggle (API or manual export), one-time/periodic import | Long historical baseline (125 years) that the live USGS GeoJSON feed can't practically backfill; used the same way — training only |

**Reality check on faults specifically:** there's no live "active fault API" anywhere in the world — fault data is inherently static/slow-changing (updated when new studies happen), so treat it as a **reference layer you load once and update quarterly**, not something your ingestion pipeline polls.

---

## 5. Suggested Data Model (simplified)

```sql
-- Core event table (earthquakes, eruptions treated as timestamped events)
CREATE TABLE hazard_events (
  id UUID PRIMARY KEY,
  hazard_type TEXT CHECK (hazard_type IN ('earthquake','volcanic','landslide')),
  source TEXT, -- 'usgs', 'phivolcs', 'gvp'
  external_id TEXT, -- source's own event ID, for dedup
  magnitude NUMERIC,
  depth_km NUMERIC,
  location GEOGRAPHY(POINT, 4326),
  place_name TEXT,
  occurred_at TIMESTAMPTZ,
  alert_level TEXT,
  raw_payload JSONB, -- keep the original for reprocessing
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_hazard_events_geo ON hazard_events USING GIST(location);

-- Static reference layers
CREATE TABLE fault_lines (
  id UUID PRIMARY KEY,
  name TEXT,
  source TEXT, -- 'phivolcs_atlas', 'gem'
  geom GEOGRAPHY(LINESTRING, 4326),
  max_magnitude_estimate NUMERIC,
  metadata JSONB
);

CREATE TABLE volcanoes (
  id UUID PRIMARY KEY,
  name TEXT,
  location GEOGRAPHY(POINT, 4326),
  current_alert_level INT,
  last_updated TIMESTAMPTZ
);

-- Regional seismic risk profiling (ML layer output — written by batch jobs, read by the API)
CREATE TABLE region_seismic_features (
  id UUID PRIMARY KEY,
  region_name TEXT,              -- province/administrative region or grid cell id
  geom GEOGRAPHY(POLYGON, 4326),
  event_count INT,
  mean_magnitude NUMERIC,
  max_magnitude NUMERIC,
  mean_depth_km NUMERIC,
  event_density NUMERIC,         -- events per unit area, used as a clustering feature
  dataset_snapshot TEXT,         -- which Kaggle dataset version this was computed from
  computed_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE region_risk_profiles (
  id UUID PRIMARY KEY,
  region_id UUID REFERENCES region_seismic_features(id),
  kmeans_cluster INT,            -- raw cluster id from the unsupervised stage
  rf_predicted_label TEXT,       -- e.g. 'Low','Moderate','High','Very High'
  rf_confidence NUMERIC,         -- classifier's predicted-class probability
  feature_importances JSONB,     -- top contributing features for this prediction
  model_version TEXT,            -- ties back to a joblib artifact + metadata file
  generated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. Suggested Build Phases

| Phase | Scope |
|---|---|
| **1 — MVP** | USGS earthquake feed ingestion → PostGIS → simple REST API → web map showing last 7 days of PH-region earthquakes |
| **2** | Add PHIVOLCS scraper for local intensity + volcano bulletins; add real-time push (WebSocket) |
| **3** | Layer in static fault lines (GEM dataset) + volcano hazard zones as map overlays |
| **4** | Mobile app with push notifications (FCM) for new events near user's saved location |
| **5** | Regional Seismic Risk Profiling: ingest Kaggle PHIVOLCS + USGS (1900–2025) historical datasets → feature engineering per region → K-Means clustering → Random Forest classifier → risk profile map layer |
| **6 (stretch)** | Landslide susceptibility overlays; InSAR-based ground deformation layer |

---

## 7. Things worth deciding early
- **Naming/branding** — worth picking something distinct from "NOAH" to avoid confusion with the actual DOST system
- **Legal/attribution** — USGS and GVP data is public domain/CC-licensed but requires attribution; PHIVOLCS content should be clearly credited since you're scraping, not API-consuming
- **Rate limits** — USGS caches feeds for 1 min (recent) to 15 min (older); poll no faster than that
- **Dataset licensing/attribution for the Kaggle training sets** — confirm the license terms on both Kaggle dataset pages (they're compiled by a third-party uploader, not published directly by PHIVOLCS/USGS) and credit both the original agency and the Kaggle compiler in `docs/data-sources.md`
- **Cluster/label naming for the risk profiling module** — decide on a fixed, documented mapping from `kmeans_cluster` (0,1,2,...) to human-readable risk labels (Low/Moderate/High/Very High) early, since cluster numbering can change between retraining runs if not pinned by centroid ordering (e.g., always order clusters by mean magnitude ascending)