from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests

from app.config import Settings
from ingestion.sources.phivolcs_volcano import (
    PhivolcsFetchError,
    PhivolcsParseError,
    fetch_volcano_bulletins,
    parse_volcano_bulletins,
)

HTML = (Path(__file__).resolve().parents[1] / "fixtures/phivolcs_volcano.html").read_text()
NOW = datetime(2026, 9, 8, 9, tzinfo=UTC)


def test_saved_listing_preserves_levels_links_and_local_bulletin_time():
    rows = {v.name: v for v in parse_volcano_bulletins(HTML, Settings().phivolcs_volcano_url, NOW)}
    assert len(rows) == 5
    assert rows["Pinatubo"].current_alert_level == 0
    assert rows["Pinatubo"].bulletin_at is None
    assert rows["Mayon"].bulletin_at == datetime(2026, 9, 7, 16, tzinfo=UTC)
    assert "bid=16738" in str(rows["Mayon"].bulletin_url)
    assert rows["Taal"].source == "phivolcs"
    assert rows["Taal"].retrieved_at == NOW


@pytest.mark.parametrize(
    "html",
    ["<html>maintenance</html>", HTML.replace("Taal - 1", "Taal - 9")],
    ids=["missing-markup", "invalid-alert"],
)
def test_changed_or_invalid_source_fails_visibly(html):
    with pytest.raises(PhivolcsParseError):
        parse_volcano_bulletins(html, Settings().phivolcs_volcano_url, NOW)


def test_network_failure_is_distinct_from_parse_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("private details")

    monkeypatch.setattr(requests, "get", fail)
    with pytest.raises(PhivolcsFetchError):
        fetch_volcano_bulletins(Settings())
