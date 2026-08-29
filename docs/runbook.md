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

## Data Accuracy Concern

1. Treat coordinate, magnitude, alert-level, and deduplication issues as high priority.
2. Preserve raw payloads for reprocessing.
3. Verify against the source site or API before publishing corrections.

## Local Scaffold Check

Run from the repository root:

```bash
python scripts/verify_structure.py
```
