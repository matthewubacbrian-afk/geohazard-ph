# Runbook

## Ingestion Failure

1. Check which source failed and whether the source is reachable.
2. Inspect the saved raw payload or HTML snapshot.
3. Confirm whether the parser failed because the source shape changed.
4. Disable only the affected source if bad data could reach users.
5. Add or update a fixture before changing parser logic.

## Ingestion & Worker

Run a one-shot USGS and PHIVOLCS earthquake ingest locally from `backend/`:

```bash
python -m ingestion.scheduler
```

The command fetches recent earthquakes and upserts them into Postgres, logging fetched and processed counts for each source.

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

## Canonical Event Reconciliation

The matcher now rebuilds groups from current source rows during nonempty ingestion.
Before rolling this change into a database that already contains events, take a
database backup and inspect the proposed changes during a maintenance window:

```bash
cd backend
python -m ingestion.reconcile
python -m ingestion.reconcile --apply
```

The first command rolls back its changes and logs inspected and changed row counts.
The second commits them. Check `/api/v1/events` and `/api/v1/events/summary`
afterward. Browsers reconcile through their periodic REST refresh; the maintenance
command does not publish WebSocket messages. Rows without a stable source
`external_id` use a content key and need source-level review if revised.

## Portable Staging Release

The manual **Prepare Staging Release** workflow runs backend and web checks,
publishes API and web images to GHCR under the commit SHA, and uploads a deployment
bundle. It does not connect to a host. The bundle contains `compose.staging.yml`,
the Caddyfile, the deploy script, and `.env.staging.example`.

Prepare a Linux host with Docker Compose v2, a DNS name pointing to the host,
inbound ports 80 and 443, and outbound access to GHCR and the event sources.
Log in to GHCR if the images are private. Extract the bundle to one directory,
copy `.env.staging.example` to `.env.staging`, and set its image prefix, domain,
database credentials, CORS origin, and risk-profile export file. Keep
`.env.staging` and the export out of version control. The browser bundle uses
same-origin `/api/v1` and derives `wss://` from the public HTTPS origin.

Before the first deployment to a populated database, back up Postgres and run
the canonical reconciliation preview and apply commands using the release API
image during a maintenance window. From the extracted bundle directory, after
setting `.env.staging`, run:

```bash
export IMAGE_TAG=<release-commit-sha>
docker compose --env-file .env.staging -f compose.staging.yml pull
docker compose --env-file .env.staging -f compose.staging.yml up -d postgres redis
docker compose --env-file .env.staging -f compose.staging.yml run --rm migrate
docker compose --env-file .env.staging -f compose.staging.yml run --rm --no-deps api python -m ingestion.reconcile
docker compose --env-file .env.staging -f compose.staging.yml run --rm --no-deps api python -m ingestion.reconcile --apply
```

For an empty database, migrations run automatically as a one-shot Compose
service before the API starts. Postgres and Redis health checks gate startup,
and the worker waits for a healthy API. The staging worker runs ingestion once
per cycle and waits five minutes after each attempt, including failed attempts.

Run from the extracted bundle directory:

```bash
bash scripts/deploy_staging.sh <release-commit-sha> https://staging.example.com
```

The script validates Compose, pulls the immutable images, starts the stack,
waits for health, and checks `/health`, `/api/v1/events`, and
`/api/v1/risk-profile/clusters`. Caddy obtains and
renews TLS certificates for `SITE_DOMAIN` and forwards `/api/` and `/ws/` to
the API. Its certificate state and Postgres data use persistent Docker volumes.
The old release SHA is the rollback target: rerun the script with that SHA after
checking schema compatibility. Restore the database backup if a migration or
data reconciliation must be undone. Review `docker compose -f compose.staging.yml
ps` and service logs when health checks fail.

## Epic 2 realtime channel (Person B)

Start Redis and the API, then open the dashboard. `GET /api/v1/subscribe` checks
broker connectivity; the dashboard shows LIVE only while its socket is open.
The Nginx configuration forwards `/ws/` with WebSocket upgrade headers.
Container API/worker Redis and database addresses use Compose service names.

For a custom browser API host, set `VITE_API_BASE_URL` in `web/.env.local`.
The WebSocket URL is derived from that API base using ws/wss and `/ws/events`.
An explicit `VITE_WS_URL=wss://your-host/ws/events` override is also supported in
that file. Restart Vite after environment edits.

The scheduler passes committed canonical event changes to the publisher.
The browser also refreshes the REST event list every 30 seconds.

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

## Import static layers (Epic 3)

Start PostGIS, install backend dependencies, and apply migration `0003`:

```bash
docker compose up -d postgres redis
backend/.venv/bin/pip install -e 'backend[dev]'
(cd backend && .venv/bin/alembic upgrade head)
```

Obtain reviewed source files using `docs/data-sources.md`. From the repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/import_fault_lines.py \
  data/fault_lines/gem_active_faults_harmonized.geojson \
  --source gem \
  --source-url https://github.com/GEMScienceTools/gem-global-active-faults \
  --license-name CC-BY-SA-4.0 --dataset-version YOUR_SOURCE_COMMIT --dry-run
```

Repeat without `--dry-run` to persist the validated snapshot. Use `--source phivolcs`
for reviewed atlas vectors, supplying their source URL, version and license/permission.
For volcano polygons add `--kind volcano_zones`. The command accepts `.geojson`, `.json`
or `.shp` with its sibling files; PDF digitization is a separate GIS task.

A refresh atomically replaces that source in the selected layer, preserving other
sources. Use complete snapshots, not partial updates. Stable identifiers survive
reimport; obsolete features are removed. Invalid or empty imports retain prior data.
Concurrent refreshes serialize using a transaction advisory lock.

Enable **Fault lines** or **Volcano zones** in the dashboard. Loading, empty and retry
states appear independently of live events; source attribution accompanies loaded layers.
Changing basemaps restores the current overlays and visibility settings.

Smoke check `/api/v1/faults` and `/api/v1/volcano-zones` after import. Verify source names,
versions, counts and geometry against the source map. An empty response means no
reference features have been imported, not that an area has no hazard.

For PowerShell, set `$env:PYTHONPATH = "backend"`, use the backend virtual environment's
`Scripts/python.exe`, and pass the same CLI arguments on one line.

Rollback code only after exporting imported data if needed: migration downgrade to
`0002` drops both reference tables.

For this working session a validated 155-feature GEM subset is available locally at
`data/fault_lines/local/gem-ph.geojson`, with source/subset SHA-256 checksums and provenance
in `gem-ph.metadata.json`. It is intentionally ignored by Git. Use it as the CLI input
with `--dataset-version downloaded-2026-09-10` after starting PostGIS.
