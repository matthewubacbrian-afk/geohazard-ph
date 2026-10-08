import json
from conftest import FIXTURES

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
