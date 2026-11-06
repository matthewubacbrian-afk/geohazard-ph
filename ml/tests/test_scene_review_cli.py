import json
import sys
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
    baseline_comparison: object = None
    test_split_sha256: str = "a" * 64


@dataclass
class _FakeComparison:
    passed_required_non_regression: bool = False


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
    manifest = SimpleNamespace(
        records=records,
        supported_labels=("open_ground",),
        schema_version=1,
        label_schema_version=2,
    )
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
    training_metadata_path = tmp_path / "training-for-evaluation.json"
    training_metadata_path.write_text("{}", encoding="utf-8")
    assert cli.main([
        "evaluate", "--manifest", "m.json", "--data-root", str(tmp_path),
        "--splits", str(splits_file), "--sufficiency-policy", "policy.json",
        "--checkpoint", str(tmp_path / "checkpoint"), "--thresholds", "thresholds.json",
        "--training-metadata", str(training_metadata_path),
        "--output", str(evaluation_path),
    ]) == 0
    assert json.loads(evaluation_path.read_text(encoding="utf-8"))["passed_thresholds"]

    evaluation_inputs = []
    baseline_cache = tmp_path / "model-cache"
    baseline_model, baseline_processor = object(), object()

    def make_dataset(dataset_manifest, data_root, ids, image_processor):
        evaluation_inputs.append((dataset_manifest, data_root, ids, image_processor))
        return object()

    def load_baseline(cache):
        assert cache == baseline_cache
        return baseline_model, baseline_processor

    def compare_baseline(model, dataset, candidate):
        assert model is baseline_model
        assert candidate.passed_thresholds
        return _FakeComparison()

    monkeypatch.setattr(cli, "SceneReviewDataset", make_dataset)
    monkeypatch.setattr(cli, "_make_baseline_inputs", load_baseline)
    monkeypatch.setattr(cli, "evaluate_pinned_baseline", compare_baseline)
    comparison_path = tmp_path / "comparison.json"
    assert cli.main([
        "evaluate", "--manifest", "m.json", "--data-root", str(tmp_path),
        "--splits", str(splits_file), "--sufficiency-policy", "policy.json",
        "--checkpoint", str(tmp_path / "checkpoint"), "--thresholds", "thresholds.json",
        "--training-metadata", str(training_metadata_path),
        "--baseline-model-cache", str(baseline_cache), "--output", str(comparison_path),
    ]) == 2
    report = json.loads(comparison_path.read_text(encoding="utf-8"))
    assert report["baseline_comparison"]["passed_required_non_regression"] is False
    assert report["baseline_coverage"]["comparable_labels"] == ["open_ground"]
    assert evaluation_inputs[0][:3] == evaluation_inputs[1][:3] == (manifest, tmp_path, ("c",))
    assert evaluation_inputs[1][3] is baseline_processor

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


def test_baseline_loader_pins_cached_revision_and_disables_backbone_fetch(tmp_path, monkeypatch):
    calls = {}

    def loader(name):
        def load(model_id, **options):
            calls[name] = model_id, options
            return SimpleNamespace()

        return SimpleNamespace(from_pretrained=load)

    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(
        DetrConfig=loader("config"),
        DetrForSegmentation=loader("model"),
        DetrImageProcessor=loader("processor"),
    ))
    cli._make_baseline_inputs(tmp_path)
    for model_id, options in calls.values():
        assert model_id == "facebook/detr-resnet-50-panoptic"
        assert options["revision"] == "d53b52a799403a8867920f82c869e40732b47037"
        assert options["cache_dir"] == tmp_path
        assert options["local_files_only"] is True
    assert calls["model"][1]["config"].use_pretrained_backbone is False


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
