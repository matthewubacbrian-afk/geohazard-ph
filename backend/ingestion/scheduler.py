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
