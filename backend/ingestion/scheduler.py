import logging

from app.config import get_settings
from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.services.events_publisher import publish
from app.services.ingest import ingest_events
from ingestion.sources.phivolcs_earthquake import fetch_recent_events as fetch_phivolcs_events
from ingestion.sources.usgs import fetch_recent_events

logger = logging.getLogger(__name__)


def run_usgs_ingest() -> tuple[int, int]:
    settings = get_settings()
    events = fetch_recent_events(settings)
    with SessionLocal() as session:
        processed = ingest_events(session, events, on_committed=publish)
    return len(events), processed


def run_phivolcs_ingest() -> tuple[int, int]:
    settings = get_settings()
    events = fetch_phivolcs_events(settings)
    with SessionLocal() as session:
        processed = ingest_events(session, events, on_committed=publish)
    return len(events), processed


def main() -> None:
    configure_logging()
    usgs_fetched, usgs_processed = run_usgs_ingest()
    logger.info(
        "USGS ingest complete",
        extra={"source": "usgs", "fetched": usgs_fetched, "processed": usgs_processed},
    )
    phivolcs_fetched, phivolcs_processed = run_phivolcs_ingest()
    logger.info(
        "PHIVOLCS ingest complete",
        extra={
            "source": "phivolcs",
            "fetched": phivolcs_fetched,
            "processed": phivolcs_processed,
        },
    )


if __name__ == "__main__":
    main()
