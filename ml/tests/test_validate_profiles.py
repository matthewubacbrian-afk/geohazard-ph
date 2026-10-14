import json
from pathlib import Path
from shutil import copyfile

import pytest
from conftest import FIXTURES

from ml.features import RegionFeatures
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


def test_label_stability_runs_seed_and_leave_one_out_comparisons():
    from ml.validate_profiles import _label_stability

    rows = [
        RegionFeatures("A", 10, 4.0, 5.0, 10.0, 1.0),
        RegionFeatures("B", 20, 4.5, 6.0, 20.0, 2.0),
        RegionFeatures("C", 30, 5.0, 7.0, 30.0, 3.0),
        RegionFeatures("D", 40, 5.5, 8.0, 40.0, 4.0),
    ]
    saved_labels = {"A": "Low", "B": "Moderate", "C": "Moderate", "D": "High"}

    stability = _label_stability(rows, saved_labels, [])

    assert stability["saved_labels"] == saved_labels
    assert stability["seed_sweep"]["seeds"] == list(range(20))
    assert stability["seed_sweep"]["fit_count"] == 20
    assert set(stability["seed_sweep"]["change_count_by_region"]) == set(saved_labels)
    assert stability["leave_one_region_out"]["fit_count"] == 4
    assert stability["leave_one_region_out"]["comparisons_per_region"] == {
        name: 3 for name in saved_labels
    }
    assert stability["shared_window_refit"]["unavailable_reason"] == "insufficient_regions"
    assert saved_labels == {"A": "Low", "B": "Moderate", "C": "Moderate", "D": "High"}


def test_label_stability_refits_shared_window_features():
    from ml.validate_profiles import _label_stability

    rows = [
        RegionFeatures("A", 10, 4.0, 5.0, 10.0, 1.0),
        RegionFeatures("B", 20, 4.5, 6.0, 20.0, 2.0),
        RegionFeatures("C", 30, 5.0, 7.0, 30.0, 3.0),
    ]
    saved_labels = {"A": "Low", "B": "Moderate", "C": "High"}
    stability = _label_stability(rows, saved_labels, rows[:2])

    assert stability["shared_window_refit"]["unavailable_reason"] is None
    assert stability["shared_window_refit"]["included_regions"] == ["A", "B"]
    assert set(stability["shared_window_refit"]["labels"]) == {"A", "B"}
    assert isinstance(stability["shared_window_refit"]["change_count"], int)


def test_sparse_region_sensitivity_uses_shared_window_breakpoints(monkeypatch):
    from types import SimpleNamespace

    import ml.validate_profiles as validation

    counts = [
        {"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 2}},
        {"region_name": "B", "shared_window_count_by_source": {"phivolcs": 2, "usgs": 2}},
        {"region_name": "C", "shared_window_count_by_source": {"phivolcs": 3, "usgs": 3}},
    ]
    features = [
        RegionFeatures("A", 3, 4.0, 5.0, 10.0, 1.0),
        RegionFeatures("B", 4, 4.5, 6.0, 20.0, 2.0),
        RegionFeatures("C", 6, 5.0, 7.0, 30.0, 3.0),
    ]
    saved = {"A": "Low", "B": "Moderate", "C": "Moderate"}
    fit_sizes = []

    def fake_fit(rows, k_values, random_state):
        names = [row.region_name for row in rows]
        fit_sizes.append(len(names))
        labels = {"A": "Low", "B": "Moderate", "C": "High"}
        return SimpleNamespace(risk_labels={name: labels[name] for name in names})

    monkeypatch.setattr(validation, "fit_kmeans", fake_fit)
    result = validation._sparse_region_sensitivity(counts, saved, features)

    assert result["count_basis"] == "combined_sources_in_shared_window"
    assert result["thresholds_are_policy"] is False
    scenarios = result["scenarios"]
    assert [item["minimum_shared_window_events"] for item in scenarios] == [0, 4, 5, 7]
    assert scenarios[1]["included_regions"] == ["B", "C"]
    assert scenarios[1]["excluded_regions"] == ["A"]
    assert scenarios[1]["changed_regions"] == ["C"]
    assert scenarios[1]["change_count"] == 1
    assert scenarios[1]["exclusion_reason_by_region"] == {
        "A": "below_minimum_event_count"
    }
    assert scenarios[-1]["labels"] is None
    assert scenarios[-1]["unavailable_reason"] == "insufficient_regions"
    assert fit_sizes == [3, 2]


def test_sparse_region_sensitivity_treats_missing_coverage_as_zero():
    from ml.validate_profiles import _sparse_region_sensitivity

    result = _sparse_region_sensitivity(
        [{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 0}}],
        {"A": "Low", "No events": "Moderate"},
        [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
    )

    first = result["scenarios"][0]
    assert first["excluded_regions"] == ["No events"]
    assert first["exclusion_reason_by_region"] == {
        "No events": "no_shared_window_observations"
    }


@pytest.mark.parametrize(
    "coverage, saved, features",
    [
        (
            [{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1}}],
            {"A": "Low"},
            [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
        ),
        (
            [{"region_name": "A", "shared_window_count_by_source": {"phivolcs": -1, "usgs": 2}}],
            {"A": "Low"},
            [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
        ),
        (
            [{"region_name": "B", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 0}}],
            {"A": "Low"},
            [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
        ),
        (
            [{"region_name": "A", "shared_window_count_by_source": {"phivolcs": 1, "usgs": 1}}],
            {"A": "Low"},
            [RegionFeatures("A", 1, 4.0, 5.0, 10.0, 1.0)],
        ),
    ],
)
def test_sparse_region_sensitivity_rejects_malformed_counts(coverage, saved, features):
    from ml.validate_profiles import _sparse_region_sensitivity

    with pytest.raises(ValueError):
        _sparse_region_sensitivity(coverage, saved, features)


def test_cli_writes_json_and_markdown_on_success(
    saved_bundle: tuple[Path, Path, Path], tmp_path: Path
):
    from ml.validate_profiles import main

    artifact_dir, phivolcs, usgs = saved_bundle
    output_dir = tmp_path / "report"

    assert main([
        "--artifact-dir", str(artifact_dir),
        "--phivolcs-csv", str(phivolcs),
        "--usgs-csv", str(usgs),
        "--output-dir", str(output_dir),
    ]) == 0

    payload = json.loads((output_dir / "validation-report.json").read_text(encoding="utf-8"))
    markdown = (output_dir / "validation-report.md").read_text(encoding="utf-8")
    assert payload["review_state"] == "requires_domain_review"
    sensitivity = payload["sparse_region_sensitivity"]
    assert sensitivity["thresholds_are_policy"] is False
    assert sensitivity["count_basis"] == "combined_sources_in_shared_window"
    assert sensitivity["scenarios"][0]["minimum_shared_window_events"] == 0
    assert "Sparse-region cutoff sensitivity" in markdown
    assert "not a policy cutoff" in markdown.lower()
    assert payload["boundary_sha256"]
    assert payload["assignment_rule"]["max_offshore_km"] == 100.0
    assert "source_coverage" in payload
    assert "label_stability" in payload
    assert payload["label_stability"]["comparison_parameters"] == {
        "k_candidates": [3, 4, 5],
        "shared_window_random_state": 42,
        "seed_sweep_random_states": list(range(20)),
        "leave_one_region_out_random_state": 42,
        "baseline_training_k_candidates": None,
        "baseline_training_random_state": None,
        "parameter_match_verified": False,
    }
    assert any("training settings" in item for item in payload["limitations"])
    assert "training settings" in markdown.lower()
    assert "requires domain review" in markdown.lower()
    assert "Bicol Region" in markdown
    assert "Regional observation spans" in markdown
    assert "Seed" in markdown
    assert "(seeds 0-19)" in markdown
    assert "n/a" in markdown
    assert str(tmp_path) not in (output_dir / "validation-report.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in markdown


def test_cli_does_not_create_output_when_inputs_fail(
    saved_bundle: tuple[Path, Path, Path], tmp_path: Path, capsys
):
    from ml.validate_profiles import main

    artifact_dir, phivolcs, usgs = saved_bundle
    output_dir = tmp_path / "report"
    usgs.write_text(usgs.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert main([
        "--artifact-dir", str(artifact_dir),
        "--phivolcs-csv", str(phivolcs),
        "--usgs-csv", str(usgs),
        "--output-dir", str(output_dir),
    ]) == 1
    assert "input_files" in capsys.readouterr().err
    assert not output_dir.exists()


@pytest.mark.parametrize("child", [False, True])
def test_cli_rejects_output_inside_held_bundle(
    saved_bundle: tuple[Path, Path, Path], child: bool, capsys
):
    from ml.validate_profiles import main

    artifact_dir, phivolcs, usgs = saved_bundle
    output_dir = artifact_dir / "nested" if child else artifact_dir

    assert main([
        "--artifact-dir", str(artifact_dir),
        "--phivolcs-csv", str(phivolcs),
        "--usgs-csv", str(usgs),
        "--output-dir", str(output_dir),
    ]) == 1
    assert "output-dir" in capsys.readouterr().err
    assert not (output_dir / "validation-report.json").exists()
    assert not (output_dir / "validation-report.md").exists()
