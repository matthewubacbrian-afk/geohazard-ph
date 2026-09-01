# GeoHazard PH — Project File Tree

Current on-disk monorepo layout for **Python/FastAPI** (backend + ingestion),
**React + Vite + TypeScript** web (CSS Modules, MapLibre GL — **no Tailwind**),
**React Native** mobile, **Docker Compose** infra, and a standalone **Python
`ml/` module** (scikit-learn: K-Means + Random Forest) for the Regional Seismic
Risk Profiling feature. Stack decisions are recorded in
`docs/adr/` and the architecture doc; this tree reflects what is actually
checked in today (including scaffold/placeholder files), not aspirational scope.

```
geohazard-ph/
├── AGENTS.md                            # agent/dev instructions, entry point for contributors
├── BACKEND_STANDARDS.md                 # FastAPI/Python conventions
├── CODING_STANDARDS.md                  # cross-stack structure, conventions, verification
├── REACT_BEST_PRACTICES.md              # React conventions
├── README.md
├── LICENSE
├── .env                                 # local env (gitignored)
├── .env.example                         # DB, Redis, API keys (Sentry, S3-compatible), never committed
├── .gitignore
├── docker-compose.yml                   # api + worker + postgres/postgis + redis (local/staging)
├── docker-compose.prod.yml
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml               # lint/test/build backend
│       ├── web-ci.yml
│       ├── mobile-ci.yml
│       └── deploy-staging.yml
│
├── .superpowers/                        # auto-generated SDD tracking (tooling artifact)
│   └── sdd/
│       └── 2026-08-29-epic1-polish/     # task briefs/reports/review diffs for the epic
│
├── .worktrees/                          # git worktree scratch space (currently empty)
│
├── docs/                                # versioned alongside code, per framework doc §6
│   ├── api-contracts.md
│   ├── data-sources.md                  # USGS/PHIVOLCS/GVP/GEM access notes + attribution
│   ├── error-handling-and-logging.md
│   ├── geohazard-project-overview.md    # short stub → root geohazard-*.md
│   ├── geohazard-development-framework.md
│   ├── geohazard-system-architecture.md
│   ├── git-workflow.md
│   ├── glossary.md
│   ├── runbook.md                       # what to do when a scraper breaks, source downtime, etc.
│   ├── testing-standards.md
│   ├── adr/                             # architecture decision records
│   │   ├── 0001-record-architecture-decisions.md
│   │   └── 0002-epic2-realtime-phivolcs-contracts.md
│   └── superpowers/                     # planning/spec records (historical snapshots)
│       ├── plans/*                      # 2026-08-27 … 2026-08-31 plans
│       ├── specs/*                      # matching design specs
│       └── templates/
│           ├── plan-template.md
│           └── spec-template.md
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini                      # migration tool config
│   ├── Dockerfile
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app entrypoint
│   │   ├── config.py                    # env/settings (Pydantic Settings)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── db.py                    # SQLAlchemy engine/session, PostGIS setup
│   │   │   ├── redis.py                 # cache + pub/sub client
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   │
│   │   ├── models/                      # SQLAlchemy / GeoAlchemy2 ORM models
│   │   │   ├── __init__.py
│   │   │   ├── hazard_event.py
│   │   │   ├── fault_line.py
│   │   │   ├── volcano.py
│   │   │   ├── landslide_zone.py
│   │   │   └── user_subscription.py
│   │   │
│   │   ├── schemas/                     # Pydantic request/response models
│   │   │   ├── __init__.py
│   │   │   ├── hazard_event.py
│   │   │   ├── fault_line.py
│   │   │   ├── volcano.py
│   │   │   ├── alert.py
│   │   │   └── risk_profile.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                  # shared FastAPI dependencies (db session, pagination)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── events.py            # GET /events
│   │   │       ├── hazards.py           # GET /hazards/:type
│   │   │       ├── faults.py            # GET /faults
│   │   │       ├── volcanoes.py         # GET /volcanoes
│   │   │       ├── alerts.py            # subscription CRUD
│   │   │       ├── subscribe.py         # WebSocket / SSE channel
│   │   │       └── risk_profile.py      # GET /risk-profile/:region, GET /risk-profile/clusters
│   │   │
│   │   └── services/                    # business logic separate from route handlers
│   │       ├── __init__.py
│   │       ├── events.py
│   │       ├── ingest.py
│   │       ├── dedup.py                 # USGS/PHIVOLCS event dedup logic
│   │       ├── proximity.py             # spatial "within radius" queries for alerts
│   │       ├── notifications.py         # push dispatch
│   │       └── risk_profile.py          # reads risk profiles for API responses
│   │
│   ├── ingestion/                      # scheduled workers, separate process(es) from the API
│   │   ├── __init__.py
│   │   ├── scheduler.py                 # cron entrypoint / Celery beat config
│   │   ├── celery_app.py
│   │   ├── validation.py                # schema validation for ingestion failures
│   │   │
│   │   ├── scraping/
│   │   │   ├── __init__.py
│   │   │   ├── html_cache/              # raw HTML snapshots (re-parsing doesn't re-hit source)
│   │   │   │   └── .gitkeep
│   │   │   └── parsers.py               # BeautifulSoup/Playwright parsing helpers
│   │   │
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── usgs.py                  # GeoJSON feed ingestion
│   │       ├── phivolcs_earthquake.py   # bulletin scraper
│   │       ├── phivolcs_volcano.py      # bulletin scraper
│   │       ├── phivolcs_fault_atlas.py  # fault-atlas import
│   │       ├── gvp.py                   # Smithsonian GVP REST client
│   │       ├── gem_faults.py            # GEM Global Active Faults importer
│   │       ├── landslide_susceptibility.py
│   │       └── insar_sentinel1.py
│   │
│   ├── db/
│   │   ├── init_postgis.sql             # CREATE EXTENSION postgis; etc.
│   │   ├── migrations/                  # Alembic migration scripts
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       ├── .gitkeep
│   │   │       └── 0001_create_hazard_events.py
│   │   └── seed/                        # sample/fixture data for local dev
│   │       ├── sample_earthquakes.json
│   │       └── sample_fault_lines.geojson
│   │
│   └── tests/
│       ├── conftest.py
│       ├── fixtures/
│       │   ├── phivolcs_bulletin_sample.html
│       │   ├── risk_profiles.json
│       │   └── usgs_response_sample.json
│       ├── integration/
│       │   ├── conftest.py
│       │   ├── test_events_api.py
│       │   ├── test_proximity_query.py
│       │   ├── test_risk_profile_api.py
│       │   └── test_usgs_ingest.py
│       └── unit/
│           ├── test_db_engine.py
│           ├── test_dedup.py
│           ├── test_events_service.py
│           ├── test_hazard_event_model.py
│           ├── test_main.py
│           ├── test_phivolcs_parser.py
│           ├── test_risk_profile_service.py
│           ├── test_usgs_fetch.py
│           └── test_usgs_parser.py
│
├── ml/                                # Regional Seismic Risk Profiling module
│   ├── pyproject.toml                  # separate from backend/ so training deps (scikit-learn)
│   │                                   # don't bloat the API/worker container
│   ├── data/
│   │   ├── processed/
│   │   │   └── .gitkeep
│   │   └── raw/                        # untouched Kaggle exports (gitignored — large)
│   │       └── .gitkeep
│   ├── model_artifacts/                # versioned joblib files + metadata.json (gitignored/LFS)
│   │   └── .gitkeep
│   ├── src/ml/
│   │   ├── __init__.py
│   │   ├── ingest_kaggle.py            # download/load Kaggle datasets
│   │   ├── clean_merge.py              # reconcile PHIVOLCS + USGS schemas, dedupe
│   │   ├── features.py                 # per-region aggregation features
│   │   ├── clustering.py               # K-Means: fit, choose k, assign cluster
│   │   ├── classifier.py               # Random Forest: train/predict, feature importances
│   │   ├── evaluate.py                 # silhouette score, accuracy/recall, confusion matrix
│   │   ├── train.py                    # orchestrates the full pipeline, writes to PostGIS
│   │   └── persist.py                  # joblib save/load + model metadata
│   └── tests/
│       ├── fixtures/
│       │   ├── phivolcs_sample.csv
│       │   ├── sample_region_events.csv
│       │   └── usgs_sample.csv
│       ├── test_classifier.py
│       ├── test_clean_merge.py
│       ├── test_clustering.py
│       ├── test_features.py
│       ├── test_ingest_kaggle.py
│       ├── test_persist.py
│       └── test_train.py
│
├── web/                              # React + Vite + TS dashboard (CSS Modules, no Tailwind)
│   ├── DESIGN_NOTES.md                # design tokens, motion, layout conventions
│   ├── WEB_STRUCTURE.md               # web app structure explanation
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   │
│   ├── src/
│   │   ├── main.tsx                   # React DOM bootstrap + global style imports
│   │   ├── App.tsx                    # view switch (hero / dashboard / placeholders)
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── api/
│   │   │   └── client.ts              # typed fetch wrapper for backend REST API
│   │   │
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── ComingSoon.tsx + .module.css
│   │   │   │   ├── Reveal/Reveal.tsx + Reveal.module.css   # IntersectionObserver scroll reveal
│   │   │   │   ├── RiskMeter.tsx + .module.css
│   │   │   │   ├── SectionHeader.tsx + .module.css
│   │   │   │   └── Skeleton.tsx + .module.css
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardMapArea.tsx + .module.css      # map with overlays + loading/empty states
│   │   │   │   └── DashboardSidebar.tsx + .module.css      # controls/views/tabs panel
│   │   │   ├── events/                              # activity feed (active dashboard flow)
│   │   │   │   ├── EventFeed.tsx + .module.css      # scrolling live-event list
│   │   │   │   ├── EventFeedItem.tsx + .module.css  # single event row/card
│   │   │   │   └── EventDetailPanel.tsx + .module.css # selected-event detail
│   │   │   ├── layout/
│   │   │   │   └── TopNav.tsx + TopNav.module.css   # primary navigation (hero/dashboard themes)
│   │   │   ├── map/
│   │   │   │   ├── basemaps.ts                      # basemap definitions + BasemapId type
│   │   │   │   ├── EventMarker.tsx                  # non-MapLibre legacy marker (reference)
│   │   │   │   └── MapView.tsx + MapView.module.css # live MapLibre map
│   │   │   └── risk/
│   │   │       ├── RegionLookup.tsx                 # search a province/region for its risk profile
│   │   │       ├── RiskProfileCard.tsx + .module.css
│   │   │       └── RiskProfilesPanel.tsx + .module.css # risk panel in the dashboard activity area
│   │   │
│   │   ├── hooks/
│   │   │   ├── useEvents.ts              # TanStack Query fetch of hazard events
│   │   │   ├── useEventSummary.ts        # derived summary counts per hazard type
│   │   │   ├── useFaultLines.ts          # legacy fault-line fetch
│   │   │   ├── useRealtimeAlerts.ts      # realtime alert subscription
│   │   │   ├── useRevealOnScroll.ts      # IntersectionObserver reveal (respects reduced-motion)
│   │   │   └── useRiskProfiles.ts        # ML risk-profile fetch
│   │   │
│   │   ├── lib/
│   │   │   └── risk.ts                   # eventRiskBucket() → risk level helpers
│   │   │
│   │   ├── pages/
│   │   │   ├── About.tsx                 # data source attribution (USGS/GVP/PHIVOLCS/Kaggle)
│   │   │   ├── Dashboard.tsx + Dashboard.module.css  # main 3-column instrument panel
│   │   │   ├── DataSources.tsx           # data-source credits
│   │   │   ├── Hero.tsx + Hero.module.css  # marketing landing + methodology
│   │   │   ├── HistoricalBrowser.tsx     # filterable event timeline (reserved)
│   │   │   └── RiskProfileExplorer.tsx   # standalone regional risk-profile view (out of active flow)
│   │   │
│   │   ├── styles/
│   │   │   ├── base.css                  # reset, typography, reduced-motion
│   │   │   ├── tokens.css                # design tokens (primitives + semantic)
│   │   │   └── utilities.css             # shared a11y + button helpers
│   │   │
│   │   └── types/
│   │       ├── hazard.ts                 # mirrors backend Pydantic schemas
│   │       └── views.ts                  # the View union used by App/TopNav
│   │
│   └── tests/                            # Vitest + Testing Library
│       ├── basemaps.test.ts
│       ├── DashboardCard.test.tsx
│       ├── DashboardSidebar.test.tsx
│       ├── DashboardStates.test.tsx
│       ├── EventFeed.test.tsx
│       ├── MapView.test.tsx
│       └── RiskProfile.test.tsx
│
├── mobile/                           # React Native app
│   ├── package.json
│   ├── package-lock.json
│   ├── app.json
│   ├── babel.config.js
│   ├── metro.config.js
│   ├── android/                      # native project files (generated)
│   │   └── .gitkeep
│   ├── ios/                          # native project files (generated)
│   │   └── .gitkeep
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
│   │   │   ├── pushNotifications.ts
│   │   │   ├── offlineCache.ts
│   │   │   └── api.ts
│   │   └── types/
│   │       └── hazard.ts
│   └── tests/
│       └── offlineCache.test.ts
│
├── infra/
│   ├── nginx/
│   │   └── reverse-proxy.conf
│   └── terraform/                    # infra-as-code, if/when moving off single VPS
│       └── .gitkeep
│
├── data/                             # static reference layers (EPIC 3), loaded not polled
│   ├── fault_lines/
│   │   ├── .gitkeep
│   │   └── phivolcs_fault_atlas/
│   │       └── .gitkeep
│   ├── landslide_susceptibility/
│   │   └── .gitkeep
│   └── volcano_hazard_zones/
│       └── .gitkeep
│
└── scripts/
    ├── import_fault_lines.py         # one-off/quarterly static layer refresh
    ├── import_landslide_layer.py
    ├── seed_local_db.sh
    ├── train_risk_profile_models.ps1 # convenience wrapper around ml/src/ml/train.py
    └── verify_structure.py           # checks scaffold/file structure against standards
```

## Notes tied back to the docs

- **Phase → folder mapping** (`geohazard-development-framework.md` §3,
  `geohazard-system-architecture.md` §6): the tree above is the **current on-disk
  state**; epics add files incrementally into the same skeleton rather than
  restructuring. It is no longer "sized for the full v1+stretch scope up front" —
  unbuilt/later-scope files (e.g. ML model artifacts, mobile native runtimes,
  production `.shp` datasets) are scaffold placeholders (`.gitkeep`) or absent.
- **`ingestion/` is separated from `api/`** though both live under `backend/` —
  the architecture doc calls these out as distinct layers (ETL vs. application/API)
  with different deploy/scale characteristics (workers vs. request-serving process).
- **`ml/` is a separate top-level module, not nested under `backend/`** — it has
  its own `pyproject.toml` and heavier, training-only dependencies (`scikit-learn`)
  that would otherwise bloat the API/worker Docker image; it's invoked as a batch
  job (locally via `scripts/train_risk_profile_models.ps1`, or a scheduled CI job),
  not imported by `backend/` at runtime. The API only reads what
  `ml/src/ml/train.py` has already written into PostGIS.
- **`ml/data/raw/` holds the two Kaggle exports**
  (`bwandowando/philippine-earthquakes-from-phivolcs` and
  `bwandowando/philippine-earthquakes-1900-2025-from-usgs`) — gitignored since
  they're large; document the exact download date/version in
  `ml/model_artifacts/<version>/metadata.json` so results are reproducible.
- **`db/migrations/` uses Alembic** to keep the schema under version control rather
  than hand-run SQL.
- **`tests/fixtures/` holds real saved API responses** — per the framework doc's
  requirement that ingestion stories be tested against real payloads, not just
  mocks; `ml/tests/fixtures/` follows the same principle with a small trimmed
  slice of the Kaggle CSVs.
- **`docs/` stubs vs. root `.md`:** `docs/geohazard-*.md` are short redirect stubs
  pointing to the canonical root-level files (`geohazard-project-overview.md`,
  `geohazard-development-framework.md`, `geohazard-system-architecture.md`).
  `geohazard-file-tree.md` lives only at the root.
- **Web styling is CSS Modules**, not Tailwind — see `web/DESIGN_NOTES.md` and
  `web/WEB_STRUCTURE.md` for the token system and the current Dashboard layout.
- **`.superpowers/sdd/`** and `docs/superpowers/` hold automated SDD tracking and
  historical planning/spec records; the spec/plan `.md` files are treated as
  snapshot documentation, not live source-of-truth, and are listed here for
  completeness only.
