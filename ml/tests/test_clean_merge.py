from pathlib import Path

from ml.clean_merge import load_and_merge_sources, normalize_csv


def test_normalize_csv_maps_phivolcs_headers():
    rows, report = normalize_csv(Path("tests/fixtures/phivolcs_sample.csv"), source="phivolcs")

    assert report.accepted_rows == 2
    assert report.rejected_rows == 0
    assert rows[0]["source"] == "phivolcs"
    assert rows[0]["region_name"] == "Bicol Region"
    assert rows[0]["magnitude"] == 5.1
    assert rows[0]["depth_km"] == 34.0


def test_normalize_csv_maps_usgs_headers():
    rows, report = normalize_csv(Path("tests/fixtures/usgs_sample.csv"), source="usgs")

    assert report.accepted_rows == 2
    assert rows[0]["source_event_id"] == "usgs-001"
    assert rows[1]["region_name"] == "Eastern Visayas"


def test_load_and_merge_sources_deduplicates_overlapping_events():
    rows, reports = load_and_merge_sources(
        phivolcs_paths=[Path("tests/fixtures/phivolcs_sample.csv")],
        usgs_paths=[Path("tests/fixtures/usgs_sample.csv")],
    )

    assert len(rows) == 3
    assert reports["phivolcs"].accepted_rows == 2
    assert reports["usgs"].accepted_rows == 2
