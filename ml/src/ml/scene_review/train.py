"""Deterministic local-only fine-tuning for the Scene Review segmentation model."""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ml.scene_review.dataset import SceneReviewDataset
from ml.scene_review.manifest import (
    DatasetValidationReport,
    SceneDatasetManifest,
    SufficiencyPolicy,
    validate_dataset,
)
from ml.scene_review.splits import DatasetSplits, validate_splits

DEFAULT_MODEL_ID = "facebook/detr-resnet-50-panoptic"
DEFAULT_MODEL_REVISION = "d53b52a799403a8867920f82c869e40732b47037"


@dataclass(frozen=True)
class TrainingConfig:
    model_id: str
    model_revision: str
    seed: int
    epochs: int
    batch_size: int
    learning_rate: float
    supported_labels: tuple[str, ...]
    sufficiency_policy: SufficiencyPolicy
    data_root: Path
    output_dir: Path

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be nonempty")
        if not isinstance(self.model_revision, str) or not self.model_revision.strip():
            raise ValueError("model_revision must be pinned")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an integer")
        if not isinstance(self.epochs, int) or isinstance(self.epochs, bool) or self.epochs < 1:
            raise ValueError("epochs must be positive")
        if (
            not isinstance(self.batch_size, int)
            or isinstance(self.batch_size, bool)
            or self.batch_size < 1
        ):
            raise ValueError("batch_size must be positive")
        if (
            not isinstance(self.learning_rate, (float, int))
            or isinstance(self.learning_rate, bool)
            or self.learning_rate <= 0
        ):
            raise ValueError("learning_rate must be positive")
        if not isinstance(self.supported_labels, tuple) or not self.supported_labels:
            raise ValueError("supported_labels must be a nonempty tuple")
        if len(set(self.supported_labels)) != len(self.supported_labels):
            raise ValueError("supported_labels must not contain duplicates")
        if not isinstance(self.sufficiency_policy, SufficiencyPolicy):
            raise TypeError("a declared SufficiencyPolicy is required")
        if not isinstance(self.data_root, Path) or not isinstance(self.output_dir, Path):
            raise TypeError("data_root and output_dir must be Path instances")


@dataclass(frozen=True)
class TrainingResult:
    checkpoint_path: Path
    best_epoch: int
    best_validation_loss: float
    seed: int
    trained_labels: tuple[str, ...]
    training_metadata: Mapping[str, Any]


def train_model(
    manifest: SceneDatasetManifest,
    splits: DatasetSplits,
    config: TrainingConfig,
    *,
    model_cache: Path,
    model_loader: Callable[..., object] | None = None,
    image_processor_factory: Callable[..., object] | None = None,
    trainer_factory: Callable[..., object] | None = None,
    dataset_factory: Callable[..., object] | None = None,
) -> TrainingResult:
    """Train and select by validation loss without accessing the held-out test split."""
    if not isinstance(config, TrainingConfig):
        raise TypeError("config must be a TrainingConfig")
    if tuple(config.supported_labels) != tuple(manifest.supported_labels):
        raise ValueError("training labels must exactly match the manifest's supported labels")
    validate_splits(manifest.records, splits)
    split_by_id = {
        image_id: name
        for name, ids in (
            ("train", splits.train_ids),
            ("validation", splits.validation_ids),
            ("test", splits.test_ids),
        )
        for image_id in ids
    }
    report = validate_dataset(
        manifest,
        config.data_root,
        split_by_image_id=split_by_id,
        sufficiency_policy=config.sufficiency_policy,
    )
    _require_passing_gate(report)

    _seed_everything(config.seed)
    loader = model_loader or _load_model
    processor_factory = image_processor_factory or _load_processor
    make_dataset = dataset_factory or SceneReviewDataset
    trainer_builder = trainer_factory or _TorchTrainer
    label_to_id = {label: index for index, label in enumerate(config.supported_labels)}
    model = loader(
        model_id=config.model_id,
        revision=config.model_revision,
        cache_dir=model_cache,
        local_files_only=True,
        num_labels=len(config.supported_labels),
        id2label={index: label for label, index in label_to_id.items()},
        label2id=label_to_id,
        ignore_mismatched_sizes=True,
    )
    processor = processor_factory(
        model_id=config.model_id,
        revision=config.model_revision,
        cache_dir=model_cache,
        local_files_only=True,
    )
    train_dataset = make_dataset(
        manifest=manifest,
        data_root=config.data_root,
        record_ids=splits.train_ids,
        image_processor=processor,
    )
    validation_dataset = make_dataset(
        manifest=manifest,
        data_root=config.data_root,
        record_ids=splits.validation_ids,
        image_processor=processor,
    )
    trainer = trainer_builder(
        model=model,
        config=config,
        seed=config.seed,
    )
    best_epoch = 0
    best_validation_loss = float("inf")
    checkpoint_path: Path | None = None

    def consider_checkpoint(epoch: int, validation_loss: float) -> None:
        nonlocal best_epoch, best_validation_loss, checkpoint_path
        validation_loss = float(validation_loss)
        if not np.isfinite(validation_loss):
            raise ValueError("validation loss must be finite")
        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_epoch = epoch
            checkpoint_path = config.output_dir / f"checkpoint-epoch-{epoch}"
            _save_model(model, checkpoint_path)

    trainer.fit(
        train_dataset,
        validation_dataset,
        epochs=config.epochs,
        output_dir=config.output_dir,
        on_validation_epoch_end=consider_checkpoint,
    )
    if checkpoint_path is None:
        raise ValueError("training did not produce a finite validation loss")

    split_metadata: dict[str, object] = {}
    for split_name, summary in report.split_summaries.items():
        split_metadata[split_name] = {
            "total_sample_count": summary.total_sample_count,
            "ignore_containing_sample_count": summary.excluded_sample_count,
        }
        if split_name in {"train", "validation"}:
            split_metadata[split_name].update(
                {
                    "unsupported_pixel_counts_by_canonical_label": dict(
                        report.unsupported_pixel_counts_by_split.get(split_name, {})
                    ),
                    "loss_eligible_sample_count": summary.retained_sample_count,
                    "loss_excluded_sample_count": summary.excluded_sample_count,
                    "exclusion_rate": summary.exclusion_rate,
                    "retained_counts_by_scene_type": {
                        scene_type: scene_summary.retained_sample_count
                        for scene_type, scene_summary in summary.scene_type_summaries.items()
                    },
                }
            )
        else:
            split_metadata[split_name]["unsupported_pixel_counts_by_canonical_label"] = dict(
                report.unsupported_pixel_counts_by_split.get(split_name, {})
            )
            split_metadata[split_name]["evaluation_performed"] = False
            split_metadata[split_name]["evaluated_sample_count"] = 0
    metadata = {
        "model_id": config.model_id,
        "model_revision": config.model_revision,
        "seed": config.seed,
        "supported_labels": list(config.supported_labels),
        "split_counts": split_metadata,
        "unsupported_pixel_counts_by_canonical_label": dict(report.unsupported_pixel_counts),
        "sufficiency_gate_passed": report.sufficiency_gate_passed,
    }
    return TrainingResult(
        checkpoint_path=checkpoint_path,
        best_epoch=best_epoch,
        best_validation_loss=best_validation_loss,
        seed=config.seed,
        trained_labels=config.supported_labels,
        training_metadata=metadata,
    )


def _require_passing_gate(report: DatasetValidationReport) -> None:
    if report.sufficiency_gate_passed is not True:
        raise ValueError("training requires a declared, passing sufficiency gate")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _load_model(**kwargs: object) -> object:
    try:
        from transformers import DetrForSegmentation
    except ImportError as exc:
        raise RuntimeError("install the scene-review optional dependency extra") from exc
    return DetrForSegmentation.from_pretrained(**kwargs)


def _load_processor(**kwargs: object) -> object:
    try:
        from transformers import DetrImageProcessor
    except ImportError as exc:
        raise RuntimeError("install the scene-review optional dependency extra") from exc
    return DetrImageProcessor.from_pretrained(**kwargs)


def _save_model(model: object, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    save_pretrained = getattr(model, "save_pretrained", None)
    if not callable(save_pretrained):
        raise TypeError("model must support save_pretrained for checkpoint selection")
    save_pretrained(path)


def _eligible_indices(dataset: object) -> list[int]:
    """Return only indices whose run mask is safe for the stock DETR loss."""
    return [index for index in range(len(dataset)) if dataset[index]["loss_eligible"]]


class _TorchTrainer:
    """Minimal CPU trainer that drops ignore-containing samples before model forward."""

    def __init__(self, *, model: object, config: TrainingConfig, seed: int) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("install the scene-review optional dependency extra") from exc
        self._torch = torch
        self._model = model
        self._config = config
        self._seed = seed
        self._model.to(torch.device("cpu"))

    def fit(
        self,
        train_dataset: object,
        validation_dataset: object,
        *,
        epochs: int,
        output_dir: Path,
        on_validation_epoch_end: Callable[[int, float], None],
    ) -> None:
        torch = self._torch
        optimizer = torch.optim.AdamW(self._model.parameters(), lr=self._config.learning_rate)
        for epoch in range(epochs):
            self._run_epoch(train_dataset, optimizer, epoch)
            validation_loss = self._run_epoch(validation_dataset, None, epoch)
            on_validation_epoch_end(epoch + 1, validation_loss)

    def _run_epoch(self, dataset: object, optimizer: object | None, epoch: int) -> float:
        torch = self._torch
        training = optimizer is not None
        self._model.train(training)
        losses: list[float] = []
        order = _eligible_indices(dataset)
        if training:
            random.Random(self._seed + epoch).shuffle(order)
        for start in range(0, len(order), self._config.batch_size):
            batch = [dataset[index] for index in order[start : start + self._config.batch_size]]
            pixel_values = torch.stack(
                [torch.as_tensor(sample["pixel_values"], dtype=torch.float32) for sample in batch]
            )
            labels = [
                {key: torch.as_tensor(value) for key, value in sample["labels"].items()}
                for sample in batch
            ]
            model_inputs = {"pixel_values": pixel_values, "labels": labels}
            if all("pixel_mask" in sample for sample in batch):
                model_inputs["pixel_mask"] = torch.stack(
                    [torch.as_tensor(sample["pixel_mask"]) for sample in batch]
                )
            if training:
                optimizer.zero_grad()
            with torch.set_grad_enabled(training):
                output = self._model(**model_inputs)
                loss = output.loss
                if training:
                    loss.backward()
                    optimizer.step()
            losses.extend([float(loss.detach().cpu())] * len(batch))
        if not losses:
            raise ValueError("a split has no loss-eligible samples")
        return float(np.mean(losses))
