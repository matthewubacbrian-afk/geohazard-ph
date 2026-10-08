import signal
import threading
from types import SimpleNamespace

import pytest

from ingestion import scheduler


@pytest.fixture(autouse=True)
def preserve_signal_handlers():
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    yield
    for sig, handler in previous.items():
        signal.signal(sig, handler)


def test_scheduler_default_wait_can_be_interrupted(monkeypatch):
    stop_event = threading.Event()
    cycles = []
    waits = []
    monkeypatch.setattr(scheduler, "run_cycle", lambda: cycles.append(True))

    def interrupted_wait(seconds):
        waits.append(seconds)
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return stop_event.is_set()

    def uninterruptible_sleep(seconds):
        pytest.fail("Worker uses uninterruptible sleep during shutdown")

    monkeypatch.setattr(stop_event, "wait", interrupted_wait)
    monkeypatch.setattr("time.sleep", uninterruptible_sleep)
    scheduler.main(
        stop_event=stop_event,
        settings=SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=None),
    )
    assert cycles == [True]
    assert waits == [60]
    assert stop_event.is_set()


def test_scheduler_honors_configured_cycle_limit(monkeypatch):
    cycles = []
    monkeypatch.setattr(scheduler, "run_cycle", lambda: cycles.append(True))

    def unexpected_sleep(seconds):
        pytest.fail("Worker did not stop at the configured cycle limit")

    scheduler.main(
        sleep_fn=unexpected_sleep,
        settings=SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=1),
    )
    assert cycles == [True]


def test_scheduler_restores_signal_handlers(monkeypatch):
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    monkeypatch.setattr(scheduler, "run_cycle", lambda: None)
    scheduler.main(
        max_cycles=1,
        settings=SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=None),
    )
    assert {sig: signal.getsignal(sig) for sig in previous} == previous


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
    callbacks = []

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: SessionContext())

    def fake_ingest(session, events, on_committed=None):
        ingested.append(events)
        callbacks.append(on_committed)
        if on_committed is not None:
            on_committed(["published"])
        return len(events)

    monkeypatch.setattr(scheduler, "ingest_events", fake_ingest)
    monkeypatch.setattr(scheduler, "publish", lambda changes: changes)

    assert scheduler.run_usgs_ingest() == (1, 1)
    assert scheduler.run_phivolcs_ingest() == (2, 2)
    assert ingested == [["usgs"], ["phivolcs", "phivolcs-2"]]
    assert callbacks == [scheduler.publish, scheduler.publish]


def test_scheduler_polling_runs_repeated_cycles(monkeypatch):
    settings = SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=None)
    usgs_calls = []
    phivolcs_calls = []

    def fetch_usgs(_settings):
        usgs_calls.append(True)
        return ["usgs"]

    def fetch_phivolcs(_settings):
        phivolcs_calls.append(True)
        return ["phivolcs"]

    monkeypatch.setattr(scheduler, "fetch_recent_events", fetch_usgs)
    monkeypatch.setattr(scheduler, "fetch_phivolcs_events", fetch_phivolcs)

    ingested = []

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: SessionContext())

    def fake_ingest(session, events, on_committed=None):
        ingested.append(events)
        if on_committed is not None:
            on_committed(["published"])
        return len(events)

    monkeypatch.setattr(scheduler, "ingest_events", fake_ingest)
    monkeypatch.setattr(scheduler, "publish", lambda changes: changes)

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    stop_event = threading.Event()
    scheduler.main(
        sleep_fn=fake_sleep,
        stop_event=stop_event,
        max_cycles=3,
        settings=settings,
    )

    assert len(usgs_calls) == 3
    assert len(phivolcs_calls) == 3
    assert len(sleep_calls) == 2
    assert all(s == 60 for s in sleep_calls)
    assert ingested == [["usgs"], ["phivolcs"], ["usgs"], ["phivolcs"], ["usgs"], ["phivolcs"]]


def test_scheduler_graceful_shutdown_on_stop_event(monkeypatch):
    settings = SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=None)
    usgs_calls = []
    phivolcs_calls = []

    monkeypatch.setattr(scheduler, "fetch_recent_events", lambda _s: usgs_calls.append(True) or ["usgs"])
    monkeypatch.setattr(
        scheduler, "fetch_phivolcs_events", lambda _s: phivolcs_calls.append(True) or ["phivolcs"]
    )

    ingested = []

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: SessionContext())

    def fake_ingest(session, events, on_committed=None):
        ingested.append(events)
        if on_committed is not None:
            on_committed(["published"])
        return len(events)

    monkeypatch.setattr(scheduler, "ingest_events", fake_ingest)
    monkeypatch.setattr(scheduler, "publish", lambda changes: changes)

    sleep_calls = []

    stop_event = threading.Event()

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        stop_event.set()

    scheduler.main(
        sleep_fn=fake_sleep,
        stop_event=stop_event,
        max_cycles=None,
        settings=settings,
    )

    assert len(usgs_calls) == 1
    assert len(phivolcs_calls) == 1
    assert len(sleep_calls) == 1
    assert len(ingested) == 2


def test_scheduler_source_failure_does_not_block_other(monkeypatch):
    settings = SimpleNamespace(ingest_poll_interval_seconds=60, ingest_max_cycles=None)
    usgs_calls = []
    phivolcs_calls = []

    def fetch_usgs(_settings):
        usgs_calls.append(True)
        raise RuntimeError("usgs failed")

    def fetch_phivolcs(_settings):
        phivolcs_calls.append(True)
        return ["phivolcs"]

    monkeypatch.setattr(scheduler, "fetch_recent_events", fetch_usgs)
    monkeypatch.setattr(scheduler, "fetch_phivolcs_events", fetch_phivolcs)

    ingested = []

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: SessionContext())

    def fake_ingest(session, events, on_committed=None):
        ingested.append(events)
        if on_committed is not None:
            on_committed(["published"])
        return len(events)

    monkeypatch.setattr(scheduler, "ingest_events", fake_ingest)
    monkeypatch.setattr(scheduler, "publish", lambda changes: changes)

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    stop_event = threading.Event()

    scheduler.main(
        sleep_fn=fake_sleep,
        stop_event=stop_event,
        max_cycles=1,
        settings=settings,
    )

    assert len(usgs_calls) == 1
    assert len(phivolcs_calls) == 1
    assert len(ingested) == 1
    assert ingested[0] == ["phivolcs"]
    assert len(sleep_calls) == 0
