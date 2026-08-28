from app.core.db import SessionLocal, engine, get_db_session


def test_engine_and_session_local_expose_sqlalchemy_url():
    assert str(engine.url).startswith("postgresql")
    assert SessionLocal.kw["bind"] is engine


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
