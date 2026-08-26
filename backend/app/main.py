from fastapi import FastAPI

from app.api.v1 import alerts, events, faults, hazards, risk_profile, subscribe, volcanoes
from app.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.project_name, version="0.1.0")

app.include_router(events.router, prefix="/api/v1")
app.include_router(hazards.router, prefix="/api/v1")
app.include_router(faults.router, prefix="/api/v1")
app.include_router(volcanoes.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(subscribe.router, prefix="/api/v1")
app.include_router(risk_profile.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "geohazard-api"}
