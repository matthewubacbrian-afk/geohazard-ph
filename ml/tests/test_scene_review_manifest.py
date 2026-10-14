import hashlib
import json

import numpy as np
import pytest
from PIL import Image

from ml.scene_review.labels import BACKGROUND_ID, IGNORE_ID
from ml.scene_review.manifest import SufficiencyPolicy, load_manifest, validate_dataset

USES = ["training", "evaluation", "derived_weight_redistribution"]


def record(**updates):
    item = {
        "image_id": "local-1",
        "image_path": "images/one.png",
        "mask_path": "masks/one.png",
        "image_sha256": "",
        "mask_sha256": "",
        "group_id": "group-1",
        "scene_type": "outdoor",
        "lighting": "day",
        "occlusion": "low",
        "image_quality": "good",
        "source_image_id": "source-123",
        "source_page_url": "https://source.example/image/123",
        "original_image_source": "Example archive",
        "original_image_creator": "Creator",
        "image_license_name": "Image grant",
        "image_terms_evidence_url": "https://source.example/terms/123",
        "image_retrieval_evidence_url": "https://source.example/releases/v1",
        "image_release_or_retrieval_id": "release-v1/image-123",
        "image_rights_evidence_scope": "image_specific",
        "image_rights_evidence_reference": "source-123 clause 4 grants all intended uses",
        "image_rights_review_status": "approved",
        "image_rights_reviewer": "Reviewer",
        "image_rights_decision_date": "2026-10-15",
        "image_rights_decision_reason": "Grant covers uses",
        "image_permitted_uses": USES,
        "image_derived_weight_status": "permitted",
        "image_derived_weight_restrictions": "No additional restrictions",
        "image_retention_limits": None,
        "image_attribution": "Creator / archive",
        "annotation_record_id": "ann-1",
        "annotation_provenance": "scene-review-v2 project annotation",
    }
    item.update(updates)
    return item


def manifest(**updates):
    data = {
        "schema_version": 1,
        "dataset_id": "dataset-1",
        "source_url": "https://source.example/dataset",
        "terms_evidence_url": "https://source.example/terms/123",
        "license_name": "Image grant",
        "retrieved_at": "2026-10-15T12:00:00Z",
        "retrieval_evidence_url": "https://source.example/releases/v1",
        "immutable_release_or_retrieval_id": "release-v1",
        "rights_review_status": "approved",
        "rights_reviewer": "Reviewer",
        "rights_decision_date": "2026-10-15",
        "rights_decision_reason": "Terms cover all uses",
        "permitted_uses": USES,
        "derived_weight_status": "permitted",
        "derived_weight_restrictions": "No additional restrictions",
        "retention_limits": "Retain under source grant terms",
        "attribution": "Creator / archive",
        "annotation_provenance": "scene-review-v2 project annotation",
        "label_schema_version": 2,
        "supported_labels": ["open_ground", "obstacle"],
        "records": [record()],
    }
    data.update(updates)
    return data


def files(tmp_path, mask_ids=(0, 1, BACKGROUND_ID)):
    root = tmp_path / "data"
    image_path, mask_path = root / "images/one.png", root / "masks/one.png"
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    Image.fromarray(np.zeros((1, len(mask_ids), 3), dtype=np.uint8)).save(image_path)
    Image.fromarray(np.array([mask_ids], dtype=np.uint8)).save(mask_path)
    return root, image_path, mask_path


def save_manifest(tmp_path, data):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def add_hashes(item, image_path, mask_path):
    item["image_sha256"] = hashlib.sha256(image_path.read_bytes()).hexdigest()
    item["mask_sha256"] = hashlib.sha256(mask_path.read_bytes()).hexdigest()


def multi_dataset(tmp_path, masks, scene_types, *, supported_labels=None):
    root = tmp_path / "data"
    records = []
    for index, mask_ids in enumerate(masks):
        image_path = root / f"images/{index}.png"
        mask_path = root / f"masks/{index}.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.zeros((1, len(mask_ids), 3), dtype=np.uint8)).save(image_path)
        Image.fromarray(np.array([mask_ids], dtype=np.uint8)).save(mask_path)
        item = record(
            image_id=f"local-{index}",
            image_path=f"images/{index}.png",
            mask_path=f"masks/{index}.png",
            scene_type=scene_types[index],
            group_id=f"private-location-{index}",
        )
        add_hashes(item, image_path, mask_path)
        records.append(item)
    manifest_data = manifest(records=records)
    if supported_labels is not None:
        manifest_data["supported_labels"] = list(supported_labels)
    return root, load_manifest(save_manifest(tmp_path, manifest_data))


def sufficiency_policy(
    *,
    maximum_exclusion_rate=0.5,
    minimum_retained_samples_by_split=None,
    required_scene_types_by_split=None,
    minimum_retained_samples_by_scene_type=None,
):
    return SufficiencyPolicy(
        maximum_exclusion_rate=maximum_exclusion_rate,
        minimum_retained_samples_by_split=minimum_retained_samples_by_split
        or {
            "train": 1,
            "validation": 1,
            "test": 1,
        },
        required_scene_types_by_split=required_scene_types_by_split
        or {
            "train": ("indoor",),
            "validation": ("outdoor",),
            "test": ("mixed",),
        },
        minimum_retained_samples_by_scene_type=minimum_retained_samples_by_scene_type or {},
        minimum_retained_groups_by_split={"train": 1, "validation": 1, "test": 1},
        minimum_retained_samples_per_group_by_split={"train": 1, "validation": 1, "test": 1},
        required_group_ids_by_split={"train": (), "validation": (), "test": ()},
    )


def test_load_manifest_parses_dataclasses_and_rejects_missing_or_extra_fields(tmp_path):
    loaded = load_manifest(save_manifest(tmp_path, manifest()))
    assert loaded.records[0].source_image_id == "source-123"
    assert loaded.records[0].image_permitted_uses == tuple(USES)
    missing = manifest()
    del missing["retention_limits"]
    with pytest.raises(ValueError, match="missing fields"):
        load_manifest(save_manifest(tmp_path, missing))
    with pytest.raises(ValueError, match="unknown fields"):
        load_manifest(save_manifest(tmp_path, manifest(unexpected=True)))
    with pytest.raises(TypeError, match="JSON"):
        load_manifest(save_manifest(tmp_path, "not json"))


def test_valid_manifest_reports_counts_only_and_uses_declared_subset(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    data = manifest()
    add_hashes(data["records"][0], image_path, mask_path)
    report = validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    assert report.image_count == 1
    assert report.pixel_counts == {
        "open_ground": 1,
        "obstacle": 1,
        "glass_facade": 0,
        "overhead_lines": 0,
        "visible_building_damage": 0,
        "background": 1,
        "ignore": 0,
    }
    assert report.unsupported_pixel_counts == {}
    assert report.run_mask_ignore_sample_count == 0
    assert report.loss_eligible_sample_count == 1
    assert report.loss_excluded_sample_count == 0
    assert report.exclusion_rate == 0
    assert (
        report.split_summaries["unsplit"].scene_type_summaries["outdoor"].retained_sample_count == 1
    )
    assert report.sufficiency_gate_passed is None
    assert any("gate undeclared" in warning for warning in report.warnings)
    assert not hasattr(report, "paths") and not hasattr(report, "records")


def test_scene_type_categories_are_controlled_and_group_values_do_not_escape(tmp_path):
    root, manifest_data = multi_dataset(tmp_path, [(0, BACKGROUND_ID)], ["../../private/path"])

    with pytest.raises(ValueError, match="scene_type"):
        validate_dataset(manifest_data, root)


def test_reports_split_and_scene_type_exclusion_counts_and_passes_declared_gate(tmp_path):
    root, manifest_data = multi_dataset(
        tmp_path,
        [(0, BACKGROUND_ID), (0, BACKGROUND_ID), (0, BACKGROUND_ID)],
        ["indoor", "outdoor", "mixed"],
    )
    splits = {"local-0": "train", "local-1": "validation", "local-2": "test"}

    report = validate_dataset(
        manifest_data,
        root,
        split_by_image_id=splits,
        sufficiency_policy=sufficiency_policy(),
    )

    assert report.sufficiency_gate_passed is True
    assert report.sufficiency_gate_reasons == ()
    assert report.split_summaries["train"].retained_sample_count == 1
    assert report.split_summaries["train"].scene_type_summaries["indoor"].retained_sample_count == 1
    assert report.split_summaries["train"].group_summaries.total_group_count == 1
    assert report.split_summaries["train"].group_summaries.retained_group_count == 1
    assert report.split_summaries["train"].group_summaries.minimum_retained_samples_per_group == 1
    assert report.split_summaries["train"].group_summaries.maximum_retained_samples_per_group == 1
    assert "private-location" not in repr(report)
    assert "local-0" not in repr(report)
    assert "source-123" not in repr(report)
    assert "images/0.png" not in repr(report)


@pytest.mark.parametrize(
    "policy, masks, expected_reason",
    [
        (
            sufficiency_policy(maximum_exclusion_rate=0.0),
            [(0, 1), (0, 5), (0, 5)],
            "exclusion rate",
        ),
        (
            sufficiency_policy(
                minimum_retained_samples_by_split={"train": 2, "validation": 1, "test": 1}
            ),
            [(0, 5), (0, 5), (0, 5)],
            "minimum retained",
        ),
        (
            sufficiency_policy(
                required_scene_types_by_split={
                    "train": ("outdoor",),
                    "validation": ("outdoor",),
                    "test": ("mixed",),
                }
            ),
            [(0, 5), (0, 5), (0, 5)],
            "required scene coverage",
        ),
        (
            sufficiency_policy(minimum_retained_samples_by_scene_type={"indoor": 2}),
            [(0, 5), (0, 5), (0, 5)],
            "indoor minimum retained",
        ),
    ],
)
def test_declared_gate_fails_exclusion_rate_minimum_or_representation(
    tmp_path,
    policy,
    masks,
    expected_reason,
):
    root, manifest_data = multi_dataset(
        tmp_path,
        masks,
        ["indoor", "outdoor", "mixed"],
        supported_labels=("open_ground",) if expected_reason == "exclusion rate" else None,
    )
    splits = {"local-0": "train", "local-1": "validation", "local-2": "test"}

    report = validate_dataset(
        manifest_data,
        root,
        split_by_image_id=splits,
        sufficiency_policy=policy,
    )

    assert report.sufficiency_gate_passed is False
    assert any(expected_reason in reason for reason in report.sufficiency_gate_reasons)


def test_gate_cannot_run_without_complete_declared_splits_or_policy(tmp_path):
    root, manifest_data = multi_dataset(
        tmp_path,
        [(0, BACKGROUND_ID), (0, BACKGROUND_ID), (0, BACKGROUND_ID)],
        ["indoor", "outdoor", "mixed"],
    )
    with pytest.raises(ValueError, match="split assignments"):
        validate_dataset(
            manifest_data,
            root,
            sufficiency_policy=sufficiency_policy(),
        )

    report = validate_dataset(manifest_data, root)
    assert report.sufficiency_gate_passed is None


def test_group_exclusion_stats_and_required_group_gate_do_not_expose_group_ids(tmp_path):
    root, manifest_data = multi_dataset(
        tmp_path,
        [(0, 1), (0, BACKGROUND_ID), (0, BACKGROUND_ID)],
        ["indoor", "outdoor", "mixed"],
        supported_labels=("open_ground",),
    )
    policy = sufficiency_policy()
    policy = SufficiencyPolicy(
        **{
            **policy.__dict__,
            "required_group_ids_by_split": {
                "train": ("private-location-0",),
                "validation": (),
                "test": (),
            },
        }
    )
    splits = {"local-0": "train", "local-1": "validation", "local-2": "test"}

    report = validate_dataset(
        manifest_data,
        root,
        split_by_image_id=splits,
        sufficiency_policy=policy,
    )

    train_groups = report.split_summaries["train"].group_summaries
    assert train_groups.total_group_count == 1
    assert train_groups.retained_group_count == 0
    assert train_groups.excluded_group_count == 1
    assert train_groups.minimum_retained_samples_per_group == 0
    assert train_groups.maximum_retained_samples_per_group == 0
    assert report.sufficiency_gate_passed is False
    assert any("required group coverage" in reason for reason in report.sufficiency_gate_reasons)
    assert "private-location-0" not in repr(report)
    assert "local-0" not in repr(report)


def test_rejects_nonapproved_dataset_or_image_records(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    for data in (
        manifest(rights_review_status="pending_review"),
        manifest(rights_review_status="excluded"),
    ):
        add_hashes(data["records"][0], image_path, mask_path)
        with pytest.raises(ValueError, match="approved"):
            validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    for status in ("pending_review", "excluded"):
        data = manifest()
        data["records"][0]["image_rights_review_status"] = status
        add_hashes(data["records"][0], image_path, mask_path)
        with pytest.raises(ValueError, match="approved"):
            validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


def test_requires_all_three_uses_dataset_and_image_level(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    cases = [manifest(permitted_uses=USES[:2]), manifest()]
    cases[1]["records"][0]["image_permitted_uses"] = USES[:2]
    for data in cases:
        add_hashes(data["records"][0], image_path, mask_path)
        with pytest.raises(ValueError, match="derived_weight_redistribution"):
            validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("rights_reviewer", ""),
        ("rights_decision_date", ""),
        ("rights_decision_reason", ""),
        ("immutable_release_or_retrieval_id", ""),
        ("retrieval_evidence_url", ""),
        ("retention_limits", ""),
        ("annotation_provenance", ""),
        ("derived_weight_status", "not established"),
        ("derived_weight_restrictions", ""),
    ],
)
def test_requires_complete_dataset_decision_and_provenance(tmp_path, field, value):
    root, image_path, mask_path = files(tmp_path)
    data = manifest(**{field: value})
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("image_rights_reviewer", ""),
        ("image_rights_decision_date", ""),
        ("image_rights_decision_reason", ""),
        ("image_release_or_retrieval_id", ""),
        ("image_retrieval_evidence_url", ""),
        ("original_image_source", ""),
        ("original_image_creator", ""),
        ("annotation_record_id", ""),
        ("annotation_provenance", ""),
        ("image_attribution", ""),
        ("image_derived_weight_status", "not established"),
        ("image_derived_weight_restrictions", ""),
    ],
)
def test_rejects_missing_image_rights_provenance_and_weight_fields(tmp_path, field, value):
    root, image_path, mask_path = files(tmp_path)
    data = manifest()
    data["records"][0][field] = value
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


def test_shared_grant_requires_record_specific_coverage_and_retention_override(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    data = manifest()
    item = data["records"][0]
    item["image_rights_evidence_scope"] = "shared_grant"
    item["image_rights_evidence_reference"] = "section 4 generally permits research"
    add_hashes(item, image_path, mask_path)
    with pytest.raises(ValueError, match="shared grant must expressly cover"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    item["image_rights_evidence_reference"] = (
        "source-123 clause 4 expressly covers training, evaluation, and weights"
    )
    item["image_terms_evidence_url"] = "https://other.example/terms"
    with pytest.raises(ValueError, match="retention"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


def test_accepts_shared_grant_that_explicitly_covers_image(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    data = manifest()
    item = data["records"][0]
    item["image_rights_evidence_scope"] = "shared_grant"
    item["image_rights_evidence_reference"] = (
        "grant clause 4 expressly covers source-123 for training, evaluation, and derived weights"
    )
    add_hashes(item, image_path, mask_path)

    report = validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)

    assert report.image_count == 1


def test_rejects_unsafe_paths_hash_mismatch_and_malformed_files(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    for key, path_value in (("image_path", "../outside.png"), ("mask_path", "C:/outside.png")):
        data = manifest()
        data["records"][0][key] = path_value
        add_hashes(data["records"][0], image_path, mask_path)
        with pytest.raises(ValueError, match="path"):
            validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    data = manifest()
    data["records"][0]["image_path"] = "images/missing.png"
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError, match="does not exist"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    data = manifest()
    add_hashes(data["records"][0], image_path, mask_path)
    data["records"][0]["image_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)


def test_remaps_unsupported_pixels_counts_them_and_reports_sample_exclusion(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    data = manifest(supported_labels=["open_ground"])
    add_hashes(data["records"][0], image_path, mask_path)
    report = validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    assert report.unsupported_pixel_counts == {"obstacle": 1}
    assert report.run_mask_ignore_pixel_count == 1
    assert report.run_mask_ignore_sample_count == 1
    assert report.loss_eligible_sample_count == 0
    assert report.loss_excluded_sample_count == 1
    assert report.exclusion_rate == 1


def test_rejects_corrupt_mask_dimension_mismatch_duplicate_ids_and_all_ignore(tmp_path):
    root, image_path, mask_path = files(tmp_path, (0, 1))
    data = manifest()
    add_hashes(data["records"][0], image_path, mask_path)
    loaded = load_manifest(save_manifest(tmp_path, data))
    Image.fromarray(np.array([[99, 0]], dtype=np.uint8)).save(mask_path)
    with pytest.raises(ValueError, match="hash|mask"):
        validate_dataset(loaded, root)
    data["records"][0]["mask_sha256"] = hashlib.sha256(mask_path.read_bytes()).hexdigest()
    loaded = load_manifest(save_manifest(tmp_path, data))
    with pytest.raises(ValueError, match="unknown mask IDs"):
        validate_dataset(loaded, root)

    data["records"][0]["mask_sha256"] = hashlib.sha256(mask_path.read_bytes()).hexdigest()
    image_path.write_bytes(b"not an image")
    data["records"][0]["image_sha256"] = hashlib.sha256(image_path.read_bytes()).hexdigest()
    loaded = load_manifest(save_manifest(tmp_path, data))
    with pytest.raises(ValueError, match="image is not a readable"):
        validate_dataset(loaded, root)

    root, image_path, mask_path = files(tmp_path / "dim", (0, 1))
    Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8)).save(image_path)
    data = manifest()
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError, match="dimension"):
        validate_dataset(load_manifest(save_manifest(tmp_path / "dim", data)), root)

    root, image_path, mask_path = files(tmp_path / "dup", (0, 1))
    data = manifest(
        records=[record(), record(image_path="images/two.png", mask_path="masks/two.png")]
    )
    add_hashes(data["records"][0], image_path, mask_path)
    data["records"][1]["image_id"] = data["records"][0]["image_id"]
    with pytest.raises(ValueError, match="duplicate"):
        validate_dataset(load_manifest(save_manifest(tmp_path / "dup", data)), root)

    Image.fromarray(np.full((1, 2), IGNORE_ID, dtype=np.uint8)).save(mask_path)
    data = manifest()
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError, match="ignore"):
        validate_dataset(load_manifest(save_manifest(tmp_path / "dup", data)), root)


def test_rejects_unsupported_labels_and_wrong_schema_version(tmp_path):
    root, image_path, mask_path = files(tmp_path)
    data = manifest(supported_labels=["unknown"])
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError, match="unknown labels"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
    data = manifest(label_schema_version=1)
    add_hashes(data["records"][0], image_path, mask_path)
    with pytest.raises(ValueError, match="schema"):
        validate_dataset(load_manifest(save_manifest(tmp_path, data)), root)
