# GeoHazard PH — Project File Tree

Monorepo layout matching `geohazard-system-architecture.md` (stack) and
`geohazard-development-framework.md` (epics/phases). Assumes **Python/FastAPI**
for both ingestion and API (per the architecture doc's suggestion to share
Pydantic models), **React + MapLibre** web, **React Native** mobile,
**Docker Compose** for local/staging infra, and a standalone **Python `ml/`
module** (scikit-learn: K-Means + Random Forest) for the Regional Seismic Risk
Profiling feature. Swap `backend/` internals for NestJS if you go the Node
route instead — the folder boundaries stay the same; `ml/` stays Python either
way since scikit-learn is the reference implementation used here.

```
geohazard-ph/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example                      # DB, Redis, API keys (FCM, Sentry, S3-compatible), never committed
├── docker-compose.yml                # api + worker + postgres/postgis + redis (local/staging)
├── docker-compose.prod.yml
│
├── docs/                             # versioned alongside code, per framework doc §6
│   ├── geohazard-project-overview.md
│   ├── geohazard-development-framework.md
│   ├── geohazard-system-architecture.md
│   ├── adr/                          # architecture decision records (e.g., "why FastAPI over NestJS")
│   │   └── 0001-record-architecture-decisions.md
│   ├── data-sources.md               # USGS/PHIVOLCS/GVP/GEM access notes + attribution requirements
│   └── runbook.md                    # what to do when a scraper breaks, source downtime, etc.
│
├── backend/
│   ├── pyproject.toml                # or requirements.txt + requirements-dev.txt
│   ├── alembic.ini                   # migration tool config
│   ├── Dockerfile
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entrypoint
│   │   ├── config.py                 # env/settings (Pydantic Settings)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── db.py                 # SQLAlchemy engine/session, PostGIS setup
│   │   │   ├── redis.py              # cache + pub/sub client
│   │   │   ├── logging.py
│   │   │   └── security.py           # if/when auth is added (LGU/admin accounts)
│   │   │
│   │   ├── models/                   # SQLAlchemy / GeoAlchemy2 ORM models
│   │   │   ├── __init__.py
│   │   │   ├── hazard_event.py       # earthquakes, eruptions (EPIC 1/2)
│   │   │   ├── fault_line.py         # EPIC 3
│   │   │   ├── volcano.py            # EPIC 3
│   │   │   ├── landslide_zone.py     # EPIC 6 (stretch)
│   │   │   ├── user_subscription.py  # saved locations for alerts (EPIC 4)
│   │   │   ├── region_seismic_features.py  # per-region ML input features (EPIC 5)
│   │   │   └── region_risk_profile.py      # K-Means/Random Forest output labels (EPIC 5)
│   │   │
│   │   ├── schemas/                  # Pydantic request/response models (shared shape w/ ingestion)
│   │   │   ├── __init__.py
│   │   │   ├── hazard_event.py
│   │   │   ├── fault_line.py
│   │   │   ├── volcano.py
│   │   │   ├── alert.py
│   │   │   └── risk_profile.py       # EPIC 5
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py               # shared FastAPI dependencies (db session, pagination)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── events.py         # GET /events?type=earthquake&since=...
│   │   │       ├── hazards.py        # GET /hazards/:type
│   │   │       ├── faults.py         # GET /faults
│   │   │       ├── volcanoes.py      # GET /volcanoes
│   │   │       ├── alerts.py         # subscription CRUD
│   │   │       ├── subscribe.py      # WebSocket / SSE channel, per architecture §2–3
│   │   │       └── risk_profile.py   # GET /risk-profile/:region, GET /risk-profile/clusters (EPIC 5)
│   │   │
│   │   └── services/                 # business logic separate from route handlers
│   │       ├── __init__.py
│   │       ├── dedup.py              # USGS/PHIVOLCS event dedup logic (EPIC 2)
│   │       ├── proximity.py          # spatial "within radius" queries for alerts
│   │       ├── notifications.py      # FCM push dispatch
│   │       └── risk_profile.py       # reads region_risk_profiles table for API responses (EPIC 5)
│   │
│   ├── ingestion/                    # scheduled workers, separate process(es) from the API
│   │   ├── __init__.py
│   │   ├── scheduler.py              # cron entrypoint / Celery beat config
│   │   ├── celery_app.py             # or simple cron+queue if starting minimal
│   │   │
│   │   ├── sources/
│   │   │   ├── __init__.py
│   │   │   ├── usgs.py               # GeoJSON feed ingestion (EPIC 1)
│   │   │   ├── phivolcs_earthquake.py    # bulletin scraper (EPIC 2)
│   │   │   ├── phivolcs_volcano.py       # bulletin scraper (EPIC 2)
│   │   │   ├── gvp.py                 # Smithsonian GVP REST client
│   │   │   ├── gem_faults.py          # GEM Global Active Faults shapefile importer (EPIC 3)
│   │   │   ├── phivolcs_fault_atlas.py   # manual/semi-manual digitization import (EPIC 3)
│   │   │   ├── landslide_susceptibility.py  # EPIC 6 (stretch)
│   │   │   └── insar_sentinel1.py     # EPIC 6 (stretch, research spike first)
│   │   │
│   │   ├── scraping/
│   │   │   ├── __init__.py
│   │   │   ├── html_cache/            # raw HTML snapshots so re-parsing doesn't re-hit source
│   │   │   └── parsers.py             # BeautifulSoup/Playwright parsing helpers
│   │   │
│   │   └── validation.py             # schema validation + error logging for ingestion failures
│   │
│   ├── db/
│   │   ├── migrations/               # Alembic migration scripts
│   │   │   └── versions/
│   │   ├── init_postgis.sql          # CREATE EXTENSION postgis; etc.
│   │   └── seed/                     # sample/fixture data for local dev
│   │       ├── sample_earthquakes.json
│   │       └── sample_fault_lines.geojson
│   │
│   └── tests/
│       ├── unit/
│       │   ├── test_dedup.py
│       │   ├── test_usgs_parser.py
│       │   └── test_phivolcs_parser.py
│       ├── integration/
│       │   ├── test_events_api.py    # against a test PostGIS instance
│       │   └── test_proximity_query.py
│       ├── fixtures/                 # saved real API response payloads (per testing strategy doc)
│       │   ├── usgs_response_sample.json
│       │   └── phivolcs_bulletin_sample.html
│       └── conftest.py
│
├── ml/                                # Regional Seismic Risk Profiling module (EPIC 5)
│   ├── pyproject.toml                 # separate from backend/ so training deps (scikit-learn,
│   │                                   # jupyter) don't bloat the API/worker container image
│   ├── notebooks/                     # exploration only — nothing here runs in production
│   │   ├── 01_eda_phivolcs_usgs.ipynb
│   │   ├── 02_kmeans_tuning.ipynb     # elbow method / silhouette score exploration
│   │   └── 03_random_forest_eval.ipynb
│   │
│   ├── data/
│   │   ├── raw/                       # untouched Kaggle exports (gitignored — large files)
│   │   │   ├── phivolcs_kaggle_export.csv       # from bwandowando/philippine-earthquakes-from-phivolcs
│   │   │   └── usgs_1900_2025_kaggle_export.csv # from bwandowando/philippine-earthquakes-1900-2025-from-usgs
│   │   └── processed/                 # cleaned + merged, region-aggregated feature tables
│   │       └── region_features.parquet
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── ingest_kaggle.py           # download/load Kaggle datasets (Kaggle API or manual export)
│   │   ├── clean_merge.py             # reconcile PHIVOLCS + USGS schemas, dedupe overlapping events
│   │   ├── features.py                # per-region aggregation: count, mean/max magnitude, mean
│   │   │                               # depth, spatial density
│   │   ├── clustering.py              # K-Means: fit, choose k, assign region_seismic_features → cluster
│   │   ├── classifier.py              # Random Forest: train on cluster labels, predict, feature importances
│   │   ├── evaluate.py                # silhouette score, accuracy/precision/recall, confusion matrix
│   │   ├── train.py                   # orchestrates the full pipeline end-to-end, writes to PostGIS
│   │   └── persist.py                 # joblib save/load + model metadata (version, dataset snapshot, metrics)
│   │
│   ├── model_artifacts/               # versioned joblib files + metadata.json (gitignored, or LFS)
│   │   └── v1/
│   │       ├── kmeans_model.joblib
│   │       ├── random_forest_model.joblib
│   │       └── metadata.json
│   │
│   └── tests/
│       ├── test_features.py           # aggregation matches hand-computed values on a fixture slice
│       ├── test_clustering.py         # silhouette score above threshold on fixture data
│       ├── test_classifier.py         # accuracy/precision/recall above threshold on held-out split
│       └── fixtures/
│           └── sample_region_events.csv   # small trimmed slice of the Kaggle datasets, not the full files
│
├── web/                              # React + Vite + TS dashboard
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── Dockerfile
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── map/
│   │   │   │   ├── MapView.tsx           # MapLibre GL wrapper
│   │   │   │   ├── LayerControls.tsx     # toggle earthquake/volcano/fault/landslide/risk layers
│   │   │   │   ├── EventMarker.tsx
│   │   │   │   ├── FaultLineLayer.tsx
│   │   │   │   └── RiskProfileLayer.tsx  # choropleth of region_risk_profiles (EPIC 5)
│   │   │   ├── events/
│   │   │   │   ├── EventList.tsx
│   │   │   │   ├── EventFilterBar.tsx    # by hazard type, date range, magnitude
│   │   │   │   └── EventDetailPanel.tsx
│   │   │   ├── volcano/
│   │   │   │   └── VolcanoAlertCard.tsx
│   │   │   ├── risk/
│   │   │   │   ├── RiskProfileCard.tsx   # cluster + RF label, confidence, feature importances
│   │   │   │   └── RegionLookup.tsx      # search a province/region for its risk profile
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx             # main map + layer controls
│   │   │   ├── HistoricalBrowser.tsx     # filterable event timeline
│   │   │   ├── RiskProfileExplorer.tsx   # dedicated regional risk-profiling view (EPIC 5)
│   │   │   └── About.tsx                 # data source attribution (USGS/GVP/PHIVOLCS/Kaggle)
│   │   │
│   │   ├── hooks/
│   │   │   ├── useEvents.ts              # TanStack Query hooks against API
│   │   │   ├── useFaultLines.ts
│   │   │   ├── useRiskProfiles.ts        # fetches /risk-profile/:region, /risk-profile/clusters
│   │   │   └── useRealtimeAlerts.ts      # WebSocket/SSE subscription
│   │   │
│   │   ├── api/
│   │   │   └── client.ts                 # typed fetch wrapper for backend REST API
│   │   │
│   │   ├── types/
│   │   │   └── hazard.ts                 # mirrors backend Pydantic schemas
│   │   │
│   │   └── styles/
│   │       └── index.css
│   │
│   └── tests/
│       └── MapView.test.tsx              # component test w/ fixture data
│
├── mobile/                           # React Native app (EPIC 4)
│   ├── package.json
│   ├── app.json
│   ├── metro.config.js
│   ├── ios/                          # native project files (generated)
│   ├── android/                      # native project files (generated)
│   │
│   ├── src/
│   │   ├── App.tsx
│   │   ├── navigation/
│   │   │   └── RootNavigator.tsx
│   │   ├── screens/
│   │   │   ├── HomeScreen.tsx            # quick-glance status
│   │   │   ├── NearbyHazardsScreen.tsx
│   │   │   ├── AlertsScreen.tsx
│   │   │   └── SavedLocationsScreen.tsx  # proximity alert radius setup
│   │   ├── services/
│   │   │   ├── pushNotifications.ts      # FCM integration
│   │   │   ├── offlineCache.ts           # SQLite/WatermelonDB last-known data
│   │   │   └── api.ts
│   │   └── types/
│   │       └── hazard.ts
│   │
│   └── tests/
│       └── offlineCache.test.ts
│
├── infra/
│   ├── github-actions/
│   │   ├── backend-ci.yml            # lint/test/build backend
│   │   ├── web-ci.yml
│   │   ├── mobile-ci.yml
│   │   └── deploy-staging.yml
│   ├── terraform/                    # optional, if infra-as-code is wanted beyond docker-compose
│   │   └── (empty — add if/when moving off single VPS)
│   └── nginx/
│       └── reverse-proxy.conf
│
├── data/                             # static reference layers (EPIC 3), loaded not polled
│   ├── fault_lines/
│   │   ├── gem_active_faults.shp     # + .dbf/.shx/.prj siblings
│   │   └── phivolcs_fault_atlas/     # digitized per-fault data
│   ├── volcano_hazard_zones/
│   └── landslide_susceptibility/     # EPIC 6 stretch, NASA/PHIVOLCS/MGB sourced
│
└── scripts/
    ├── import_fault_lines.py         # one-off/quarterly static layer refresh
    ├── import_landslide_layer.py
    ├── seed_local_db.sh
    └── train_risk_profile_models.sh  # convenience wrapper around ml/src/train.py (EPIC 5)
```

## Notes tied back to the docs

- **Phase → folder mapping** (`geohazard-development-framework.md` §3, `geohazard-system-architecture.md` §6):
  Epic 1 (MVP) lives in `backend/ingestion/sources/usgs.py` + `backend/api/v1/events.py` +
  `web/src/pages/Dashboard.tsx`. Epics 2–6 add files incrementally into the same skeleton rather
  than requiring restructuring — the tree above is sized for the full v1+stretch scope up front.
- **`ingestion/` is separated from `api/`** even though both live under `backend/`, since the
  architecture doc calls these out as distinct layers (ETL vs. application/API) with different
  deploy/scale characteristics (workers vs. request-serving process).
- **`ml/` is a separate top-level module, not nested under `backend/`** — it has its own
  `pyproject.toml` and heavier, training-only dependencies (`scikit-learn`, `jupyter`) that would
  otherwise bloat the API/worker Docker image; it's invoked as a batch job (locally, via
  `scripts/train_risk_profile_models.sh`, or a scheduled CI job), not imported by `backend/` at
  runtime. The API only reads what `ml/src/train.py` has already written into
  `region_seismic_features` / `region_risk_profiles` (architecture doc §5).
- **`ml/data/raw/` holds the two Kaggle exports** (`bwandowando/philippine-earthquakes-from-phivolcs`
  and `bwandowando/philippine-earthquakes-1900-2025-from-usgs`) — gitignored since they're large;
  document the exact download date/version in `ml/model_artifacts/<version>/metadata.json` so
  results are reproducible.
- **`db/migrations/` uses Alembic** to keep the `hazard_events` / `fault_lines` / `volcanoes` /
  `region_seismic_features` / `region_risk_profiles` schema (architecture doc §5) under version
  control rather than hand-run SQL.
- **`tests/fixtures/` holds real saved API responses**, per the framework doc's explicit
  requirement that ingestion stories be tested against real payloads, not just mocks; `ml/tests/fixtures/`
  follows the same principle with a small trimmed slice of the Kaggle CSVs rather than synthetic data.
- **`docs/data-sources.md`** is a placeholder for the attribution requirements the architecture
  doc flags in §7 (USGS/GVP need attribution, PHIVOLCS needs clear "scraped, not API" credit, and
  the two Kaggle datasets need both original-agency and Kaggle-compiler credit).
- If you go with **Supabase** instead of self-managed Postgres+Redis (architecture doc's
  suggested shortcut), `backend/core/db.py` and `backend/core/redis.py` shrink to thin clients,
  and `db/migrations/` may instead live in Supabase's own migration tooling — flag this early
  since it changes the `backend/` internals but not the top-level folder layout.