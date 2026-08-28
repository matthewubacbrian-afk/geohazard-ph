from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "GeoHazard PH"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard"
    redis_url: str = "redis://localhost:6379/0"
    risk_profile_export_path: Path = Path("tests/fixtures/risk_profiles.json")
    usgs_feed_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    ph_bbox: tuple[float, float, float, float] = (116.0, 4.0, 128.0, 22.0)

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
