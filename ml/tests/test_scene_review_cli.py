import json
from dataclasses import dataclass
from types import SimpleNamespace

from ml.scene_review import cli
from ml.scene_review.manifest import SufficiencyPolicy
from ml.scene_review.splits import DatasetSplits


@dataclass
class _FakeEvaluation:
    passed_thresholds: bool
    sample_counts: dict
    threshold_failures: tuple = ()


def _policy():
    return SufficiencyPolicy(
        maximum_exclusion_rate=0.25,
        minimum_retained_samples_by_split={"train": 1, "validation": 1, "test": 1},
        required_scene_types_by_split={"train": (), "validation": (), "test": ()},
        minimum_retained_samples_by_scene_type={},
        minimum_retained_groups_by_split={"train": 1, "validation": 1, "test": 1},
        minimum_retained_samples_per_group_by_split={"train": 1, "validation": 1, "test": 1},
        required_group_ids_by_split={"train": (), "validation": (), "test": ()},
    )


def test_cli_commands_report_counts_and_keep_artifact_root_fixed(tmp_path, monkeypatch, capsys):
    records = tuple(SimpleNamespace(image_id=f"private-image-{i}") for i in range(3))
    manifest = SimpleNamespace(records=records, supported_labels=("open_ground",))
    monkeypatch.setattr(cli, "load_manifest", lambda path: manifest)
    monkeypatch.setattr(
        cli,
        "validate_dataset",
        lambda *args, **kwargs: SimpleNamespace(
            image_count=3,
            sufficiency_gate_passed=True,
            sufficiency_gate_reasons=(),
            exclusion_rate=0.0,
            loss_eligible_sample_count=3,
            loss_excluded_sample_count=0,
            split_summaries={},
        ),
    )
    monkeypatch.setattr(
        cli,
        "make_grouped_splits",
        lambda records, seed: DatasetSplits(("a",), ("b",), ("c",)),
    )
    monkeypatch.setattr(cli, "splits_to_json", lambda splits, seed: '{"train_ids":["a"]}')
    splits_file = tmp_path / "splits.json"
    assert cli.main(["split", "--manifest", "m.json", "--data-root", str(tmp_path),
                     "--output", str(splits_file)]) == 0
    assert splits_file.exists()
    assert "private-image" not in capsys.readouterr().out

    assert cli.main(["validate", "--manifest", "m.json", "--data-root", str(tmp_path)]) == 0
    assert "private-image" not in capsys.readouterr().out

    captured = {}
    monkeypatch.setattr(cli, "_read_splits", lambda path: DatasetSplits(("a",), ("b",), ("c",)))
    monkeypatch.setattr(cli, "_read_sufficiency_policy", lambda path: _policy())
    monkeypatch.setattr(
        cli,
        "train_model",
        lambda *args, **kwargs: SimpleNamespace(
            best_epoch=1,
            best_validation_loss=0.25,
            trained_labels=("open_ground",),
            training_metadata={"manifest_sha256": "f" * 64},
        ),
    )
    assert cli.main([
        "train", "--manifest", "m.json", "--data-root", str(tmp_path),
        "--splits", str(splits_file), "--sufficiency-policy", "policy.json",
        "--model-cache", str(tmp_path / "cache"), "--output-dir", str(tmp_path / "run"),
    ]) == 0
    assert "manifest_sha256" not in capsys.readouterr().out

    monkeypatch.setattr(cli, "_read_evaluation_thresholds", lambda path: object())
    monkeypatch.setattr(cli, "_make_evaluation_inputs", lambda *args, **kwargs: (object(), object()))
    monkeypatch.setattr(cli, "SceneReviewDataset", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli,
        "evaluate_model",
        lambda *args, **kwargs: _FakeEvaluation(True, {"evaluated": 3}),
    )
    evaluation_path = tmp_path / "evaluation.json"
    assert cli.main([
        "evaluate", "--manifest", "m.json", "--data-root", str(tmp_path),
        "--splits", str(splits_file), "--sufficiency-policy", "policy.json",
        "--checkpoint", str(tmp_path / "checkpoint"), "--thresholds", "thresholds.json",
        "--output", str(evaluation_path),
    ]) == 0
    assert json.loads(evaluation_path.read_text(encoding="utf-8"))["passed_thresholds"]

    artifact_root = tmp_path / "repo" / "ml" / "model_artifacts" / "scene_review"
    monkeypatch.setattr(cli, "ARTIFACT_ROOT", artifact_root)
    def fake_export(**kwargs):
        captured["root"] = kwargs["output_root"]
        artifact = artifact_root / kwargs["version"]
        (artifact / "model").mkdir(parents=True)
        return artifact

    monkeypatch.setattr(cli, "export_artifact", fake_export)
    metadata_file = tmp_path / "training.json"
    metadata_file.write_text('{"sufficiency_gate_passed":true}', encoding="utf-8")
    assert cli.main([
        "export", "--checkpoint", str(tmp_path / "checkpoint"),
        "--evaluation", str(evaluation_path), "--metadata", str(metadata_file),
        "--version", "v-test",
    ]) == 0
    assert captured["root"] == artifact_root
    assert "private-image" not in capsys.readouterr().out


def test_cli_requires_predeclared_sufficiency_policy_for_training(capsys):
    assert cli.main([
        "train", "--manifest", "manifest.json", "--data-root", ".",
        "--splits", "splits.json", "--model-cache", "cache", "--output-dir", "run",
    ]) == 2
    assert "invalid command arguments" in capsys.readouterr().err.lower()


def test_argparse_errors_do_not_echo_private_argument_values(capsys):
    private_value = r"private-image-id-C:\Users\matth\private\manifest.json"

    assert cli.main([
        "split",
        "--manifest",
        "manifest.json",
        "--data-root",
        ".",
        "--seed",
        private_value,
        "--output",
        "splits.json",
    ]) == 2

    output = capsys.readouterr()
    assert "private-image-id" not in output.out + output.err
    assert "private" not in output.out + output.err
    assert "invalid command arguments" in output.err


def test_cli_help_remains_available(capsys):
    assert cli.main(["--help"]) == 0
    assert "usage: scene-review" in capsys.readouterr().out.lower()


def test_cli_errors_do_not_echo_local_paths_or_record_ids(tmp_path, monkeypatch, capsys):
    private_path = str(tmp_path / "private-manifest.json")
    monkeypatch.setattr(cli, "load_manifest", lambda path: (_ for _ in ()).throw(
        ValueError(f"invalid record private-image at {private_path}")))

    assert cli.main(["validate", "--manifest", private_path, "--data-root", str(tmp_path)]) == 2
    output = capsys.readouterr().out
    assert private_path not in output
    assert "private-image" not in output
    assert "operation failed" in output


def test_validate_refuses_pending_image_rights_without_echoing_evidence(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_manifest", lambda path: object())
    monkeypatch.setattr(
        cli,
        "validate_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("source-private-id has pending rights at https://private.invalid/terms")
        ),
    )

    assert cli.main([
        "validate", "--manifest", "private.json", "--data-root", str(tmp_path)
    ]) == 2
    output = capsys.readouterr().out
    assert "pending" not in output
    assert "private-id" not in output
    assert "https://" not in output
