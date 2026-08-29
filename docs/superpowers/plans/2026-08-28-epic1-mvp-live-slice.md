# Epic 1 MVP Live Earthquake Slice — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make real USGS earthquake data flow `USGS feed → ingestion → PostGIS (hazard_events) → GET /api/v1/events → web map markers`, replacing the hardcoded sample and relevant stubs.

**Architecture:** A bottom-up vertical slice. First the PostGIS-backed ORM model + Alembic migration; then the DB session plumbing; then the USGS ingestion worker (fetch → parse → dedup → upsert) and the scheduler entrypoint; then wire `GET /api/v1/events` to the DB; finally render live markers in the web `MapView`. Layers depend on earlier ones via small, typed interfaces.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, GeoAlchemy2, Alembic, psycopg3, PostgreSQL + PostGIS (Docker), requests, pytest; web: React 18, TypeScript, Vite, MapLibre GL, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-28-epic1-mvp-live-slice-design.md`

## Global Constraints

- All human/agent changes follow `CODING_STANDARDS.md` and `AGENTS.md`.
- Conventional Commits; imperative, lowercase after type (e.g. `feat: add usgs ingestion worker`).
- Python line length 100; use type hints on public functions.
- Backend imports resolve from `backend/`; `pytest` runs from `backend/`.
- Do not commit credentials, generated artifacts, or large datasets.
- Treat geohazard data-correctness bugs as P0; never imply prediction/official warning.
- Preserve `source` and `external_id` for deduplication.
- Parser/fetch **unit** tests must not require a database or network; **integration** tests use Dockerized PostGIS.
- USGS caches feeds ~1 min (recent); do not poll faster than that.
- Verification commands: `pytest -v` (backend), `npm test` + `npm run build` (web), `python scripts\verify_structure.py`, `git diff --check`.

---

### Task 1: SQLAlchemy ORM model + Base

**Files:**
- Modify: `backend/app/models/hazard_event.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/unit/test_hazard_event_model.py` (create)

**Interfaces:**
- Produces:
  - `class HazardEvent(Base)` — SQLAlchemy declarative model for table `hazard_events`.
  - `Base = declarative_base()` — exposed from `backend/app/models` (import as `from app.models import Base, HazardEvent`).
  - `HazardEvent` columns: `id` (Mapped[uuid.UUID], server_default `uuid4`), `hazard_type` (str), `source` (str), `external_id` (str | None), `magnitude` (float | None), `depth_km` (float | None), `latitude` (float), `longitude` (float), `place_name` (str), `alert_level` (str | None), `location` (Geography(Point, 4326)), `raw_payload` (dict | None), `occurred_at` (datetime), `created_at` (datetime, server_default `now()`). UniqueConstraint on `(source, external_id)`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_hazard_event_model.py`:

```python
from sqlalchemy import inspect

from app.models import HazardEvent


def test_hazard_event_model_table_and_columns():
    columns = {c.name: c for c in inspect(HazardEvent).columns}

    assert HazardEvent.__tablename__ == "hazard_events"
    for col in [
        "id",
        "hazard_type",
        "source",
        "external_id",
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
        "place_name",
        "alert_level",
        "location",
        "raw_payload",
        "occurred_at",
        "created_at",
    ]:
        assert col in columns


def test_hazard_event_unique_constraint_on_source_external_id():
    constraints = [
        c
        for c in inspect(HazardEvent).table_constraints
        if c.name == "uq_hazard_events_source_external_id"
    ]
    assert len(constraints) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_hazard_event_model.py -v` from `backend/`
Expected: FAIL (import error / no `HazardEvent` attributes).

- [ ] **Step 3: Write the ORM model**

Replace `backend/app/models/hazard_event.py` with:

```python
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HazardEvent(Base):
    __tablename__ = "hazard_events"
    __table_args__ = (
        Index("uq_hazard_events_source_external_id", "source", "external_id", unique=True),
        Index("idx_hazard_events_occurred_at", "occurred_at"),
        Index("idx_hazard_events_geo", "location"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_type: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    magnitude: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    depth_km: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    place_name: Mapped[str] = mapped_column(Text)
    alert_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
```

Replace `backend/app/models/__init__.py` with:

```python
from app.models.hazard_event import Base, HazardEvent

__all__ = ["Base", "HazardEvent"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_hazard_event_model.py -v` from `backend/`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/hazard_event.py backend/app/models/__init__.py backend/tests/unit/test_hazard_event_model.py
git commit -m "feat: add HazardEvent ORM model"
```

---

### Task 2: DB engine, session, and settings

**Files:**
- Modify: `backend/app/core/db.py`
- Modify: `backend/app/config.py`
- Test: `backend/tests/unit/test_db_engine.py` (create)

**Interfaces:**
- Consumes: `Settings` from `app.config` (fields below).
- Produces:
  - `def get_settings() -> Settings` (cached, from `app.config`) — adds `usgs_feed_url: str` and `ph_bbox: tuple[float, float, float, float]`.
  - `from app.core.db import engine, SessionLocal, get_db_session` — `get_db_session()` is a generator yielding a `Session` and guaranteeing close; usable as a FastAPI dependency and overridable via `app.dependency_overrides`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_db_engine.py`:

```python
from app.core.db import SessionLocal, engine
from app.core.db import get_db_session


def test_engine_and_session_local_expose_sqlalchemy_url():
    assert str(engine.url).startswith("postgresql")


def test_get_db_session_is_a_generator():
    gen = get_db_session()
    session = next(gen)
    try:
        assert session is not None
    finally:
        gen.close()


def test_default_ph_bbox_is_within_philippines():
    from app.config import get_settings

    west, south, east, north = get_settings().ph_bbox
    assert south >= 4.0 and north <= 22.0
    assert west >= 116.0 and east <= 128.0
```

Note: `backend/tests/unit/test_events_api.py` currently imports in a way that may conflict; this task only adds the unit test. `engine` will be created from `DATABASE_URL` even if the DB is unreachable (connection is lazy), so this unit test does not require a running DB.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_db_engine.py -v` from `backend/`
Expected: FAIL (import error — `db.py` has no `engine`, `SessionLocal`; config lacks `ph_bbox`).

- [ ] **Step 3: Implement settings + db module**

Modify `backend/app/config.py` to add settings (keep existing fields):

```python
class Settings(BaseSettings):
    project_name: str = "GeoHazard PH"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard"
    redis_url: str = "redis://localhost:6379/0"
    risk_profile_export_path: Path = Path("tests/fixtures/risk_profiles.json")
    usgs_feed_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    ph_bbox: tuple[float, float, float, float] = (116.0, 4.0, 128.0, 22.0)

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
```

Replace `backend/app/core/db.py` with:

```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["engine", "SessionLocal", "init_db", "get_db_session", "Base"]
```

Note: `init_db()` is provided as a convenience for local dev/seeding and integration tests; production schema is managed by Alembic (Task 3).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_db_engine.py -v` from `backend/`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/db.py backend/app/config.py backend/tests/unit/test_db_engine.py
git commit -m "feat: add database engine and session"
```

---

### Task 3: Alembic migration for hazard_events

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/db/migrations/versions/0001_create_hazard_events.py`
- Test: `backend/tests/integration/conftest.py` (create) — shared integration harness used from Task 5 onward.

**Interfaces:**
- Consumes: `Settings.database_url` (env `DATABASE_URL`), `app.models.Base.metadata`.
- Produces:
  - Alembic config able to run `alembic upgrade head` against `alias` URL supplied via `-x db_url=...` (used by tests) or env `DATABASE_URL`.
  - Migration revision `0001_create_hazard_events` creating the `hazard_events` table with the PostGIS `location` column.

- [ ] **Step 1: Add alembic dependency and create env.py**

Modify `backend/pyproject.toml` runtime dependencies — add `"alembic>=1.13.0"`.

Create `backend/alembic/env.py`:

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    x_arg = context.get_x_argument(as_dictionary=True)
    if "db_url" in x_arg:
        return x_arg["db_url"]
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create `backend/alembic/script.py.mako` (standard template):

```
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 2: Create the migration by hand**

Create `backend/db/migrations/versions/0001_create_hazard_events.py`:

```python
"""create hazard_events table

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "hazard_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("hazard_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("magnitude", sa.Numeric(), nullable=True),
        sa.Column("depth_km", sa.Numeric(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("place_name", sa.Text(), nullable=False),
        sa.Column("alert_level", sa.Text(), nullable=True),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("raw_payload", JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source", "external_id", name="uq_hazard_events_source_external_id"),
    )
    op.create_index("idx_hazard_events_occurred_at", "hazard_events", ["occurred_at"])
    op.create_index("idx_hazard_events_geo", "hazard_events", ["location"])


def downgrade() -> None:
    op.drop_index("idx_hazard_events_geo", table_name="hazard_events")
    op.drop_index("idx_hazard_events_occurred_at", table_name="hazard_events")
    op.drop_table("hazard_events")
```

- [ ] **Step 3: Create integration test harness**

Create `backend/tests/integration/conftest.py`:

```python
import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.db import get_db_session
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[2]
BASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard_test",
)


@pytest.fixture(scope="session")
def migrated_engine():
    admin_engine = create_engine(BASE_URL)
    with admin_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    subprocess.run(
        [
            "alembic",
            "-x",
            f"db_url={BASE_URL}",
            "upgrade",
            "head",
        ],
        cwd=BACKEND_DIR,
        check=True,
    )
    yield admin_engine


@pytest.fixture(scope="session")
def client(migrated_engine):
    def override_get_db_session():
        from sqlalchemy.orm import Session

        with Session(migrated_engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.pop(get_db_session, None)
```

Note: If `alembic` is not on PATH in the test environment, the harness can instead invoke
`python -m alembic ...`. Adjust the command if needed to keep CI passing.

- [ ] **Step 4: Verify migration applies against a running PostGIS**

Ensure Docker PostGIS is up (`docker compose up postgres`), create the test DB, then run:

```bash
# from backend/
createdb -h localhost -U geohazard geohazard_test   # or use psql
alembic -x db_url=postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard_test upgrade head
alembic -x db_url=postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard_test current
```

Run: `pytest tests/integration/conftest.py -v` from `backend/`
Expected: conftest loads without error (no test collected is fine).

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/alembic/env.py backend/alembic/script.py.mako backend/db/migrations/versions/0001_create_hazard_events.py backend/tests/integration/conftest.py
git commit -m "feat: add alembic migration for hazard_events"
```

Note: committing after the conftest exists is intentional so Tasks 4–7 build on a shared harness. If the DB is not available locally, still commit (implementation artifacts are complete); the integration tests are verified in CI with a PostGIS service.

---

### Task 4: USGS fetch + parser + ingest service + scheduler

**Files:**
- Modify: `backend/ingestion/sources/usgs.py`
- Create: `backend/app/services/ingest.py`
- Modify: `backend/ingestion/scheduler.py`
- Test: `backend/tests/unit/test_usgs_fetch.py` (create), `backend/tests/integration/test_usgs_ingest.py` (create)

**Interfaces:**
- Consumes: `HazardEvent` (Pydantic, from `app.schemas.hazard_event`), `app.config.Settings.usgs_feed_url` / `ph_bbox`, `app.services.dedup.dedup_key`, `app.models.HazardEvent` (ORM), `Session` from `sqlalchemy.orm`, `get_settings()` from `app.config`.
- Produces:
  - `ingestion.sources.usgs.parse_usgs_feature(feature: dict) -> HazardEvent` (existing, kept — enriches with `raw_payload` handling).
  - `ingestion.sources.usgs.fetch_recent_events(settings: Settings, *, session: requests.Session | None = None) -> list[HazardEvent]` — GETs `settings.usgs_feed_url` with `minlatitude/maxlatitude/minlongitude/maxlongitude` from `settings.ph_bbox` + `eventtype=earthquake`, raises `USGSFetchError` on non-200, parses each feature with `parse_usgs_feature`.
  - `class USGSFetchError(RuntimeError)` — raised on HTTP failure.
  - `app.services.ingest.ingest_usgs_events(session: Session, events: list[HazardEvent]) -> int` — upserts by `(source, external_id)`; returns number of rows inserted/updated.
  - `ingestion.scheduler.run_usgs_ingest() -> None` — fetches and ingests, prints a summary; entrypoint used by docker `worker`.

- [ ] **Step 1: Write failing unit test for fetch**

Create `backend/tests/unit/test_usgs_fetch.py`:

```python
from app.config import get_settings
from ingestion.sources.usgs import USGSFetchError, fetch_recent_events


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class FakeBadResponse:
    status_code = 500

    def raise_for_status(self):
        raise RuntimeError("boom")


def test_fetch_recent_events_parses_fixture(monkeypatch):
    import requests

    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "abc123",
                "properties": {
                    "mag": 4.8,
                    "place": "12 km E of Sample, Philippines",
                    "time": 1787788800000,
                },
                "geometry": {"coordinates": [121.0, 14.5, 35.0]},
            }
        ],
    }

    captured = {}

    def fake_get(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse(payload)

    monkeypatch.setattr(requests, "get", fake_get)

    events = fetch_recent_events(get_settings())

    assert len(events) == 1
    assert events[0].source == "usgs"
    assert events[0].latitude == 14.5
    assert captured["params"]["minlatitude"] == 4.0


def test_fetch_recent_events_raises_on_http_error(monkeypatch):
    import requests

    def fake_get(url, params=None, **kwargs):
        return FakeBadResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    try:
        fetch_recent_events(get_settings())
    except Exception as exc:
        assert "USGS" in str(exc) or isinstance(exc, USGSFetchError)
    else:
        raise AssertionError("expected an error")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_usgs_fetch.py -v` from `backend/`
Expected: FAIL (ImportError — `fetch_recent_events`/`USGSFetchError` not defined).

- [ ] **Step 3: Implement USGS fetch**

Replace `backend/ingestion/sources/usgs.py` with:

```python
from datetime import UTC, datetime

import requests

from app.config import Settings
from app.schemas.hazard_event import HazardEvent


class USGSFetchError(RuntimeError):
    pass


def parse_usgs_feature(feature: dict) -> HazardEvent:
    properties = feature["properties"]
    longitude, latitude, depth_km = feature["geometry"]["coordinates"]
    return HazardEvent(
        id=f"usgs-{feature['id']}",
        hazard_type="earthquake",
        source="usgs",
        external_id=feature["id"],
        magnitude=properties.get("mag"),
        depth_km=depth_km,
        latitude=latitude,
        longitude=longitude,
        place_name=properties.get("place") or "Unknown location",
        occurred_at=datetime.fromtimestamp(properties["time"] / 1000, tz=UTC),
    )


def fetch_recent_events(
    settings: Settings, *, session: requests.Session | None = None
) -> list[HazardEvent]:
    west, south, east, north = settings.ph_bbox
    params = {
        "minlatitude": south,
        "maxlatitude": north,
        "minlongitude": west,
        "maxlongitude": east,
        "eventtype": "earthquake",
        "format": "geojson",
        "orderby": "time",
        "limit": 200,
    }
    http = session or requests
    response = http.get(settings.usgs_feed_url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise USGSFetchError(f"USGS feed request failed: {exc}") from exc
    data = response.json()
    return [parse_usgs_feature(f) for f in data.get("features", [])]
```

- [ ] **Step 4: Write failing ingest/upsert test**

Create `backend/tests/integration/test_usgs_ingest.py`:

```python
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.ingest import ingest_usgs_events


def _make_event(external_id: str, magnitude: float) -> HazardEvent:
    return HazardEvent(
        id=f"usgs-{external_id}",
        hazard_type="earthquake",
        source="usgs",
        external_id=external_id,
        magnitude=magnitude,
        depth_km=30.0,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample, Philippines",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
    )


def test_ingest_usgs_events_upserts_deduplicates(migrated_engine):
    with Session(migrated_engine) as session:
        ingested = ingest_usgs_events(session, [_make_event("e1", 4.0), _make_event("e1", 4.5)])
        assert ingested == 1

        # Upsert updated the magnitude rather than inserting a second row.
        rows = session.execute(select(HazardEventORM)).scalars().all()
        assert len(rows) == 1
        assert float(rows[0].magnitude) == 4.5
```

- [ ] **Step 5: Run test to verify it fails**

Run: `pytest tests/integration/test_usgs_ingest.py -v` from `backend/`
Expected: FAIL (ImportError — `ingest_usgs_events` not defined).

- [ ] **Step 6: Implement ingest service + scheduler**

Create `backend/app/services/ingest.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.dedup import dedup_key


def ingest_usgs_events(session: Session, events: list[HazardEvent]) -> int:
    if not events:
        return 0

    keys = [dedup_key(event) for event in events]
    existing = session.execute(
        select(HazardEventORM).where(
            HazardEventORM.source.in_([k[0] for k in keys]),
            HazardEventORM.external_id.in_([k[1] for k in keys]),
        )
    ).scalars().all()
    by_key = {dedup_key(row): row for row in existing}

    changed = 0
    for event in events:
        key = dedup_key(event)
        row = by_key.get(key)
        if row is None:
            session.add(
                HazardEventORM(
                    hazard_type=event.hazard_type,
                    source=event.source,
                    external_id=event.external_id,
                    magnitude=event.magnitude,
                    depth_km=event.depth_km,
                    latitude=event.latitude,
                    longitude=event.longitude,
                    place_name=event.place_name,
                    alert_level=event.alert_level,
                    location=f"SRID=4326;POINT({event.longitude} {event.latitude})",
                    occurred_at=event.occurred_at,
                )
            )
            changed += 1
        else:
            _update_row(row, event)
            changed += 1
    session.commit()
    return changed


def _update_row(row: HazardEventORM, event: HazardEvent) -> None:
    row.magnitude = event.magnitude
    row.depth_km = event.depth_km
    row.place_name = event.place_name
    row.alert_level = event.alert_level
    row.occurred_at = event.occurred_at
```

Modify `backend/ingestion/scheduler.py`:

```python
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.db import SessionLocal
from app.services.ingest import ingest_usgs_events
from ingestion.sources.usgs import fetch_recent_events


def run_usgs_ingest() -> tuple[int, int]:
    settings = get_settings()
    events = fetch_recent_events(settings)
    with SessionLocal() as session:
        processed = ingest_usgs_events(session, events)
    return len(events), processed


def main() -> None:
    fetched, processed = run_usgs_ingest()
    print(f"USGS ingest complete: fetched={fetched}, processed={processed}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Run tests to verify they pass**

Run from `backend/`:
`pytest tests/unit/test_usgs_fetch.py -v`
Expected: PASS.
`pytest tests/integration/test_usgs_ingest.py -v` (with PostGIS test DB running)
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/ingestion/sources/usgs.py backend/app/services/ingest.py backend/ingestion/scheduler.py backend/app/config.py backend/tests/unit/test_usgs_fetch.py backend/tests/integration/test_usgs_ingest.py
git commit -m "feat: add USGS ingestion worker"
```

---

### Task 5: DB-backed events API + service

**Files:**
- Create: `backend/app/services/events.py`
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/api/v1/events.py`
- Test: `backend/tests/integration/test_events_api.py` (replace)
- Test: `backend/tests/unit/test_events_service.py` (create)

**Interfaces:**
- Consumes: `Session` from `sqlalchemy.orm`, `HazardEventORM.Dict` types from `app.models`, `get_db_session` from `app.core.db`, `HazardEvent` Pydantic schema.
- Produces:
  - `app.services.events.list_events(session: Session, since: datetime | None = None) -> list[HazardEvent]` — queries `hazard_events`, newest `occurred_at` first, optional `since` filter, mapping ORM rows to Pydantic `HazardEvent`.
  - `GET /api/v1/events?since=<ISO8601>` returns `list[HazardEvent]`.

- [ ] **Step 1: Write failing unit test for the service**

Create `backend/tests/unit/test_events_service.py`:

```python
from app.services import events


def test_events_service_module_exports_list_events():
    assert callable(events.list_events)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_events_service.py -v` from `backend/`
Expected: FAIL (ImportError — `app.services.events` doesn't exist).

- [ ] **Step 3: Implement events service**

Create `backend/app/services/events.py`:

```python
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent


def list_events(session: Session, since: datetime | None = None) -> list[HazardEvent]:
    stmt = select(HazardEventORM).order_by(HazardEventORM.occurred_at.desc())
    if since is not None:
        stmt = stmt.where(HazardEventORM.occurred_at >= since)
    rows = session.execute(stmt).scalars().all()
    return [_to_schema(row) for row in rows]


def _to_schema(row: HazardEventORM) -> HazardEvent:
    return HazardEvent(
        id=f"{row.source}-{row.external_id}" if row.source else str(row.id),
        hazard_type=row.hazard_type,
        source=row.source,
        external_id=row.external_id,
        magnitude=float(row.magnitude) if row.magnitude is not None else None,
        depth_km=float(row.depth_km) if row.depth_km is not None else None,
        latitude=row.latitude,
        longitude=row.longitude,
        place_name=row.place_name,
        occurred_at=row.occurred_at,
        alert_level=row.alert_level,
    )
```

- [ ] **Step 4: Wire deps + endpoint**

Modify `backend/app/api/deps.py`:

```python
from app.core.db import get_db_session

__all__ = ["get_db_session"]
```

(It already re-exports `get_db_session`; no functional change required, but confirm it still points
at the real session from Task 2.)

Replace `backend/app/api/v1/events.py`:

```python
from datetime import datetime

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

- [ ] **Step 5: Replace the integration test**

Replace `backend/tests/integration/test_events_api.py` with:

```python
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM


def test_events_endpoint_returns_db_rows(client, migrated_engine):
    with Session(migrated_engine) as session:
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="live-1",
                magnitude=4.2,
                depth_km=25.0,
                latitude=15.0,
                longitude=120.0,
                place_name="Seeded, Philippines",
                location="SRID=4326;POINT(120.0 15.0)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.commit()

    response = client.get("/api/v1/events")

    assert response.status_code == 200
    bodies = response.json()
    assert any(b["external_id"] == "live-1" for b in bodies)
    assert all("occurred_at" in b for b in bodies)


def test_events_endpoint_filters_by_since(client, migrated_engine):
    response = client.get("/api/v1/events?since=2027-01-01T00:00:00Z")
    assert response.status_code == 200
    assert response.json() == []
```

Note: the integration tests depend on the `client`/`migrated_engine` fixtures from
`backend/tests/integration/conftest.py` (Task 3). `hazard_type` is a `Text` column on the ORM but
the Pydantic schema declares a `Literal`; the ORM does not enforce the Literal, so seeding with
`"earthquake"` is fine.

- [ ] **Step 6: Run tests to verify they pass**

Run from `backend/` (PostGIS test DB running):
`pytest tests/unit/test_events_service.py tests/integration/test_events_api.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/events.py backend/app/api/v1/events.py backend/tests/unit/test_events_service.py backend/tests/integration/test_events_api.py
git commit -m "feat: back events endpoint with PostGIS"
```

---

### Task 6: Web map renders live event markers

**Files:**
- Modify: `web/src/components/map/MapView.tsx`
- Modify: `web/src/pages/Dashboard.tsx` (only if it does not already pass `events` to `MapView` — verify first)
- Test: `web/tests/MapView.test.tsx` (replace)

**Interfaces:**
- Consumes: `HazardEvent[]` prop `events` on `MapView`, plus `web/src/api/client.ts` `fetchEvents` and `web/src/hooks/useEvents.ts` `useEvents()` (already exist).
- Produces: `MapView` that, given `events`, renders a MapLibre map with one circle/symbol per event whose coordinates are `[longitude, latitude]`, and shows explicit empty/error states.

- [ ] **Step 1: Write the failing test**

Replace `web/tests/MapView.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import MapView from '../src/components/map/MapView';

describe('MapView', () => {
  it('shows an empty state when there are no events', () => {
    render(<MapView events={[]} />);
    expect(screen.getByText(/no events/i)).toBeTruthy();
  });
});
```

Note: `@testing-library/react` is **not** currently a dependency. Install it first:

```bash
# from web/
npm install -D @testing-library/react @testing-library/jest-dom
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- MapView` from `web/`
Expected: FAIL (MapView has no "no events" text; testing-library may not render without jsdom config — add a `vitest` environment if needed in `web/vite.config.ts` or a `vitest.config.ts`).

- [ ] **Step 3: Implement MapLibre Marker rendering**

Replace `web/src/components/map/MapView.tsx`:

```tsx
import { useEffect, useRef } from 'react';
import maplibre from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

import type { HazardEvent } from '../../types/hazard';

type MapViewProps = {
  events: HazardEvent[];
};

const PH_CENTER: [number, number] = [122.0, 12.0];

export default function MapView({ events }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibre.Map({
      container: containerRef.current,
      center: PH_CENTER,
      zoom: 5,
      style: 'https://demotiles.maplibre.org/style.json',
    });
    map.on('load', () => {
      map.addSource('events', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: events.map((e) => ({
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [e.longitude, e.latitude] },
            properties: { place: e.place_name, magnitude: e.magnitude ?? null },
          })),
        },
      });
      map.addLayer({
        id: 'event-circles',
        type: 'circle',
        source: 'events',
        paint: {
          'circle-radius': 8,
          'circle-color': '#dc2626',
          'circle-stroke-width': 1,
          'circle-stroke-color': '#ffffff',
        },
      });
    });
    return () => map.remove();
  }, [events]);

  if (events.length === 0) {
    return (
      <section className="map-shell" aria-label="Hazard map">
        <div className="map-empty">No events to display.</div>
      </section>
    );
  }

  return (
    <section className="map-shell" aria-label="Hazard map">
      <div ref={containerRef} className="map-canvas" style={{ width: '100%', height: '400px' }} />
      <div className="map-count">{events.length} events loaded</div>
    </section>
  );
}
```

Note: to keep the component test deterministic and avoid network/WebGL issues in jsdom, guard the
test to assert on the empty-state branch only (already done). The MapLibre branch is covered by
`npm run build` (type-check) and manual QA, per CODING_STANDARDS web testing rules.

- [ ] **Step 4: Verify Dashboard passes events to MapView**

Open `web/src/pages/Dashboard.tsx`. Confirm it calls `useEvents()` and passes `events` to `<MapView events={...} />`. If it does, no change needed. If it does not render `MapView` with events, update it to:

```tsx
import { useEvents } from '../hooks/useEvents';
import MapView from '../components/map/MapView';

export default function Dashboard() {
  const { data: events = [], isLoading, error } = useEvents();
  return (
    <main>
      {isLoading ? <p>Loading events…</p> : error ? <p>Failed to load events.</p> : <MapView events={events} />}
    </main>
  );
}
```

(Match existing imports/JSX style in `Dashboard.tsx`.)

- [ ] **Step 5: Run tests and build**

Run from `web/`:
`npm test`
Expected: PASS.
`npm run build`
Expected: PASS (type-checks MapLibre code).

- [ ] **Step 6: Commit**

```bash
git add web/src/components/map/MapView.tsx web/src/pages/Dashboard.tsx web/tests/MapView.test.tsx web/package.json web/package-lock.json
git commit -m "feat: render live event markers on the map"
```

---

### Task 7: Full verification + docs update

**Files:**
- Modify: `README.md`
- Modify: `docs/data-sources.md`
- Modify: `docs/runbook.md`

**Goal:** Run the complete verification battery and update documentation for the new setup, API, scheduler/workflow, and data-source usage.

- [ ] **Step 1: Run backend tests**

Run from `backend/` (with PostGIS test DB up):
`pytest -v`
Expected: PASS.

- [ ] **Step 2: Run web tests and build**

Run from `web/`:
`npm test`
`npm run build`
Expected: both PASS.

- [ ] **Step 3: Run structure verification and whitespace check**

From repo root:
`python scripts\verify_structure.py`
`git diff --check`
Expected: PASS.

- [ ] **Step 4: Update README.md**

Add a section under setup documenting:
- The USGS ingestion worker: `python -m ingestion.scheduler` runs a one-shot ingest; in Docker, the `worker` service runs it.
- The new `GET /api/v1/events?since=` behavior (DB-backed, newest first).
- That `hazard_events` is managed by Alembic migrations under `backend/db/migrations/versions`.

Keep existing wording/style.

- [ ] **Step 5: Update docs/data-sources.md**

Under the USGS row, note:
- The ingestion worker polls the USGS Earthquakes feed filtered to the PH bounding box.
- `min/max` lat/lon come from `PH_BBOX` config; poll cadence stays ≥ 1 minute to respect USGS caching.
- Attribution: USGS data requires attribution (keep or add a line noting "USGS Earthquake Hazards Program" attribution).

- [ ] **Step 6: Update docs/runbook.md**

Add an "Ingestion & worker" subsection:
- How to run a one-shot ingest locally (`python -m ingestion.scheduler` from `backend/`).
- How to run migrations (`alembic upgrade head` from `backend/`, or `alembic -x db_url=... upgrade head`).
- What to check when the USGS feed is unreachable (USGSFetchError, poll cadence, source status).

- [ ] **Step 7: Commit**

```bash
git add README.md docs/data-sources.md docs/runbook.md
git commit -m "docs: document usgs ingestion and events endpoint"
```

---

## Notes for the executor
- Tasks 1–3 must run in order; Tasks 4–6 depend on the earlier ones' interfaces.
- Integration tests require a running PostGIS. Use `docker compose up postgres` and create the
  `geohazard_test` database first. If CI lacks PostGIS, run those tests there; keep unit tests DB-free.
- `maplibre-gl` is already a web dependency; `@testing-library/react` must be added for the web test.
