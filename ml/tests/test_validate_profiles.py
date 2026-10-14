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
