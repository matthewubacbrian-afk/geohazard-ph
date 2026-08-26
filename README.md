# GeoHazard PH

GeoHazard PH is a Project NOAH-inspired geologic hazard monitoring platform for the Philippines. The starter scaffold sets up a monorepo for public earthquake, volcano, active fault, landslide, and ground-movement data.

## Stack

- Backend/API: Python, FastAPI, SQLAlchemy, Pydantic
- Ingestion: Python workers for USGS, PHIVOLCS, GVP, GEM, and stretch data sources
- Data store: PostgreSQL with PostGIS plus Redis
- Web: React, TypeScript, Vite, MapLibre
- Mobile: React Native starter shell
- Local infra: Docker Compose

## Repository Layout

- `backend/` - API, ingestion workers, migrations, fixtures, and tests
- `web/` - React dashboard starter
- `mobile/` - React Native app starter
- `infra/` - CI/CD, reverse proxy, and deployment placeholders
- `data/` - static reference layer drop zones
- `docs/` - project docs, ADRs, runbooks, specs, and plans
- `scripts/` - one-off import and setup helpers

## Local Setup

1. Copy `.env.example` to `.env`.
2. Start infrastructure with `docker compose up postgres redis`.
3. Install backend dependencies from `backend/`.
4. Install web dependencies from `web/`.
5. Run `python scripts/verify_structure.py` from the repository root to confirm the scaffold is intact.

The scaffold includes sample fixtures and route stubs so the first implementation phase can focus on USGS ingestion, the events API, and the map dashboard.

## Regional Seismic Risk Profiling

The ML module trains K-Means clusters and a Random Forest classifier from two Kaggle historical earthquake datasets:

- `bwandowando/philippine-earthquakes-from-phivolcs`
- `bwandowando/philippine-earthquakes-1900-2025-from-usgs`

Set `KAGGLE_USERNAME` and `KAGGLE_KEY`, then run:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
```

The generated risk labels are descriptive statistical profiles based on historical records. They are not earthquake predictions.
