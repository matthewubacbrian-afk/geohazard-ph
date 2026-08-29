# GeoHazard PH — Epic 1 MVP Live Earthquake Slice (Design)

**Date:** 2026-08-28

## Context

The repository's scaffold, backend API routing, ML risk-profiling module (Epic 5), and
web/mobile shells exist, but the **live-data backbone (Epic 1) was never built**. As of the
last verified state:

- `GET /api/v1/events` returns a single hardcoded sample event (`backend/app/api/v1/events.py`).
- The `hazard_events` ORM model is a dataclass stub, not a SQLAlchemy/PostGIS table.
- `backend/app/core/db.py` yields `None`; there is no DB session.
- `backend/db/migrations/versions/` holds only `.gitkeep` — no Alembic migration exists.
- `backend/ingestion/sources/usgs.py` has a parser (`parse_usgs_feature`) but no HTTP fetch/DB write.
- `backend/ingestion/scheduler.py` is a stub.
- `web` map components (`MapView.tsx`, `EventMarker.tsx`) are placeholders.

Epic 5 (risk profiling) and the API/web scaffolds were completed first, but nothing feeds the
database with live events, so the platform cannot yet display real hazards.

## Goal

Build the **MVP live earthquake slice**: real USGS earthquake data flows
**USGS feed → ingestion → PostGIS (`hazard_events`) → `GET /api/v1/events` → web map markers**.
Replace the hardcoded sample and the relevant stubs with working, tested code.

## Scope

### In scope
1. Real SQLAlchemy/GeoAlchemy2 `HazardEvent` ORM model + PostGIS `hazard_events` table via Alembic.
2. Working SQLAlchemy engine/session (`db.py`), wired into FastAPI via `deps.py`.
3. USGS ingestion: fetch the PH-bounding-box feed, parse to `HazardEvent`, deduplicate, upsert.
4. `GET /api/v1/events` reads `hazard_events` from the DB (optional `since` filter, newest first).
5. Web `MapView` renders markers from the `/events` response (loading/empty/error states).
6. Tests at each layer; docs updates.

### Out of scope (later epics)
- PHIVOLCS scrapers, WebSocket push channel, cross-source dedup (Epic 2).
- Static fault/volcano layers and layer-toggle UI (Epic 3).
- Mobile alert app features (Epic 4).
- Wiring the ML risk profiles to live event data (Epic 5 follow-up).

## Decisions (confirmed)
- **Alembic** for schema versioning (scaffold already ships `alembic.ini`; add `env.py`).
- **Dockerized PostGIS** for integration tests; parser/fetch unit tests stay DB-free with a real
  saved USGS response fixture.
- **Configurable PH bounding box** for ingestion (default approx. lat 4–22, lon 116–128).

## Architecture & data flow

```
USGS Earthquake GeoJSON feed (PH bounding box, free, no key)
   │  poll: ingestion/scheduler.py (runs in docker `worker` service)
   ▼
ingestion/sources/usgs.py: fetch_recent_events(bbox) → parse_usgs_feature → HazardEvent[]
   ▼
app/services/ingest.py: ingest_usgs_events(session, events)
      dedup via app/services/dedup.py:dedup_key (source, external_id) → upsert
   ▼
PostgreSQL + PostGIS: hazard_events   (Alembic migration)
   ▼
api/v1/events.py: GET /api/v1/events?since=  → app/services/events.py:list_events
   ▼
web: api/client.ts fetchEvents → hooks/useEvents → Dashboard → MapView/EventMarker (live markers)
```

## Data model (`hazard_events`)

Mirrors the existing Pydantic schema (`backend/app/schemas/hazard_event.py`) plus PostGIS and
raw payload:

| column | type | notes |
|---|---|---|
| id | UUID PK | server default uuid4 |
| hazard_type | text | check in ('earthquake','volcanic','landslide') |
| source | text | 'usgs' |
| external_id | text | source's event id; used with `source` for dedup; unique index on (source, external_id) |
| magnitude | numeric | nullable |
| depth_km | numeric | nullable |
| location | Geography(Point, 4326) | from latitude/longitude |
| place_name | text | |
| alert_level | text | nullable |
| occurred_at | timestamptz | indexed |
| raw_payload | jsonb | original USGS feature; nullable |
| created_at | timestamptz | default now() |

`latitude` / `longitude` are also kept as plain numeric columns for simple API reading and tests;
`location` (the Geography point) is kept in sync for spatial queries (used later by Epics 3–4).

## Files

### Backend
- Modify `backend/pyproject.toml` — add `alembic>=1.13.0` to runtime deps.
- Create `backend/alembic/env.py` — Alembic environment wired to app settings/Base metadata.
- Create `backend/db/migrations/versions/<rev>_create_hazard_events.py` — migration.
- Modify `backend/app/models/hazard_event.py` — SQLAlchemy ORM model (JIT imports keep ffmpeg-free; geospatial via GeoAlchemy2).
- Modify `backend/app/models/__init__.py` — export `HazardEvent`, `Base`.
- Modify `backend/app/core/db.py` — engine, `SessionLocal`, `Base`, `get_db_session`; test override support.
- Modify `backend/app/config.py` — add USGS feed URL + default PH bounding box settings.
- Modify `backend/app/api/deps.py` — pass real session.
- Modify `backend/app/api/v1/events.py` — DB-backed list endpoint.
- Create `backend/app/services/events.py` — `list_events(session, since)` query service.
- Create `backend/app/services/ingest.py` — `ingest_usgs_events(session, events)` upsert + dedup.
- Modify `backend/ingestion/sources/usgs.py` — add `fetch_recent_events(bbox, settings)`.
- Modify `backend/ingestion/scheduler.py` — real `run_usgs_ingest()` entrypoint.
- Tests: modify `backend/tests/unit/test_usgs_parser.py`, create `backend/tests/integration/conftest.py`,
  modify `backend/tests/integration/test_events_api.py`, create `backend/tests/integration/test_usgs_ingest.py`,
  modify `backend/tests/conftest.py`.

### Web
- Modify `web/src/components/map/MapView.tsx` — render markers from events.
- Modify `web/tests/MapView.test.tsx` — assert markers render.
- (No change needed to `client.ts` / `useEvents.ts` — they already target `/events`.)

### Docs
- Update `README.md`, `docs/data-sources.md`, `docs/runbook.md`.

## Testing strategy

- **Backend unit (DB-free):** `test_usgs_parser.py` parses the real saved
  `usgs_response_sample.json` fixture; `fetch_recent_events` tested with a
  monkeypatched `requests.get` returning the fixture (no network).
- **Backend integration (Dockerized PostGIS):** `integration/conftest.py` creates a dedicated
  test database, applies Alembic migrations, and injects fixture events; `test_events_api.py`
  and `test_usgs_ingest.py` exercise the endpoint and ingest service against PostGIS. Uses
  FastAPI `app.dependency_overrides[get_db_session]`.
- **Web:** `MapView.test.tsx` renders known fixture events as markers.
- **Verification commands:** `pytest -v` (from `backend/`), `npm test` and `npm run build`
  (from `web/`), `python scripts\verify_structure.py`, `git diff --check`.

## Notes / risks
- USGS caches feeds ~1 minute (recent) to ~15 minutes (older); poll no faster than that —
  the scheduler cadence defaults to 1 minute but must not hammer the source.
- Preserve `external_id` and `source` for dedup; treat data-correctness bugs as P0.
- PostGIS is required for the integration layer; unit/parser tests must not require a DB.
