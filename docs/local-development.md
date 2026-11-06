# Local Development

Reviewed: 2026-11-06. For the complete Windows dependency, environment and startup
sequence, use the [README quick start](../README.md#run-the-project-locally-windows).
For hosted staging use [deployment operations](free-split-deployment.md), not the
local Compose commands below. This reconciliation did not rerun a full fresh local setup.

## Quick Start

The POSIX-shell examples below assume dependencies/settings are already prepared
and a virtual environment exists at `backend/.venv`. From the repository root:

```bash
docker compose up -d postgres redis
until docker compose exec -T postgres pg_isready -U geohazard -d geohazard >/dev/null 2>&1; do
  sleep 2
done
```

Run migrations separately after PostgreSQL is ready, usually only once for a
new database:

```bash
cd backend
.venv/bin/alembic upgrade head
```

Load or refresh USGS and PHIVOLCS earthquake data separately when needed:

```bash
cd backend
INGEST_MAX_CYCLES=1 .venv/bin/python -m ingestion.scheduler
```

## Start API And Web App

Open two new terminals and run one command in each:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd web
npm run dev
```

Open <http://localhost:5173>. API docs are at <http://localhost:8000/docs>.

Run each example from its stated directory in a fresh terminal. These commands
use `backend/.venv`; an existing root-level environment instead needs
`../.venv/bin/...` from `backend/`. Windows uses `.venv\Scripts\...`; follow the
README rather than mixing POSIX and PowerShell syntax.

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
