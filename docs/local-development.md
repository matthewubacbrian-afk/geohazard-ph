# Local Development

## Quick Start

Run this once from the repository root:

## Special problem (me problem (nate))
sudo systemctl stop postgresql 2>/dev/null || true 

```bash
docker compose up -d postgres redis
until docker exec geohazard-ph-postgres-1 pg_isready -U geohazard -d geohazard >/dev/null 2>&1; do
  sleep 2
done
```

Run migrations separately after PostgreSQL is ready, usually only once for a
new database:

```bash
cd backend
../.venv/bin/alembic upgrade head
```

Load or refresh USGS and PHIVOLCS earthquake data separately when needed:

```bash
cd backend
../.venv/bin/python -m ingestion.scheduler
```

## Start API And Web App

Open two new terminals and run one command in each:

```bash
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd web
npm run dev
```

Open <http://localhost:5173>. API docs are at <http://localhost:8000/docs>.

The virtual environment is at the repository root, so commands run from
`backend/` use `../.venv/bin/...`.

## Verify the API

```bash
curl -sS -D - http://localhost:8000/health \
  -H 'Origin: http://localhost:5173'

curl -sS http://localhost:8000/api/v1/events \
  -H 'Origin: http://localhost:5173'
```

The health response should be `200 OK` and include:

```text
access-control-allow-origin: http://localhost:5173
```

The events response is an array. An empty array means the API is working but
the ingestion job has not populated the database yet.

## PHIVOLCS TLS Note

The PHIVOLCS earthquake and volcano adapters use the checked-in GlobalSign
intermediate with the standard CA bundle to verify the source's incomplete
certificate chain. `PHIVOLCS_SSL_VERIFY=false` is no longer supported or needed.
