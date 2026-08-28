import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

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
            sys.executable,
            "-m",
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
    admin_engine.dispose()


@pytest.fixture(autouse=True)
def clean_hazard_events(migrated_engine):
    with migrated_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE hazard_events RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def client(migrated_engine):
    def override_get_db_session():
        with Session(migrated_engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.pop(get_db_session, None)
