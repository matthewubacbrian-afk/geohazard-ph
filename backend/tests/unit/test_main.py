"""Unit tests for the FastAPI application wiring."""

from fastapi.middleware.cors import CORSMiddleware

from app.main import app


def test_cors_middleware_registered() -> None:
    middleware_classes = {m.cls for m in app.user_middleware}
    assert CORSMiddleware in middleware_classes