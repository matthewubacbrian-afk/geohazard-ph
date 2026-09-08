from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "GeoHazard PH"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    risk_profile_export_path: Path = Path("tests/fixtures/risk_profiles.json")
    usgs_feed_url: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    phivolcs_earthquake_feed_url: str = "https://earthquake.phivolcs.dost.gov.ph/"
    ph_bbox: tuple[float, float, float, float] = (116.0, 4.0, 128.0, 22.0)
    phivolcs_volcano_url: str = "https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin"
    phivolcs_volcano_timeout_seconds: float = Field(default=15, ge=1, le=60)
    phivolcs_volcano_cache_seconds: int = Field(default=300, ge=60)
    phivolcs_volcano_stale_seconds: int = Field(default=3600, ge=60)

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
