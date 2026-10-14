import json
from pathlib import Path
from shutil import copyfile

import pytest
from conftest import FIXTURES

from ml.train import run_training


@pytest.fixture
def saved_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    phivolcs = tmp_path / "phivolcs.csv"
    usgs = tmp_path / "usgs.csv"
    copyfile(FIXTURES / "phivolcs_sample.csv", phivolcs)
    copyfile(FIXTURES / "usgs_sample.csv", usgs)
    bundle = run_training(
        phivolcs_paths=[phivolcs],
        usgs_paths=[usgs],
        artifact_dir=tmp_path / "artifacts",
        artifact_version="v-test",
        download=False,
        k_values=[2],
    )
    return bundle.artifact_dir, phivolcs, usgs


def test_build_validation_report_verifies_saved_inputs(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    report = build_validation_report(artifact_dir, [phivolcs], [usgs])

    assert report["artifact_version"] == "v-test"
    assert report["review_state"] == "requires_domain_review"
    assert len(report["input_files"]) == 2


def test_build_validation_report_rejects_changed_source(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    phivolcs.write_text(phivolcs.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="input_files"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_boundary_hash(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    metadata_path = artifact_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["region_assignment"]["boundary_sha256"] = "invalid"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="boundary_sha256"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_source_count(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    metadata_path = artifact_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_reports"]["phivolcs"]["accepted"] += 1
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="source_reports"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_assignment_count(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    metadata_path = artifact_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["region_assignment"]["assigned_by_source"]["usgs"] += 1
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="assigned_by_source"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_duplicate_path(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle

    with pytest.raises(ValueError, match="more than once"):
        build_validation_report(artifact_dir, [phivolcs], [usgs, phivolcs])


def test_build_validation_report_rejects_missing_file(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    usgs.unlink()

    with pytest.raises(ValueError, match="not found"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_missing_artifact(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    (artifact_dir / "region_features.csv").unlink()

    with pytest.raises(ValueError, match="region_features.csv"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_build_validation_report_rejects_malformed_metadata(saved_bundle: tuple[Path, Path, Path]):
    from ml.validate_profiles import build_validation_report

    artifact_dir, phivolcs, usgs = saved_bundle
    metadata_path = artifact_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("model_version")
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="model_version"):
        build_validation_report(artifact_dir, [phivolcs], [usgs])


def test_coverage_uses_inclusive_shared_window_and_sorts_regions():
    from ml.validate_profiles import _coverage

    rows = [
        {"region_name": "Bicol Region", "source": "phivolcs", "occurred_at": "2024-01-01T00:00:00Z"},
        {"region_name": "Bicol Region", "source": "phivolcs", "occurred_at": "2024-01-03T00:00:00Z"},
        {"region_name": "Eastern Visayas", "source": "usgs", "occurred_at": "2024-01-04T00:00:00Z"},
        {"region_name": "Bicol Region", "source": "usgs", "occurred_at": "2024-01-02T00:00:00Z"},
    ]

    coverage = _coverage(rows)

    assert coverage["source_coverage"]["phivolcs"] == {
        "assigned_count": 2,
        "first_occurred_at": "2024-01-01T00:00:00+00:00",
        "last_occurred_at": "2024-01-03T00:00:00+00:00",
    }
    assert coverage["shared_window"] == {
        "start": "2024-01-02T00:00:00+00:00",
        "end": "2024-01-03T00:00:00+00:00",
        "available": True,
        "unavailable_reason": None,
    }
    assert [row["region_name"] for row in coverage["regions"]] == [
        "Bicol Region", "Eastern Visayas"
    ]
    assert coverage["regions"][0]["shared_window_count_by_source"] == {
        "phivolcs": 1,
        "usgs": 1,
    }
    assert coverage["regions"][1]["assigned_by_source"] == {"phivolcs": 0, "usgs": 1}
    assert coverage["regions"][1]["shared_window_count_by_source"] == {
        "phivolcs": 0,
        "usgs": 0,
    }


def test_coverage_reports_no_shared_window():
    from ml.validate_profiles import _coverage

    coverage = _coverage([
        {"region_name": "Bicol Region", "source": "phivolcs", "occurred_at": "2024-01-01T00:00:00Z"},
        {"region_name": "Bicol Region", "source": "usgs", "occurred_at": "2024-02-01T00:00:00Z"},
    ])

    assert coverage["shared_window"]["available"] is False
    assert coverage["shared_window"]["unavailable_reason"] == "no_shared_observation_window"
    assert coverage["regions"][0]["shared_window_count_by_source"] == {
        "phivolcs": 0,
        "usgs": 0,
    }
