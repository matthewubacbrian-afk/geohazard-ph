# Runbook

## Ingestion Failure

1. Check which source failed and whether the source is reachable.
2. Inspect the saved raw payload or HTML snapshot.
3. Confirm whether the parser failed because the source shape changed.
4. Disable only the affected source if bad data could reach users.
5. Add or update a fixture before changing parser logic.

## Ingestion & Worker

Run a one-shot USGS ingest locally from `backend/`:

```bash
python -m ingestion.scheduler
```

The command fetches recent earthquakes in the Philippines bounding box and upserts them into Postgres, printing `USGS ingest complete: fetched=<n>, processed=<n>`.

Apply database migrations from `backend/`:

```bash
alembic upgrade head
```

To target a specific database (for example the integration test database), pass the URL on the command line:

```bash
alembic -x db_url=postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard_test upgrade head
```

When the USGS feed is unreachable:

1. Confirm the ingest raises `USGSFetchError` and check the underlying HTTP/network error in the logs.
2. Verify the source status, URL, and credentials (USGS requires no API key; verify network egress).
3. Respect the one-minute minimum poll cadence; do not hammer the feed.
4. Confirm the bounding box (`PH_BBOX`) and `eventtype` filter are still valid if ingest runs but returns zero events.

### API — regional event summary

`GET /api/v1/events/summary` returns aggregate statistics (event_count, avg_magnitude, max_magnitude, latest_occurred_at) for events within a bounding box. The bounding box defaults to the Philippines (PH_BBOX) and may be overridden with west/south/east/north query params; an optional region_name labels the response. The web dashboard card uses this endpoint.

## Data Accuracy Concern

1. Treat coordinate, magnitude, alert-level, and deduplication issues as high priority.
2. Preserve raw payloads for reprocessing.
3. Verify against the source site or API before publishing corrections.

## Local Scaffold Check

Run from the repository root:

```bash
python scripts/verify_structure.py
```

## Epic 2 realtime channel (Person B)

Start Redis and the API, then open the dashboard. `GET /api/v1/subscribe` checks
broker connectivity; the dashboard shows LIVE only while its socket is open.
The Nginx configuration forwards `/ws/` with WebSocket upgrade headers.
Container API/worker Redis and database addresses use Compose service names.

For a custom browser API host, set `VITE_API_BASE_URL` in `web/.env.local`.
The WebSocket URL is derived from that API base using ws/wss and `/ws/events`.
An explicit `VITE_WS_URL=wss://your-host/ws/events` override is also supported in
that file. Restart Vite after environment edits.

**Person A handoff:** this branch still has the Epic 1
`ingest_usgs_events(session, events)`; Person B intentionally does not edit
`app/services/ingest.py`. When Person A's canonical ingestion lands, the scheduler
must pass the implemented callback:

```python
from app.schemas.event_change import EventChange
from app.services.events_publisher import publish

# Inside the scheduler, using Person A's generalized service:
processed = ingest_events(session, events, on_committed=publish)
```

Person A must construct `EventChange` for every touched row, including demotions,
after assigning canonical fields, and invoke the callback strictly after commit.
Until that lands, normal ingestion does not emit pushes; the dashboard's
30-second REST refresh continues to work. The publisher and Redis/WebSocket
integration tests exercise the sealed messages without pretending to implement
Person A's canonicalization.

Redis pub/sub is best-effort, without durable replay. Lost publications recover
through REST; never retry the database transaction because publishing failed.
Each browser uses its own Redis subscription, closed on disconnect. Revisit shared
fan-out if concurrent-client volume warrants it. Multi-process APIs each have
independent subscriptions. No mobile push or managed subscriptions are introduced.

Run backend tests with local PostGIS and Redis available. Realtime integration
tests use a unique test channel so fixture events never enter the live dashboard.
The source tests use saved HTML and never make external network calls.

Backend CI provisions both PostGIS and a health-checked Redis service and sets
`REDIS_URL` explicitly. If the realtime integration test fails while opening a
WebSocket with code 1013, check Redis availability first: subscription happens
before the handshake is accepted. Adding sleeps after publication cannot repair
a failed connection. `TestClient`'s `receive_json()` waits for the next message
and does not accept a `timeout` argument.

## PHIVOLCS volcano bulletins

Use the dashboard's **Volcano bulletins** view or `GET /api/v1/volcanoes`.
The API refreshes on demand at most once every five minutes per process.
Concurrent requests share one fetch. Failed refresh attempts are rate-limited
to once per minute. Cached failures are labelled stale for at most one hour;
older or missing data produces a retryable 503, never synthetic bulletin data.

Settings in the root environment:

| Variable | Default |
| --- | --- |
| `PHIVOLCS_VOLCANO_URL` | `https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin` |
| `PHIVOLCS_VOLCANO_TIMEOUT_SECONDS` | 15 |
| `PHIVOLCS_VOLCANO_CACHE_SECONDS` | 300 |
| `PHIVOLCS_VOLCANO_STALE_SECONDS` | 3600 |

A TLS/network failure raises `PhivolcsFetchError`; changed/invalid HTML raises
`PhivolcsParseError`. Both are logged by class without secret-bearing exception
text. Diagnose the source outside the request path. If the network uses a private
CA, configure a trusted CA bundle through Requests' `REQUESTS_CA_BUNDLE`; do not
disable TLS verification. During implementation on 2026-09-08 the live host failed
certificate-chain validation in this environment. Fixture parsing and endpoint
behavior were verified; a verified live fetch must be retried once trust/source
certificate configuration is corrected.
