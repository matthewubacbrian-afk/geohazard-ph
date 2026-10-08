import logging
import signal
import threading
from collections.abc import Callable
from typing import Any

from app.config import Settings, get_settings
from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.services.events_publisher import publish
from app.services.ingest import ingest_events
from ingestion.sources.phivolcs_earthquake import (
    fetch_recent_events as fetch_phivolcs_events,
)
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


def run_cycle() -> None:
    try:
        usgs_fetched, usgs_processed = run_usgs_ingest()
        logger.info(
            "USGS ingest complete",
            extra={"source": "usgs", "fetched": usgs_fetched, "processed": usgs_processed},
        )
    except Exception:
        logger.exception("ingest source failed", extra={"source": "usgs"})

    try:
        phivolcs_fetched, phivolcs_processed = run_phivolcs_ingest()
        logger.info(
            "PHIVOLCS ingest complete",
            extra={
                "source": "phivolcs",
                "fetched": phivolcs_fetched,
                "processed": phivolcs_processed,
            },
        )
    except Exception:
        logger.exception("ingest source failed", extra={"source": "phivolcs"})


def main(
    *,
    sleep_fn: Callable[[float], Any] | None = None,
    stop_event: threading.Event | None = None,
    max_cycles: int | None = None,
    settings: Settings | None = None,
) -> None:
    configure_logging()
    effective_stop_event = stop_event or threading.Event()
    effective_settings = settings or get_settings()
    cycle_limit = max_cycles if max_cycles is not None else effective_settings.ingest_max_cycles
    wait = sleep_fn if sleep_fn is not None else effective_stop_event.wait
    interval_seconds = float(effective_settings.ingest_poll_interval_seconds)

    def handle_signal(*_args: Any) -> None:
        if not effective_stop_event.is_set():
            logger.info("ingest worker received shutdown signal")
        effective_stop_event.set()

    previous_handlers = {}
    cycle_count = 0
    logger.info(
        "ingest worker starting",
        extra={"poll_interval_seconds": interval_seconds},
    )

    try:
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGTERM, signal.SIGINT):
                previous_handlers[sig] = signal.signal(sig, handle_signal)
        while not effective_stop_event.is_set():
            run_cycle()
            cycle_count += 1
            if cycle_limit is not None and cycle_count >= cycle_limit:
                break
            if effective_stop_event.is_set():
                break
            wait(interval_seconds)
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        logger.info("ingest worker stopping")


if __name__ == "__main__":
    main()
