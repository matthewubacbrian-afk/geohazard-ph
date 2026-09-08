from types import SimpleNamespace

from ingestion import scheduler


def test_scheduler_runs_usgs_and_phivolcs_ingest(monkeypatch):
    settings = SimpleNamespace()
    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(scheduler, "fetch_recent_events", lambda settings: ["usgs"])
    monkeypatch.setattr(
        scheduler,
        "fetch_phivolcs_events",
        lambda settings: ["phivolcs", "phivolcs-2"],
    )
    ingested = []

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: SessionContext())
    monkeypatch.setattr(
        scheduler,
        "ingest_events",
        lambda session, events: ingested.append(events) or len(events),
    )

    assert scheduler.run_usgs_ingest() == (1, 1)
    assert scheduler.run_phivolcs_ingest() == (2, 2)
    assert ingested == [["usgs"], ["phivolcs", "phivolcs-2"]]