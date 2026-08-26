import json
from pathlib import Path

from ml.train import run_training


def test_run_training_from_existing_csvs_writes_artifacts(tmp_path):
    result = run_training(
        phivolcs_paths=[Path("tests/fixtures/phivolcs_sample.csv")],
        usgs_paths=[Path("tests/fixtures/usgs_sample.csv")],
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
