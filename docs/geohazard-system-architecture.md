# GeoHazard PH - System Architecture

Reviewed: 2026-11-06. This describes implemented boundaries; [project status](project-status.md)
records acceptance and [deployment operations](free-split-deployment.md) records
hosting. A route's presence does not prove its data or model is provisioned.

The architecture has five layers:

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
- `GET /volcanoes` — PHIVOLCS volcano bulletin feed with bounded cached fallback.
- `GET /alerts` — alert subscriptions (stub).
- `GET /subscribe` — broker-readiness status; not a durable alert subscription or delivery guarantee.
- `GET /risk-profile/clusters` — regional seismic risk profiles.
- `GET /risk-profile/{region_name}` — single region risk profile.
- `POST /scene-analyses` — transient camera-image review returning ranked image-space floor/ground candidates, visual cues, and limitations. This route does not persist photos or assess safety; model runtime and weights are not provisioned in the default image pending measured deployment fit.

Realtime uses `WSS /ws/events` outside `/api/v1`. The ingestion transaction resolves
canonical identity before a best-effort post-commit publish to Redis. The API relays
messages to connected browsers; there is no durable replay. A LIVE badge means
transport connectivity, not source-worker health or event freshness.

## Active split staging

GitHub Actions runs one source-ingestion cycle using the pinned published image,
writing to Supabase PostGIS and publishing to Upstash Redis. Render API reads the
same database and relays WSS; Render Static Site serves the web application.
The configured worker cadence is six hours. Browser REST refresh every 30 seconds
reads persisted data and does not ingest sources. Migrations remain release-only
operations, distinct from worker cycles. Colocated Docker Compose/Oracle is an
alternative topology, not the active staging deployment.

## Scene review paths

Both clients capture only after an explicit user action and display image-space
candidates with limitations. The web default uses a local worker with pinned
quantized ONNX weights; it does not upload photos or call the Python endpoint.
First use downloads model/runtime files; device capacity and public downloads
can limit availability. See [browser architecture and verification](browser-scene-analysis.md).

Mobile retains bounded JPEG requests to `POST /api/v1/scene-analyses`. The Python
route processes images transiently in memory without image/history persistence.
Its default deployment lacks model runtime/weights and can return a typed 503;
a working browser worker does not provision mobile inference.

Both paths use provisional blur handling and deterministic visual ranking. Neither
establishes structural stability, hidden hazards, accessibility or safety; obstruction
is not validated. See the [scene-review runbook](runbook.md#epic-7-scene-review)
and [model preflight](data-sources.md#scene-analysis-model-preflight).
