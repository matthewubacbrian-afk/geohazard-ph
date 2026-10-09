# GeoHazard PH

GeoHazard PH is a Project NOAH-inspired geologic hazard monitoring platform for the Philippines. The repository is a monorepo for the API, web dashboard, ML risk-profile pipeline, mobile starter shell, infrastructure, and source-data documentation.

## What Is Included

- `backend/` - FastAPI API, ingestion workers, services, database models, and backend tests.
- `web/` - React, TypeScript, Vite, and MapLibre dashboard.
- `ml/` - Kaggle-backed regional seismic risk profiling pipeline using K-Means and Random Forest.
- `mobile/` - React Native starter shell.
- `infra/` - reverse proxy configuration for the portable staging release.
- `data/` - local static data drop zones.
- `docs/` - project documentation, specs, implementation plans, ADRs, and runbooks.
- `scripts/` - helper scripts for verification, imports, and ML training.

## Coding Standards

All human-written and generated changes should follow [CODING_STANDARDS.md](CODING_STANDARDS.md). Coding agents should also read [AGENTS.md](AGENTS.md) before modifying the repository.

Staging images and a portable Compose deployment bundle can be produced by the
manual workflow in `.github/workflows/deploy-staging.yml`. See
[docs/runbook.md](docs/runbook.md) for host setup, reconciliation, deployment,
and rollback commands.

## Prerequisites

Install these before running the project locally:

- Python 3.11
- Node.js and npm
- Docker Desktop
- Git
- Kaggle credentials, only if training risk-profile models from Kaggle

On Windows, the ML training wrapper prefers the Python launcher:

```powershell
py -3.11 --version
```

## First-Time Setup

### Linux (Bash)

Use Python 3.11 and separate virtual environments for the API and ML packages.
Run these commands from the repository root. Keep an existing `.env` if you
have already configured it:

```bash
test -f .env || cp .env.example .env
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e './backend[dev]'
python3.11 -m venv ml/.venv
ml/.venv/bin/python -m pip install -e './ml[dev]'
(cd web && npm ci)
python3.11 scripts/verify_structure.py
```

On Linux, Docker Engine with the Compose plugin can be used in place of Docker
Desktop. If the daemon is stopped, start it with `sudo systemctl start docker`.
Your user must have access to the Docker daemon to run the commands below.

Start Postgres and Redis, wait for Postgres to accept connections, and apply
the database migrations before starting the API:

```bash
docker compose up -d postgres redis
docker compose exec postgres pg_isready -U geohazard -d geohazard
(cd backend && .venv/bin/alembic upgrade head)
```

Run the API and web app in separate terminals:

```bash
# Terminal 1, from the repository root
cd backend
.venv/bin/uvicorn app.main:app --reload
```

```bash
# Terminal 2, from the repository root
cd web
npm run dev
```

Open `http://localhost:5173` for the dashboard or `http://localhost:8000/docs`
for the API documentation. To populate the earthquake feed, run
`(cd backend && .venv/bin/python -m ingestion.scheduler)` from the repository
root after applying migrations. This fetches live USGS data.

For local sample risk profiles, set `RISK_PROFILE_EXPORT_PATH=tests/fixtures/risk_profiles.json`
in the root `.env`; the path is relative to the backend working directory.
Kaggle credentials are needed for training unless you pass `--offline`.

Verify the installation from the repository root:

```bash
# Create the separate integration-test database once.
docker compose exec postgres createdb -U geohazard geohazard_test
(cd backend && .venv/bin/pytest -v)
(cd ml && .venv/bin/pytest -v)
(cd web && npm test && npm run build)
```

The mobile starter is optional for dashboard development. Install its dependencies
with `(cd mobile && npm ci)` when working on mobile.

### Windows (PowerShell)

Run these commands from the repository root:

```powershell
Copy-Item .env.example .env
```

Start local infrastructure:

```powershell
docker compose up postgres redis
```

Install backend dependencies:

```powershell
Set-Location backend
pip install -e ".[dev]"
Set-Location ..
```

Install web dependencies:

```powershell
Set-Location web
npm install
Set-Location ..
```

Install ML dependencies:

```powershell
Set-Location ml
pip install -e ".[dev]"
Set-Location ..
```

Verify the expected project structure:

```powershell
python scripts\verify_structure.py
```

## Run The App

Use three terminal windows: one for infrastructure, one for the backend, and one for the web app.

Terminal 1, from the repository root:

```powershell
docker compose up postgres redis
```

Terminal 2, from `backend/`:

```powershell
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Terminal 3, from `web/`:

```powershell
npm run dev
```

The web app usually runs at:

```text
http://localhost:5173
```

If the frontend needs a different API URL, set this in `web/.env.local`
(Vite reads environment files from `web/`):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The backend allows the Vite dev origins (`http://localhost:5173` and `http://127.0.0.1:5173`) by default via the `CORS_ORIGINS` setting. Add or change allowed origins through `CORS_ORIGINS` in `.env` using a JSON array (the frontend calls the API directly from the browser, so the origin must be listed here):

```env
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

## Run With Docker Compose

To start Postgres, Redis, the API, and the worker together:

```powershell
docker compose up --build
```

Useful local ports:

- API: `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## Live Earthquake Ingestion

The ingestion worker polls USGS and PHIVOLCS sources on a configurable interval and upserts events into Postgres. Start the polling worker locally from `backend/`:

```powershell
python -m ingestion.scheduler
```

By default the worker runs in a long-running polling loop, waiting at least 60 seconds after each cycle to respect source caching. Configure the interval with `INGEST_POLL_INTERVAL_SECONDS` (seconds, minimum 60). Each cycle runs USGS and PHIVOLCS independently; if one source fails, the other still runs. `SIGTERM`/`SIGINT` interrupts the wait immediately; an active cycle finishes before shutdown.

For a local one-shot run, set `INGEST_MAX_CYCLES=1` in the command's environment. Leave it unset for the Docker worker: a bounded worker combined with `restart: unless-stopped` would repeatedly restart.

In Docker, the `worker` service runs the same long-running scheduler:

```powershell
docker compose up --build worker
```

The live earthquake feed, `GET /api/v1/events`, is database-backed and returns events newest-first, with an optional `since` filter:

```text
GET /api/v1/events
GET /api/v1/events?since=2026-08-28T00:00:00Z
```

The `hazard_events` table is managed by Alembic migrations under `backend/db/migrations/versions`. Apply migrations from `backend/` with:

```powershell
alembic upgrade head
```

## Regional Seismic Risk Profiles

The ML module trains descriptive regional seismic risk profiles from two Kaggle historical earthquake datasets:

- `bwandowando/philippine-earthquakes-from-phivolcs`
- `bwandowando/philippine-earthquakes-1900-2025-from-usgs`

Set Kaggle credentials in `.env` or in your shell:

```env
KAGGLE_USERNAME=
KAGGLE_KEY=
```

Training downloads the latest version of each Kaggle dataset by default. When
fresh monthly data is published, rerun training without a manual download step.
Training runs are started manually; no schedule is configured.

Train with the latest Kaggle data:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1
```

Preserve the local CSVs under `ml/data/raw/` and use `-Offline` to reuse saved
inputs without downloading (`--offline` for the Python CLI):

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Offline
```

Automatic CLI local discovery currently treats all CSVs as PHIVOLCS inputs.
For mixed PHIVOLCS/USGS snapshots, this applies Manila time normalization to USGS
timestamps and can change deduplication, so these flags alone may not reproduce
download-mode output. For source-correct reproducible processing of saved inputs,
call `ml.train.run_training(download=False, phivolcs_paths=[...], usgs_paths=[...])`
with separate explicit lists of `Path` objects for each source.

Generated artifacts are written under:

```text
ml/model_artifacts/v1/
```

Expected outputs include:

- `metadata.json`
- `risk_profiles.json`
- `region_features.csv`
- `kmeans_model.joblib`
- `scaler.joblib`
- `random_forest_model.joblib`

In `metadata.json`, `datasets[].version` records the integer Kaggle version for
each downloaded dataset, distinguishing retrains that used different source
versions. Offline runs record `null` because no Kaggle version is resolved.

The generated labels are descriptive statistical profiles based on historical records. They are not earthquake predictions.

## Test And Build

Run ML tests:

```powershell
Set-Location ml
pytest -v
Set-Location ..
```

Run backend tests:

```powershell
Set-Location backend
pytest -v
Set-Location ..
```

Run web tests:

```powershell
Set-Location web
npm test
Set-Location ..
```

Build the web app:

```powershell
Set-Location web
npm run build
Set-Location ..
```

Run structure verification:

```powershell
python scripts\verify_structure.py
```

## Common Commands

Start infrastructure only:

```powershell
docker compose up postgres redis
```

Start all Docker services:

```powershell
docker compose up --build
```

Run backend API locally:

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

Run web dashboard locally:

```powershell
Set-Location web
npm run dev
```

Train risk-profile models:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Offline
```

Run the full local verification set:

```powershell
Set-Location ml
pytest -v
Set-Location ..\backend
pytest -v
Set-Location ..\web
npm test
npm run build
Set-Location ..
python scripts\verify_structure.py
```

## Epic 2: Realtime And Volcano Bulletins

The dashboard connects to `/ws/events` and updates its map/list from committed
`EventChange` messages. It reconnects automatically and reconciles through REST
every 30 seconds. Source selection applies to both map and list.
`GET /api/v1/subscribe` reports broker connectivity.

The **Volcano bulletins** dashboard view uses `GET /api/v1/volcanoes`, showing
PHIVOLCS alert levels, source links, observation/retrieval dates and stale-cache
status. No Kaggle credentials are required.

**Integration dependency:** Person A must wire `on_committed=publish` in the
canonical ingestion path before regular ingests emit realtime messages. This
Person B slice leaves `ingest.py` unchanged. Live PHIVOLCS fetching also requires
a valid trusted TLS chain; this environment currently reports a certificate
validation failure. See [the runbook](docs/runbook.md) for configuration,
failure behavior, verification and the exact Person A handoff.

## Epic 3: static hazard layers

Fault and volcano-zone overlays now have validated vector import, PostGIS storage,
read endpoints, source attribution, and independent dashboard toggles. Apply migration
`0003` and import reviewed datasets using [the import runbook](docs/runbook.md#import-static-layers-epic-3).
Empty layers remain explicitly labeled until source data is loaded.

The Epic 2 integration and event-feed hover fixes are already merged. Standards
remediation adds consistent API errors, structured startup logging, portable ML tests,
Testing Library web tests, and a typed mobile API mapping boundary.

## Epic 4: Mobile nearby alerts

The mobile starter now has **Nearby**, **Saved locations**, and **Alerts** tabs. Enter
coordinates and a radius of 1–500 km to see matching events from the existing
`GET /api/v1/events` feed. The app stores saved locations, the API URL, and the last
successful event list on the device; when the API is offline, cached events remain visible
with an offline label and retry action.

In **Saved locations**, configure a device-reachable API URL ending in `/api/v1` (for example,
`http://192.168.1.20:8000/api/v1` when the phone and development server share a LAN). The
default URL is empty. The in-app alert list checks for new events on startup or when refreshed;
background push delivery is not configured. Saved coordinates stay on the device and are not
sent to the backend.

### Native mobile development

The native projects target the existing React Native 0.75.5 app. Install dependencies from
`mobile/` with `npm ci`. For Android, install JDK 17 and Android Studio with Android SDK
Platform 34, Build Tools 34.0.0, Platform Tools, and NDK 26.1.10909125. Set `JAVA_HOME` and
`ANDROID_HOME` to those installations, start an Android emulator (or connect a device with USB
debugging), and run the Metro server and app in separate terminals:

```powershell
Set-Location mobile
npm start
```

```powershell
Set-Location mobile
npm run android
```

On an Android emulator, the development computer's localhost is available at `10.0.2.2`; on a
physical phone, use a LAN address reachable from the phone. Android permits cleartext HTTP only
in the debug manifest; production deployments must use HTTPS. Do not commit a local API URL.

iOS builds require macOS, Xcode, and CocoaPods. On a Mac, run `npm ci` from `mobile/`, then
run `pod install` from `mobile/ios/` and `npm run ios` from `mobile/`. The project uses
`com.geohazardph.mobile` as a development application/bundle identifier; choose the final
identifier and configure signing before any store distribution. Mobile CI runs the Jest suite
and Android debug build; it does not replace physical-device UX validation, and iOS build
verification remains a Mac task.
