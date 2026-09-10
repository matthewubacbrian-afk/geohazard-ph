# GeoHazard PH - System Architecture

This document belongs to the versioned project docs. The original root-level reference file remains available while the repo is being scaffolded.

The starter architecture has five layers:

- Public data sources: USGS, PHIVOLCS pages, Smithsonian GVP, GEM faults, and stretch GIS datasets.
- Ingestion and ETL: scheduled workers normalize, validate, deduplicate, and persist data.
- Core store: PostgreSQL/PostGIS for spatial data and Redis for cache/pub-sub.
- API: FastAPI REST and realtime endpoints.
- Clients: React web dashboard and React Native mobile app.

## API Endpoints

The backend (FastAPI) exposes the following REST endpoints under `/api/v1`:

- `GET /events` — live earthquake events, newest first, optional `since` (ISO 8601) filter.
- `GET /events/summary` — aggregate statistics (event_count, avg_magnitude, max_magnitude, latest_occurred_at) for events within a bounding box (optional west/south/east/north, defaulting to the Philippines; optional region_name).
- `GET /hazards/{hazard_type}` — hazard summary (stub).
- `GET /faults` — imported active fault reference vectors.
- `GET /volcano-zones` — imported volcano hazard polygons.
- `GET /volcanoes` — volcano reference list (stub).
- `GET /alerts` — alert subscriptions (stub).
- `GET /subscribe` — realtime channel subscription status (stub).
- `GET /risk-profile/clusters` — regional seismic risk profiles.
- `GET /risk-profile/{region_name}` — single region risk profile.
