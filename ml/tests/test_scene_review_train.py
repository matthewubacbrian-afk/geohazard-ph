from pathlib import Path
from types import SimpleNamespace

import pytest

from ml.scene_review.manifest import SufficiencyPolicy
from ml.scene_review.splits import DatasetSplits
from ml.scene_review.train import TrainingConfig, train_model


def _policy() -> SufficiencyPolicy:
    return SufficiencyPolicy(
        maximum_exclusion_rate=0.5,
        minimum_retained_samples_by_split={"train": 1, "validation": 1, "test": 1},
        required_scene_types_by_split={
            "train": ("outdoor",),
            "validation": ("outdoor",),
            "test": ("outdoor",),
        },
        minimum_retained_samples_by_scene_type={},
        minimum_retained_groups_by_split={"train": 1, "validation": 1, "test": 1},
        minimum_retained_samples_per_group_by_split={"train": 1, "validation": 1, "test": 1},
        required_group_ids_by_split={"train": (), "validation": (), "test": ()},
    )


def _config(tmp_path: Path) -> TrainingConfig:
    return TrainingConfig(
        model_id="facebook/detr-resnet-50-panoptic",
        model_revision="d53b52a799403a8867920f82c869e40732b47037",
        seed=23,
        epochs=3,
        batch_size=2,
        learning_rate=1e-5,
        supported_labels=("open_ground", "debris"),
        sufficiency_policy=_policy(),
        data_root=tmp_path / "data",
        output_dir=tmp_path / "out",
    )


class _FakeModel:
    def __init__(self):
        self.config = SimpleNamespace()

    def save_pretrained(self, path):
        Path(path, "model.marker").write_text("fake", encoding="utf-8")


def _manifest(ids):
    return SimpleNamespace(
        supported_labels=("open_ground", "debris"),
        records=[
            SimpleNamespace(image_id=image_id, group_id=image_id, image_sha256=image_id)
            for image_id in ids
        ],
    )


def test_train_requires_a_passing_declared_gate_before_loading_model(tmp_path, monkeypatch):
    from ml.scene_review import train

    calls = []
    monkeypatch.setattr(
        train,
        "validate_dataset",
        lambda *args, **kwargs: SimpleNamespace(sufficiency_gate_passed=False),
    )

    def loader(**kwargs):
        calls.append(kwargs)
        return _FakeModel()

    with pytest.raises(ValueError, match="sufficiency"):
        train_model(
            _manifest("abc"),
            DatasetSplits(("a",), ("b",), ("c",)),
            _config(tmp_path),
            model_cache=tmp_path / "cache",
            model_loader=loader,
            image_processor_factory=lambda **kwargs: object(),
            trainer_factory=lambda **kwargs: object(),
            dataset_factory=lambda **kwargs: object(),
        )
    assert calls == []

def test_train_loads_pinned_model_locally_and_never_reads_test_samples(tmp_path, monkeypatch):
    from ml.scene_review import train

    monkeypatch.setattr(
        train,
        "validate_dataset",
        lambda *args, **kwargs: SimpleNamespace(
            sufficiency_gate_passed=True,
            split_summaries={
                name: SimpleNamespace(
                    total_sample_count=count,
                    excluded_sample_count=0,
                    retained_sample_count=count,
                    exclusion_rate=0.0,
                    scene_type_summaries={
                        "outdoor": SimpleNamespace(retained_sample_count=count)
                    },
                )
                for name, count in (("train", 2), ("validation", 1), ("test", 1))
            },
            unsupported_pixel_counts={},
            unsupported_pixel_counts_by_split={"train": {}, "validation": {}, "test": {}},
            run_mask_ignore_sample_count=0,
            loss_eligible_sample_count=4,
            loss_excluded_sample_count=0,
            exclusion_rate=0.0,
        ),
    )
    loader_args = []
    processor_args = []
    dataset_ids = []
    trainer_calls = []
    trainer_args = []

    def loader(**kwargs):
        loader_args.append(kwargs)
        return _FakeModel()

    def processor_factory(**kwargs):
        processor_args.append(kwargs)
        return object()

    def dataset_factory(**kwargs):
        dataset_ids.append(tuple(kwargs["record_ids"]))
        return tuple(kwargs["record_ids"])

    class FakeTrainer:
        def fit(
            self,
            train_dataset,
            validation_dataset,
            *,
            epochs,
            output_dir,
            on_validation_epoch_end,
        ):
            trainer_calls.append((train_dataset, validation_dataset, epochs))
            for epoch, loss in enumerate((1.0, 0.5, 0.7), start=1):
                on_validation_epoch_end(epoch, loss)

    model = train_model(
        _manifest("abcd"),
        DatasetSplits(("a", "b"), ("c",), ("d",)),
        _config(tmp_path),
        model_cache=tmp_path / "cache",
        model_loader=loader,
        image_processor_factory=processor_factory,
        trainer_factory=lambda **kwargs: trainer_args.append(kwargs) or FakeTrainer(),
        dataset_factory=dataset_factory,
    )

    assert loader_args[0]["model_id"] == "facebook/detr-resnet-50-panoptic"
    assert loader_args[0]["revision"] == "d53b52a799403a8867920f82c869e40732b47037"
    assert loader_args[0]["local_files_only"] is True
    assert loader_args[0]["num_labels"] == 2
    assert loader_args[0]["id2label"] == {0: "open_ground", 1: "debris"}
    assert loader_args[0]["label2id"] == {"open_ground": 0, "debris": 1}
    assert processor_args[0]["local_files_only"] is True
    assert trainer_args[0]["seed"] == 23
    assert trainer_args[0]["config"].seed == 23
    assert dataset_ids == [("a", "b"), ("c",)]
    assert trainer_calls == [(('a', 'b'), ('c',), 3)]
    assert model.best_epoch == 2
    assert model.best_validation_loss == 0.5
    assert model.trained_labels == ("open_ground", "debris")
    assert model.checkpoint_path.exists()
    assert (model.checkpoint_path / "model.marker").read_text(encoding="utf-8") == "fake"
    assert model.training_metadata["split_counts"]["test"] == {
        "total_sample_count": 1,
        "ignore_containing_sample_count": 0,
        "unsupported_pixel_counts_by_canonical_label": {},
        "evaluation_performed": False,
        "evaluated_sample_count": 0,
    }
    assert (
        model.training_metadata["split_counts"]["train"][
            "unsupported_pixel_counts_by_canonical_label"
        ]
        == {}
    )


def test_loss_training_indices_exclude_any_sample_containing_ignore():
    from ml.scene_review.train import _eligible_indices

    samples = [
        {"loss_eligible": True},
        {"loss_eligible": False},
        {"loss_eligible": True},
    ]

    assert _eligible_indices(samples) == [0, 2]


def test_missing_local_model_cache_stops_before_processor_or_trainer(tmp_path, monkeypatch):
    from ml.scene_review import train

    monkeypatch.setattr(
        train,
        "validate_dataset",
        lambda *args, **kwargs: SimpleNamespace(sufficiency_gate_passed=True),
    )
    calls = []

    def missing_model(**kwargs):
        assert kwargs["local_files_only"] is True
        raise FileNotFoundError("pinned checkpoint is not cached locally")

    with pytest.raises(FileNotFoundError, match="not cached"):
        train_model(
            _manifest("abc"),
            DatasetSplits(("a",), ("b",), ("c",)),
            _config(tmp_path),
            model_cache=tmp_path / "missing-cache",
            model_loader=missing_model,
            image_processor_factory=lambda **kwargs: calls.append("processor"),
            trainer_factory=lambda **kwargs: calls.append("trainer"),
            dataset_factory=lambda **kwargs: object(),
        )
    assert calls == []\n