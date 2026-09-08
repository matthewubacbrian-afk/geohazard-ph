from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.services.dedup import match_and_link


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, _statement):
        return FakeResult(self.rows)


def make_row(source, *, latitude=14.5, longitude=121.0, magnitude=5.0, offset_seconds=0):
    occurred_at = datetime(2026, 8, 27, 12, 0, tzinfo=UTC) + timedelta(seconds=offset_seconds)
    return SimpleNamespace(
        id=uuid4(),
        hazard_type="earthquake",
        source=source,
        latitude=latitude,
        longitude=longitude,
        magnitude=magnitude,
        occurred_at=occurred_at,
        created_at=occurred_at,
        canonical_id=None,
        is_primary=None,
        match_confidence=None,
    )


def test_matching_sources_share_one_canonical_event_and_primary():
    usgs = make_row("usgs")
    phivolcs = make_row("phivolcs", offset_seconds=30)

    match_and_link(FakeSession([usgs, phivolcs]))

    assert usgs.canonical_id == phivolcs.canonical_id
    assert [usgs.is_primary, phivolcs.is_primary] == [False, True]


def test_nearby_aftershock_sequence_is_not_merged_when_magnitude_differs():
    usgs = make_row("usgs", magnitude=5.0)
    phivolcs = make_row("phivolcs", magnitude=5.51, offset_seconds=30)

    match_and_link(FakeSession([usgs, phivolcs]))

    assert usgs.canonical_id != phivolcs.canonical_id
    assert usgs.is_primary is True
    assert phivolcs.is_primary is True


def test_late_phivolcs_arrival_reorders_primary_deterministically():
    usgs = make_row("usgs")
    phivolcs = make_row("phivolcs", offset_seconds=30)
    usgs.canonical_id = usgs.id
    usgs.is_primary = True

    match_and_link(FakeSession([usgs, phivolcs]))

    assert usgs.canonical_id == phivolcs.canonical_id
    assert usgs.is_primary is False
    assert phivolcs.is_primary is True


def test_matching_rejects_distance_outside_tolerance():
    usgs = make_row("usgs")
    phivolcs = make_row("phivolcs", latitude=14.55)

    match_and_link(FakeSession([usgs, phivolcs]))

    assert usgs.canonical_id != phivolcs.canonical_id


def test_matching_rejects_magnitude_outside_tolerance():
    usgs = make_row("usgs")
    phivolcs = make_row("phivolcs", magnitude=5.51)

    match_and_link(FakeSession([usgs, phivolcs]))

    assert usgs.canonical_id != phivolcs.canonical_id