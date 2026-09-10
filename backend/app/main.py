from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    alerts,
    events,
    faults,
    hazards,
    realtime,
    risk_profile,
    subscribe,
    volcano_zones,
    volcanoes,
)
from app.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.services.volcanoes import VolcanoFeedUnavailable

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.project_name, version="0.1.0")
register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/v1")
app.include_router(hazards.router, prefix="/api/v1")
app.include_router(faults.router, prefix="/api/v1")
app.include_router(volcano_zones.router, prefix="/api/v1")
app.include_router(volcanoes.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(subscribe.router, prefix="/api/v1")
app.include_router(risk_profile.router, prefix="/api/v1")
app.include_router(realtime.router)


@app.exception_handler(VolcanoFeedUnavailable)
async def volcano_feed_unavailable(_request: Request, _exc: VolcanoFeedUnavailable) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "volcano_feed_unavailable",
                "message": "Volcano bulletins temporarily unavailable",
                "status": 503,
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "geohazard-api"}
