import hashlib
import json
from pathlib import Path
from shutil import copyfile

import pytest
from conftest import FIXTURES

from ml.ingest_kaggle import DownloadedDataset
from ml.train import run_training


def test_main_offline_disables_download(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)

    assert train_module.main([
        "--offline",
        "--phivolcs-csv", "phivolcs.csv",
        "--usgs-csv", "usgs.csv",
    ]) == 0
    assert captured["download"] is False
    assert captured["phivolcs_paths"] == [Path("phivolcs.csv")]
    assert captured["usgs_paths"] == [Path("usgs.csv")]


def test_main_forwards_repeated_source_csv_flags(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)

    assert train_module.main([
        "--offline",
        "--phivolcs-csv", "first.csv",
        "--phivolcs-csv", "second.csv",
        "--usgs-csv", "usgs.csv",
    ]) == 0
    assert captured["download"] is False
    assert captured["phivolcs_paths"] == [Path("first.csv"), Path("second.csv")]
    assert captured["usgs_paths"] == [Path("usgs.csv")]


def test_main_offline_without_source_paths_fails(capsys, tmp_path):
    from ml import train as train_module

    assert train_module.main(["--offline", "--artifact-dir", str(tmp_path / "art")]) == 1
    assert "PHIVOLCS and USGS" in capsys.readouterr().err


def test_main_defaults_to_download(monkeypatch, tmp_path):
    from ml import train as train_module

    captured = {}

    def fake_run_training(**kwargs):
        captured.update(kwargs)
        return train_module.TrainingResult(0, tmp_path, "v1")

    monkeypatch.setattr(train_module, "run_training", fake_run_training)

    assert train_module.main([]) == 0
    assert captured["download"] is True


def test_run_training_records_downloaded_dataset_versions(monkeypatch, tmp_path):
    downloaded = [
        DownloadedDataset(
            "bwandowando/philippine-earthquakes-from-phivolcs",
            "PHIVOLCS downloaded sample",
            "CC0: Public Domain",
            tmp_path / "phivolcs",
            12,
        ),
        DownloadedDataset(
            "bwandowando/philippine-earthquakes-1900-2025-from-usgs",
            "USGS downloaded sample",
            "Apache 2.0",
            tmp_path / "usgs",
            31,
        ),
    ]
    for dataset, fixture_name in zip(downloaded, ["phivolcs_sample.csv", "usgs_sample.csv"]):
        dataset.path.mkdir()
        copyfile(FIXTURES / fixture_name, dataset.path / fixture_name)

    monkeypatch.setattr("ml.train.download_datasets", lambda raw_dir: downloaded)

    result = run_training(
        artifact_dir=tmp_path / "art",
        artifact_version="v-test",
        k_values=[2],
        random_state=7,
    )

    assert result.profile_count == 2
    metadata = json.loads(
        (tmp_path / "art" / "v-test" / "metadata.json").read_text(encoding="utf-8")
    )
    assert {entry["slug"]: entry["version"] for entry in metadata["datasets"]} == {
        downloaded[0].slug: 12,
        downloaded[1].slug: 31,
    }
    assert metadata["datasets"] == [
        {
            "slug": dataset.slug,
            "title": dataset.title,
            "license": dataset.license_name,
            "version": dataset.version,
        }
        for dataset in downloaded
    ]
    assert {entry["source"] for entry in metadata["input_files"]} == {"phivolcs", "usgs"}


def test_run_training_from_existing_csvs_writes_artifacts(tmp_path):
    result = run_training(
        phivolcs_paths=[(FIXTURES / "phivolcs_sample.csv")],
        usgs_paths=[(FIXTURES / "usgs_sample.csv")],
        artifact_dir=tmp_path,
        artifact_version="v-test",
        download=False,
        k_values=[2],
        random_state=7,
    )

    assert result.profile_count == 2
    metadata = json.loads((tmp_path / "v-test" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["model_version"] == "v-test"
    assert metadata["datasets"][0]["slug"] == "bwandowando/philippine-earthquakes-from-phivolcs"
    assert all(entry["version"] is None for entry in metadata["datasets"])
    assert "metrics" in metadata
    assert "clustering" in metadata["metrics"]
    assert "classifier" in metadata["metrics"]
    assert metadata["source_reports"] == {
        "phivolcs": {"accepted": 2, "rejected": 0},
        "usgs": {"accepted": 2, "rejected": 0},
    }
    assert metadata["input_files"] == [
        {
            "source": source,
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for source, path in (
            ("phivolcs", FIXTURES / "phivolcs_sample.csv"),
            ("usgs", FIXTURES / "usgs_sample.csv"),
        )
    ]


def test_offline_training_requires_both_sources_before_writing(tmp_path):
    with pytest.raises(ValueError, match="PHIVOLCS and USGS"):
        run_training(
            phivolcs_paths=[FIXTURES / "phivolcs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )

    assert not (tmp_path / "art").exists()


def test_offline_training_rejects_duplicate_source_assignment(tmp_path):
    path = FIXTURES / "phivolcs_sample.csv"
    with pytest.raises(ValueError, match="more than once"):
        run_training(
            phivolcs_paths=[path],
            usgs_paths=[path],
            artifact_dir=tmp_path / "art",
            download=False,
        )

    assert not (tmp_path / "art").exists()


def test_offline_training_rejects_missing_csv(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(ValueError, match="missing.csv"):
        run_training(
            phivolcs_paths=[missing],
            usgs_paths=[FIXTURES / "usgs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )


def test_offline_training_rejects_non_csv_input(tmp_path):
    wrong_type = tmp_path / "input.txt"
    wrong_type.write_text("not a CSV", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a CSV"):
        run_training(
            phivolcs_paths=[wrong_type],
            usgs_paths=[FIXTURES / "usgs_sample.csv"],
            artifact_dir=tmp_path / "art",
            download=False,
        )


def test_download_mode_rejects_explicit_source_paths(tmp_path):
    with pytest.raises(ValueError, match="require offline"):
        run_training(
            phivolcs_paths=[FIXTURES / "phivolcs_sample.csv"],
            artifact_dir=tmp_path / "art",
        )


def test_run_training_uses_labels_from_saved_kmeans_result(tmp_path):
    run_training(
        phivolcs_paths=[(FIXTURES / "phivolcs_sample.csv")],
        usgs_paths=[(FIXTURES / "usgs_sample.csv")],
        artifact_dir=tmp_path,
        artifact_version="v-test",
        download=False,
        k_values=[2],
        random_state=7,
    )

    profiles = json.loads((tmp_path / "v-test" / "risk_profiles.json").read_text(encoding="utf-8"))
    labels_by_cluster: dict[int, set[str]] = {}
    for profile in profiles:
        labels_by_cluster.setdefault(profile["cluster"], set()).add(profile["label"])

    assert all(len(labels) == 1 for labels in labels_by_cluster.values())
