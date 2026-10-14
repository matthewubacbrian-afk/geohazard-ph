"""Offline command-line workflow for Scene Review dataset and model artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from ml.scene_review.artifacts import export_artifact
from ml.scene_review.dataset import SceneReviewDataset
from ml.scene_review.evaluate import EvaluationThresholds, evaluate_model
from ml.scene_review.manifest import (
    SufficiencyPolicy,
    load_manifest,
    validate_dataset,
)
from ml.scene_review.splits import DatasetSplits, make_grouped_splits, splits_to_json
from ml.scene_review.train import TrainingConfig, train_model

ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "model_artifacts" / "scene_review"


class _PrivacySafeArgumentParser(argparse.ArgumentParser):
    """Report malformed arguments without echoing user-supplied values."""

    def error(self, message: str) -> None:
        del message
        self.exit(2, f"{self.prog}: error: invalid command arguments\n")


def _parser() -> argparse.ArgumentParser:
    parser = _PrivacySafeArgumentParser(prog="scene-review")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate local rights-approved scene data")
    _add_manifest_root(validate)
    split = commands.add_parser("split", help="make deterministic source-group splits")
    _add_manifest_root(split)
    split.add_argument("--seed", type=int, default=42)
    split.add_argument("--output", type=Path, required=True)
    train = commands.add_parser("train", help="fine-tune offline from an explicit local model cache")
    _add_manifest_root(train)
    train.add_argument("--splits", type=Path, required=True)
    train.add_argument("--sufficiency-policy", type=Path, required=True)
    train.add_argument("--model-cache", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--epochs", type=int, default=5)
    train.add_argument("--batch-size", type=int, default=2)
    train.add_argument("--learning-rate", type=float, default=1e-5)
    train.add_argument("--model-id", default="facebook/detr-resnet-50-panoptic")
    train.add_argument(
        "--model-revision", default="d53b52a799403a8867920f82c869e40732b47037"
    )
    evaluate = commands.add_parser("evaluate", help="evaluate an explicit held-out local split")
    _add_manifest_root(evaluate)
    evaluate.add_argument("--splits", type=Path, required=True)
    evaluate.add_argument("--sufficiency-policy", type=Path, required=True)
    evaluate.add_argument("--checkpoint", type=Path, required=True)
    evaluate.add_argument("--thresholds", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    export = commands.add_parser("export", help="write an immutable reviewed model artifact")
    export.add_argument("--checkpoint", type=Path, required=True)
    export.add_argument("--evaluation", type=Path, required=True)
    export.add_argument("--metadata", type=Path, required=True)
    export.add_argument("--version", required=True)
    return parser


def _add_manifest_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        handler = {
            "validate": _run_validate,
            "split": _run_split,
            "train": _run_train,
            "evaluate": _run_evaluate,
            "export": _run_export,
        }[args.command]
        return handler(args)
    except Exception:  # noqa: BLE001 - never echo local paths or private identifiers
        print(json.dumps({"status": "error", "message": "operation failed"}, sort_keys=True))
        return 2


def _run_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    report = validate_dataset(manifest, args.data_root)
    _print_json({
        "status": "valid",
        "image_count": report.image_count,
        "loss_eligible_sample_count": report.loss_eligible_sample_count,
        "loss_excluded_sample_count": report.loss_excluded_sample_count,
        "exclusion_rate": report.exclusion_rate,
        "sufficiency_gate_passed": report.sufficiency_gate_passed,
    })
    return 0


def _run_split(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    validate_dataset(manifest, args.data_root)
    splits = make_grouped_splits(manifest.records, seed=args.seed)
    _write_new_file(args.output, splits_to_json(splits, seed=args.seed))
    _print_json({
        "status": "split",
        "train_count": len(splits.train_ids),
        "validation_count": len(splits.validation_ids),
        "test_count": len(splits.test_ids),
        "seed": args.seed,
    })
    return 0


def _run_train(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    splits = _read_splits(args.splits)
    policy = _read_sufficiency_policy(args.sufficiency_policy)
    config = TrainingConfig(
        model_id=args.model_id,
        model_revision=args.model_revision,
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        supported_labels=tuple(manifest.supported_labels),
        sufficiency_policy=policy,
        data_root=args.data_root,
        output_dir=args.output_dir,
    )
    result = train_model(manifest, splits, config, model_cache=args.model_cache)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_new_file(
        args.output_dir / "training_metadata.json",
        json.dumps(_json_value(result.training_metadata), sort_keys=True, indent=2) + "\n",
    )
    _print_json({
        "status": "trained",
        "best_epoch": result.best_epoch,
        "best_validation_loss": result.best_validation_loss,
        "trained_label_count": len(result.trained_labels),
        "sufficiency_gate_passed": result.training_metadata.get("sufficiency_gate_passed"),
    })
    return 0


def _run_evaluate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    splits = _read_splits(args.splits)
    policy = _read_sufficiency_policy(args.sufficiency_policy)
    assignments = _split_mapping(splits)
    gate = validate_dataset(
        manifest,
        args.data_root,
        split_by_image_id=assignments,
        sufficiency_policy=policy,
    )
    if gate.sufficiency_gate_passed is not True:
        raise ValueError("sufficiency gate failed")
    thresholds = _read_evaluation_thresholds(args.thresholds)
    model, processor = _make_evaluation_inputs(args.checkpoint)
    dataset = SceneReviewDataset(
        manifest, args.data_root, splits.test_ids, image_processor=processor
    )
    report = evaluate_model(
        model, dataset, thresholds, splits=splits, sufficiency_report=gate
    )
    output = _json_value(report)
    _write_new_file(args.output, json.dumps(output, sort_keys=True, indent=2) + "\n")
    _print_json({
        "status": "evaluated",
        "passed_thresholds": report.passed_thresholds,
        "evaluated_sample_count": report.sample_counts.get("evaluated", 0),
        "threshold_failure_count": len(report.threshold_failures),
    })
    return 0 if report.passed_thresholds else 2


def _run_export(args: argparse.Namespace) -> int:
    training_metadata = _read_json_object(args.metadata)
    evaluation = _read_json_object(args.evaluation)
    path = export_artifact(
        checkpoint_path=args.checkpoint,
        evaluation_report=evaluation,
        training_metadata=training_metadata,
        sufficiency_gate_passed=training_metadata.get("sufficiency_gate_passed") is True,
        version=args.version,
        output_root=ARTIFACT_ROOT,
    )
    _print_json({"status": "exported", "model_file_count": len(tuple((path / "model").iterdir()))})
    return 0


def _read_splits(path: Path) -> DatasetSplits:
    raw = _read_json_object(path)
    if set(raw) != {"schema_version", "seed", "train_ids", "validation_ids", "test_ids"}:
        raise ValueError("invalid split file")
    if raw["schema_version"] != 1:
        raise ValueError("unsupported split schema")
    return DatasetSplits(
        tuple(raw["train_ids"]), tuple(raw["validation_ids"]), tuple(raw["test_ids"])
    )


def _read_sufficiency_policy(path: Path) -> SufficiencyPolicy:
    raw = _read_json_object(path)
    expected = {
        "maximum_exclusion_rate",
        "minimum_retained_samples_by_split",
        "required_scene_types_by_split",
        "minimum_retained_samples_by_scene_type",
        "minimum_retained_groups_by_split",
        "minimum_retained_samples_per_group_by_split",
        "required_group_ids_by_split",
    }
    if set(raw) != expected:
        raise ValueError("invalid sufficiency policy fields")
    raw["required_scene_types_by_split"] = {
        key: tuple(value) for key, value in raw["required_scene_types_by_split"].items()
    }
    raw["required_group_ids_by_split"] = {
        key: tuple(value) for key, value in raw["required_group_ids_by_split"].items()
    }
    return SufficiencyPolicy(**raw)


def _read_evaluation_thresholds(path: Path) -> EvaluationThresholds:
    raw = _read_json_object(path)
    return EvaluationThresholds(**raw)


def _make_evaluation_inputs(checkpoint: Path) -> tuple[object, object]:
    try:
        from transformers import DetrForSegmentation, DetrImageProcessor
    except ImportError as exc:
        raise RuntimeError("install the scene-review optional extra") from exc
    model = DetrForSegmentation.from_pretrained(checkpoint, local_files_only=True)
    processor = DetrImageProcessor.from_pretrained(checkpoint, local_files_only=True)
    return model, processor


def _split_mapping(splits: DatasetSplits) -> dict[str, str]:
    return {
        image_id: name
        for name, ids in (
            ("train", splits.train_ids),
            ("validation", splits.validation_ids),
            ("test", splits.test_ids),
        )
        for image_id in ids
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("JSON input must be an object")
    return raw


def _write_new_file(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError("output file already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(content)


def _json_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("value cannot be serialized as JSON")


def _print_json(value: Mapping[str, object]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    sys.exit(main())
