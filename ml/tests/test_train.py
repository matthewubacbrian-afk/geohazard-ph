import json
from shutil import copyfile

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

    assert train_module.main(["--offline"]) == 0
    assert captured["download"] is False


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
