from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.services.events import list_events, summarize_events


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return FakeScalarResult(self._rows)

    def one(self):
        magnitudes = [float(row.magnitude) for row in self._rows if row.magnitude is not None]
        occurred_at = [row.occurred_at for row in self._rows if row.occurred_at is not None]
        distinct_ids = {str(getattr(row, "canonical_id", None) or row.id) for row in self._rows}
        return SimpleNamespace(
            count=len(distinct_ids),
            avg_mag=sum(magnitudes) / len(magnitudes) if magnitudes else None,
            max_mag=max(magnitudes) if magnitudes else None,
            latest=max(occurred_at) if occurred_at else None,
        )


class FakeSession:
    def __init__(self, rows):
        self._rows = rows
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return FakeExecuteResult(self._rows)


def _row(external_id="live-1"):
    row_id = UUID("12345678-1234-5678-1234-567812345678") if external_id is None else uuid4()
    return SimpleNamespace(
        id=row_id,
        hazard_type="earthquake",
        source="usgs",
        external_id=external_id,
        magnitude=Decimal("4.2"),
        depth_km=Decimal("25.5"),
        latitude=15.0,
        longitude=120.0,
        place_name="Seeded, Philippines",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
        alert_level=None,
        canonical_id=None,
        is_primary=True,
        match_confidence=None,
    )


def test_list_events_maps_rows_to_schema_and_numeric_values():
    events = list_events(FakeSession([_row()]))

    assert len(events) == 1
    assert events[0].id == "usgs-live-1"
    assert events[0].magnitude == 4.2
    assert events[0].depth_km == 25.5
    assert events[0].place_name == "Seeded, Philippines"


def test_list_events_falls_back_to_database_id_without_external_id():
    events = list_events(FakeSession([_row(external_id=None)]))

    assert events[0].id == "12345678-1234-5678-1234-567812345678"


def test_list_events_queries_newest_first_with_optional_since_filter():
    since = datetime(2026, 8, 1, tzinfo=UTC)
    session = FakeSession([])

    list_events(session, since=since)

    statement = str(session.statement)
    assert "hazard_events.occurred_at >=" in statement
    assert "ORDER BY hazard_events.occurred_at DESC" in statement


def test_list_events_defaults_to_primary_rows_and_supports_source_filter():
    session = FakeSession([])

    list_events(session, source="phivolcs")

    statement = str(session.statement)
    assert "hazard_events.is_primary IS true" not in statement
    assert "hazard_events.source = :source_1" in statement


def test_list_events_applies_primary_only_when_no_source_filter():
    session = FakeSession([])

    list_events(session)

    statement = str(session.statement)
    assert "hazard_events.is_primary IS true" in statement


def test_list_events_can_include_duplicate_rows():
    session = FakeSession([])

    list_events(session, include_duplicates=True)

    assert "hazard_events.is_primary IS true" not in str(session.statement)


def test_summarize_events_aggregates_magnitudes_and_count():
    rows = [_row("e1"), _row("e2")]
    rows[1].magnitude = Decimal("5.8")
    rows[1].occurred_at = datetime(2026, 8, 29, tzinfo=UTC)
    summary = summarize_events(
        FakeSession(rows), 116.0, 4.0, 128.0, 22.0, region_name="Test Region"
    )
    assert summary.region_name == "Test Region"
    assert summary.event_count == 2
    assert summary.avg_magnitude == 5.0
    assert summary.max_magnitude == 5.8
    assert summary.latest_occurred_at == datetime(2026, 8, 29, tzinfo=UTC)


def test_summarize_events_returns_none_aggregates_when_no_rows():
    summary = summarize_events(FakeSession([]), 116.0, 4.0, 128.0, 22.0)
    assert summary.event_count == 0
    assert summary.avg_magnitude is None
    assert summary.max_magnitude is None
    assert summary.latest_occurred_at is None


def test_summarize_events_counts_distinct_canonical_ids():
    rows = [_row("e1"), _row("e2")]
    rows[1].canonical_id = rows[0].canonical_id = rows[0].id
    summary = summarize_events(FakeSession(rows), 116.0, 4.0, 128.0, 22.0)
    assert summary.event_count == 1


def test_summarize_events_rounds_average_to_two_decimals():
    rows = [_row("e1"), _row("e2"), _row("e3")]
    rows[1].magnitude = Decimal("4.3")
    rows[2].magnitude = Decimal("4.3")
    summary = summarize_events(FakeSession(rows), 116.0, 4.0, 128.0, 22.0)
    assert summary.avg_magnitude == 4.27
    assert summary.max_magnitude == 4.3
