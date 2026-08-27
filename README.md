# GeoHazard PH

GeoHazard PH is a Project NOAH-inspired geologic hazard monitoring platform for the Philippines. The repository is a monorepo for the API, web dashboard, ML risk-profile pipeline, mobile starter shell, infrastructure, and source-data documentation.

## What Is Included

- `backend/` - FastAPI API, ingestion workers, services, database models, and backend tests.
- `web/` - React, TypeScript, Vite, and MapLibre dashboard.
- `ml/` - Kaggle-backed regional seismic risk profiling pipeline using K-Means and Random Forest.
- `mobile/` - React Native starter shell.
- `infra/` - CI/CD, reverse proxy, and deployment placeholders.
- `data/` - local static data drop zones.
- `docs/` - project documentation, specs, implementation plans, ADRs, and runbooks.
- `scripts/` - helper scripts for verification, imports, and ML training.

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

If the frontend needs a different API URL, set this in `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
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

## Regional Seismic Risk Profiles

The ML module trains descriptive regional seismic risk profiles from two Kaggle historical earthquake datasets:

- `bwandowando/philippine-earthquakes-from-phivolcs`
- `bwandowando/philippine-earthquakes-1900-2025-from-usgs`

Set Kaggle credentials in `.env` or in your shell:

```env
KAGGLE_USERNAME=
KAGGLE_KEY=
```

Train from Kaggle:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
```

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
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
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
