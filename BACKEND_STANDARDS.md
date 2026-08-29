# Backend Standards

**Project**: GeoHazard PH
**Scope**: All code under `backend/` — FastAPI API modules, Pydantic schemas, SQLAlchemy models, service layer, and ingestion workers.

This is the stack-specific contract for the backend. Read it before writing or editing any code in `backend/`. It builds on `CODING_STANDARDS.md` and does not replace it; where the two differ, the more specific rule in this document applies for backend code.

Related contracts:
- `docs/api-contracts.md` — endpoint naming, request/response shapes, error envelope, versioning.
- `docs/error-handling-and-logging.md` — cross-cutting error taxonomy and logging rules.
- `docs/testing-standards.md` — what "done" means for backend tests.

---

## Table Of Contents

1. Layer Responsibilities
2. Module Layout
3. FastAPI Route Modules
4. Dependency Injection
5. Configuration
6. Service Layer
7. Pydantic Schemas
8. SQLAlchemy Models
9. Ingestion
10. Error Handling
11. Logging
12. Dates And Coordinates
13. Testing
14. New Backend Feature Checklist
15. Known Deviations

---

## 1. Layer Responsibilities

- **Routes** (`app/api/v1/*`) handle HTTP concerns only: parameter parsing, dependency injection, and status-code selection. They delegate behavior to services.
- **Services** (`app/services/*`) hold business rules, queries, and external integrations. They never import FastAPI.
- **Schemas** (`app/schemas/*`) define input and output contracts with Pydantic. They hold validation, not behavior.
- **Models** (`app/models/*`) represent database persistence only, using SQLAlchemy 2.0 declarative `Mapped`/`mapped_column` style.
- **Core** (`app/core/*`) holds cross-cutting primitives: database session, logging, security. One file per primitive.

A route function is thin. If a route body grows past a few lines of delegation, move the logic into a service and keep the route as the adapter.

## 2. Module Layout

```text
backend/
  app/
    api/
      deps.py       # Re-exported FastAPI dependencies
      v1/           # Versioned route modules, one resource per file
    core/           # DB, Redis, logging, security primitives
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request and response schemas
    services/       # Business logic and reusable operations
  ingestion/
    sources/        # One adapter per external source
    scraping/       # HTML parsing helpers
    scheduler.py    # Scheduler entrypoints
    validation.py   # Source-payload validation helpers
  db/
    migrations/     # Alembic version files
    seed/           # Static seed data
  tests/
    unit/           # DB-free unit tests
    integration/    # Tests against PostGIS/prod-shaped services
    fixtures/       # Shared test payloads
```

## 3. FastAPI Route Modules

### Router shape

- One `APIRouter` per resource module in `backend/app/api/v1/`.
- Router prefix is the plural resource name; do not repeat the version segment (the version is applied at include time).
- Route decorators use `""` as the root path, never `"/"`.
- Route functions take typed parameters and optional `Depends` arguments; no positional session threading.

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.hazard_event import HazardEvent
from app.services.events import list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[HazardEvent])
def get_events(
    since: datetime | None = Query(default=None, description="Return events at/after this time"),
    db: Session = Depends(get_db_session),
) -> list[HazardEvent]:
    return list_events(db, since=since)
```

### Registration

Register routers once in `backend/app/main.py` with the shared version prefix:

```python
app.include_router(events.router, prefix="/api/v1")
```

### Route ordering

Static route segments must be declared before path parameters in the same router. A `"/summary"` route must precede any `"/{resource_id}"` route, or FastAPI will shadow the static one.

### Route rules

- Always declare `response_model` for public responses.
- Keep route bodies as delegation; all query building belongs in services.
- Use `Depends(get_db_session)` for the session — never construct a `SessionLocal()` inside a route.
- Declare query parameters with `Query(...)` instead of raw function arguments so they are documented in the OpenAPI schema.
- Return the schema objects the response model expects; do not return ORM rows directly.

## 4. Dependency Injection

- Expose shared dependencies from `backend/app/api/deps.py` and import them into route modules from there.
- The database session dependency is `get_db_session`, a generator yielding a `Session` and guaranteeing close in `finally`.

```python
def get_db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- Tests replace dependencies with `app.dependency_overrides[get_db_session] = override`. Overrides must be popped after the test (use a fixture that cleans up).
- Do not depend on global module state in routes; receive everything through arguments or `Depends`.

## 5. Configuration

- Define all settings in one `Settings` class in `backend/app/config.py` using pydantic-settings `BaseSettings`.
- Export a cached accessor using `@lru_cache` on `get_settings()`. Route and service code always calls `get_settings()` — never reconstructs `Settings()`.

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- Prefix any new environment variables with a project-meaningful name (for example `PH_BBOX`, `RISK_PROFILE_EXPORT_PATH`) and document them in `.env.example`.
- Keep secrets as environment variables only. Never hardcode credentials in code, defaults, or tests.
- Tests that change settings must call `get_settings.cache_clear()` after `monkeypatch.setenv(...)` so the cached instance reloads.

## 6. Service Layer

- One module per capability in `backend/app/services/`. Name it after the resource or capability (`events.py`, `ingest.py`, `dedup.py`).
- Functions take a `Session` as the first argument when they touch persistence, followed by explicit parameters.
- Return Pydantic schemas or plain typed values. Services define private `_to_schema` mappers that convert ORM rows to schemas; the mapper lives with the service, not the route.
- Raise domain exceptions for expected failure modes (for example `RiskProfileNotFound`). Convert them to `HTTPException` at the route boundary.
- Do not log inside services beyond what error-handling-and-logging.md prescribes; leave HTTP concerns to routes.

```python
def list_events(session: Session, since: datetime | None = None) -> list[HazardEvent]:
    stmt = select(HazardEventORM).order_by(HazardEventORM.occurred_at.desc())
    if since is not None:
        stmt = stmt.where(HazardEventORM.occurred_at >= since)
    rows = session.execute(stmt).scalars().all()
    return [_to_schema(row) for row in rows]
```

## 7. Pydantic Schemas

- Define public input and output models in `backend/app/schemas/`, one module per resource.
- Field names are `snake_case` and match the wire format. Validate output with Pydantic field constraints (`Field(ge=-90, le=90)` for latitude).
- Use `Literal` types for closed value sets such as `hazard_type`.
- Use `str | None = None` for optional nullable fields — never `Optional[...]` with implicit default.
- Add a new schema model when a response shape differs from an existing one; do not reuse a schema with unused fields.

```python
class EventSummary(BaseModel):
    region_name: str | None = None
    event_count: int = 0
    avg_magnitude: float | None = None
    max_magnitude: float | None = None
    latest_occurred_at: datetime | None = None
```

## 8. SQLAlchemy Models

- Define models with `Mapped[...]` and `mapped_column`. Use `timezone=True` on all `DateTime` columns.
- Table name is the snake_case plural of the resource; constraint and index names follow `uq_<table>_<columns>`, `ck_<table>_<column>`, `idx_<table>_<column>`.
- Store geospatial data in a `Geography(geometry_type="POINT", srid=4326)` column (`location`); keep plain `latitude`/`longitude` numeric columns for simple reads and queries.
- Add a `UniqueConstraint` for deduplication keys such as `(source, external_id)`.
- Every schema change ships with an Alembic migration under `backend/db/migrations/versions/`; never edit an applied migration after merge.

```python
__tablename__ = "hazard_events"
__table_args__ = (
    UniqueConstraint("source", "external_id", name="uq_hazard_events_source_external_id"),
    Index("idx_hazard_events_occurred_at", "occurred_at"),
    Index("idx_hazard_events_geo", "location"),
)
```

## 9. Ingestion

- One adapter module per external source under `backend/ingestion/sources/` (`usgs.py`, `phivolcs_earthquake.py`, `gvp.py`, ...).
- Adapters are unreliable I/O boundaries: validate source payload shape before mapping to internal schemas, and preserve source identifiers and timestamps.
- Distinguish internet, parsing, and persistence failures; callers must be able to tell them apart.
- Scheduler entrypoints live in `backend/ingestion/scheduler.py` and are the only place intended for command-style runs. They compose fetch, parse, dedup, and ingest through services.
- Unit tests for adapters never require a database or network; use fixtures and fakes (see `docs/testing-standards.md`).

## 10. Error Handling

Follow `docs/error-handling-and-logging.md`. Summary for backend routes:

- Services raise domain exceptions; routes translate them to `HTTPException` with a stable status code.
- Expected failures map to 4xx; unexpected failures surface as 500 via a global handler and are logged with a stack trace, never returned verbatim.
- Error responses use the envelope defined in `docs/error-handling-and-logging.md`. Do not return ad-hoc error dicts.
- Never expose credentials, file paths with secrets, or raw tokens in error messages or response bodies.

## 11. Logging

Follow `docs/error-handling-and-logging.md`. Summary:

- Use the standard `logging` module with `logger = logging.getLogger(__name__)` in every module that logs.
- Replace operational `print()` calls in workers and scheduler entrypoints with logger calls.
- Keep emitted fields key-value and structured; do not embed user-supplied data in the log line without escaping, and never log secrets.

## 12. Dates And Coordinates

- Serialize all datetimes as ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SSZ` or `Z`-equivalent offset).
- Store `DateTime(timezone=True)`; parse source timestamps into UTC at the ingestion boundary.
- Coordinates are decimal degrees: `latitude` is latitude, `longitude` is longitude, in that order everywhere. GeoJSON `coordinates` arrays are `[longitude, latitude]`; infer nothing from context.

## 13. Testing

Follow `docs/testing-standards.md`. Summary for backend:

- Unit tests run DB-free and live in `backend/tests/unit/test_<module>.py`.
- Integration tests live in `backend/tests/integration/test_<module>.py` and use the PostGIS fixtures from `backend/tests/integration/conftest.py` (`client`, `migrated_engine`).
- Cover service behavior and route behavior for every new endpoint.

## 14. New Backend Feature Checklist

- [ ] Read `AGENTS.md`, `CODING_STANDARDS.md`, and this document.
- [ ] Check existing modules for the closest local pattern.
- [ ] Add schema models in `backend/app/schemas/`.
- [ ] Add or update the service module in `backend/app/services/`.
- [ ] Add the route module in `backend/app/api/v1/` and register it in `main.py`.
- [ ] Add the Alembic migration when persistence changes.
- [ ] Add unit tests (DB-free) and integration tests where the endpoint touches the DB.
- [ ] Run `pytest -v` from `backend/`, plus `python scripts\verify_structure.py` when structure changes.

## 15. Known Deviations

The following current code does not yet conform to this contract. These are tracked as backlog items in `docs/superpowers/plans/2026-08-29-standards-gap-remediation.md`; new code must conform, and this list shrinks one item at a time.

- `backend/ingestion/scheduler.py` uses `print()` instead of the `logging` module.
- No global exception handler or error envelope is registered yet; endpoints return ad-hoc error shapes.
- `backend/app/core/logging.py` (`.configure_logging`) exists but is not imported or called anywhere.
- Several route modules and services return placeholder data (`[]`, stub dicts) in `backend/app/api/v1/*` and `backend/ingestion/sources/*`.
- `app/services/risk_profile.py` and a few routes call `get_settings()` multiple times per request instead of once; acceptable for small modules but consolidate when the module grows.