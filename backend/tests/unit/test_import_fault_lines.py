import importlib.util
import json
import logging
from pathlib import Path

import pytest


def load_importer():
    path = Path(__file__).resolve().parents[3] / "scripts" / "import_fault_lines.py"
    spec = importlib.util.spec_from_file_location("import_fault_lines", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_geojson(path: Path, *, outside_only: bool = False) -> None:
    inside = {
        "type": "Feature",
        "id": "fault-1",
        "properties": {"name": "Inside fault"},
        "geometry": {"type": "LineString", "coordinates": [[121, 14], [122, 15]]},
    }
    outside = {
        "type": "Feature",
        "id": "fault-2",
        "properties": {"name": "Outside fault"},
        "geometry": {"type": "LineString", "coordinates": [[2, 2], [3, 3]]},
    }
    features = [outside] if outside_only else [inside, outside]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))


def set_arguments(monkeypatch, source_path: Path) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "import_fault_lines.py",
            str(source_path),
            "--source",
            "gem",
            "--source-url",
            "https://example.org/data",
            "--license-name",
            "CC-BY-SA-4.0",
            "--dataset-version",
            "fixture",
            "--dry-run",
        ],
    )


def test_cli_dry_run_logs_coverage_report_without_database(tmp_path, monkeypatch, caplog):
    module = load_importer()
    source_path = tmp_path / "faults.geojson"
    write_geojson(source_path)
    set_arguments(monkeypatch, source_path)
    monkeypatch.setattr(module, "SessionLocal", lambda: pytest.fail("database opened"))
    caplog.set_level(logging.INFO)

    module.main()

    record = next(record for record in caplog.records if record.getMessage() == "Static layer validated")
    assert record.source_feature_count == 2
    assert record.accepted_feature_count == 1
    assert record.excluded_outside_bounds_count == 1
    assert record.accepted_bounds == (121.0, 14.0, 122.0, 15.0)
    assert record.count == 1


def test_cli_rejects_zero_accepted_features_before_database(tmp_path, monkeypatch, caplog):
    module = load_importer()
    source_path = tmp_path / "faults.geojson"
    write_geojson(source_path, outside_only=True)
    set_arguments(monkeypatch, source_path)
    monkeypatch.setattr(module, "SessionLocal", lambda: pytest.fail("database opened"))
    caplog.set_level(logging.INFO)

    with pytest.raises(SystemExit) as exit_info:
        module.main()

    assert exit_info.value.code == 1
    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Static layer validation rejected"
    )
    assert record.source_feature_count == 1
    assert record.accepted_feature_count == 0
    assert record.excluded_outside_bounds_count == 1
    assert record.accepted_bounds is None
    assert record.count == 0
