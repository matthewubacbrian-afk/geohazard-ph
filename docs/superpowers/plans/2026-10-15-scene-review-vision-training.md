# Scene Review Vision Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rights-aware, reproducible offline workflow for training and evaluating Scene Review segmentation of open ground, obstacles, and visible hazard cues.

**Architecture:** Keep image training isolated under `ml/src/ml/scene_review/` from the existing earthquake-risk pipeline. Validate source/license provenance and indexed image masks before generating group-separated splits; fine-tune the pinned DETR panoptic model offline; evaluate against the pinned baseline; export only a reviewed, versioned artifact. Backend integration remains a separate follow-up after the held-out metrics and runtime review pass.

**Tech Stack:** Python 3.11+, PyTorch, Transformers, Pillow, NumPy, pytest, Ruff, JSON manifests, indexed PNG masks.

**Spec:** `docs/superpowers/specs/2026-10-15-scene-review-vision-training-design.md`

---

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/data-sources.md`, and `docs/testing-standards.md`; read `BACKEND_STANDARDS.md` only if a later task touches backend code.
- Keep scene-image training separate from regional risk-profile training and its artifact bundle.
- Work on the current `feat/scene-review-camera-controls` branch only after confirming it is the intended checkout. Stage only files in the task; preserve existing Scene Review edits and `.superpowers/brainstorm/`.
- Use Conventional Commits with one logical change per commit. Do not commit raw images, masks, weights, caches, credentials, or generated reports containing local paths.
- Dataset manifest paths are relative to a caller-provided data root. Reject absolute paths and path traversal. Do not log image pixels, image paths that contain user information, or private source credentials.
- Training is offline. The CLI must never download dataset content or model weights implicitly. Resolve and cache the pinned initialization model explicitly before training; fail clearly when absent.
- Annotation mask IDs are fixed: `0=open_ground`, `1=obstacle`, `2=glass_facade`, `3=overhead_lines`, `4=visible_building_damage`, `5=background`, `255=ignore`. Background is an annotation value only, never a prediction class; omit background regions from DETR targets so unmatched queries represent background. For each run, map canonical target pixels for unsupported classes to `ignore`, never `background`; count those pixels by class. Because stock DETR mask loss cannot ignore selected pixels, exclude every sample containing any run-mask ignore pixels from training and validation loss; evaluation metrics mask those pixels out. Record unsupported-pixel counts by class and total, ignore-containing, loss-eligible, and loss-excluded sample counts for training and validation, plus unsupported-pixel counts by class and total, ignore-containing, and evaluated sample counts for test; stop if remapping and exclusions leave insufficient samples. A run must explicitly declare the supported target-class subset and must not score omitted classes as successful.
- Clearly visible non-target pixels, including identifiable people, are `background`; use `ignore` only for genuinely ambiguous, occluded, or otherwise unlabelable pixels. Before full annotation/training, declare the maximum ignore-driven exclusion rate, minimum retained counts, and required scene/source coverage. Report the pilot excluded count/rate and retained counts by split and relevant slices. Stop and revise annotation/data collection/loss handling if the gate fails or exclusions leave insufficient or unrepresentative examples. Do not invent numeric thresholds after reviewing pilot results.
- Keep source/location/event/capture groups intact across splits. Exact image hashes must not appear in more than one split.
- Do not emit or document a safety verdict. Candidate scores are visual ordering only.
- `overhead_lines` means only visible overhead wires or cables; the model does not identify whether they are electrical, utility, energized/live, or another type/status.
- Write a failing test before each code behavior, run it to confirm the expected failure, implement the smallest change, then rerun focused and package verification.
- ML tests run from `ml/` with `pytest -v`; formatting uses `ruff check .`; run `python scripts\verify_structure.py` when the file tree changes and `git diff --check` before each commit.

## File Map

- `docs/superpowers/scene-review-annotation-guide.md`: boundaries, inclusion/exclusion examples, annotator workflow, ambiguity/ignore rules, and double-annotation review.
- `docs/data-sources.md`: source-level reuse findings and approved dataset inventory; do not mark a source approved without permission evidence covering training and intended model-weight use.
- `ml/pyproject.toml`: optional vision-training dependencies and CLI entry point, leaving base seismic dependencies unchanged.
- `ml/src/ml/scene_review/labels.py`: canonical label IDs, mask validation, and class-subset validation.
- `ml/src/ml/scene_review/manifest.py`: typed manifest records, source-rights checks, relative-path safety, content hashes, and image/mask validation.
- `ml/src/ml/scene_review/splits.py`: deterministic source-group split generation and leakage checks.
- `ml/src/ml/scene_review/dataset.py`: validated image/mask loading and conversion to the target format required by the selected segmentation model.
- `ml/src/ml/scene_review/train.py`: deterministic offline fine-tuning and checkpoint selection using validation data only.
- `ml/src/ml/scene_review/evaluate.py`: held-out metrics, slice reports, and baseline comparison.
- `ml/src/ml/scene_review/artifacts.py`: immutable model export and provenance metadata validation.
- `ml/src/ml/scene_review/cli.py`: `validate`, `split`, `train`, `evaluate`, and `export` subcommands.
- `ml/tests/test_scene_review_labels.py`, `test_scene_review_manifest.py`, `test_scene_review_splits.py`, `test_scene_review_dataset.py`, `test_scene_review_train.py`, `test_scene_review_evaluate.py`, `test_scene_review_artifacts.py`, `test_scene_review_cli.py`, and `test_scene_review_pipeline.py`: tiny fixtures and offline contract coverage.
- `docs/project-status.md`: update only with actual data readiness, metrics, hashes, and runtime evidence.

## Task 1: Review image-source rights and create the annotation guide

**Files:**
- Create: `docs/superpowers/scene-review-annotation-guide.md`
- Modify: `docs/data-sources.md`
- Test: N/A (documentation and source-rights review; do not download images during this task)

**Interfaces:**
- Annotation IDs and meanings must match the Global Constraints exactly.
- Source inventory rows record source, original image origin, terms/permission evidence URL, retrieval date/version, attribution, allowed training/evaluation use, model-weight redistribution status, and decision (`approved`, `excluded`, or `pending review`).

- [x] **Step 1: Inspect source terms** for every candidate dataset using the dataset owner's documentation and, where images originate elsewhere, the original image source terms. Record why the evidence covers or fails to cover model training and intended weight use.
- [x] **Step 2: Write the annotation guide** with pixel boundary rules for each class, ignore conditions, indoor/outdoor examples to include, and explicit exclusions for inferred reinforcement, safety, energized wires, or actual falling-glass risk.
- [x] **Step 3: Define the annotation quality review**: double-annotate a pilot subset; compute agreement only where neither mask is ignore; separately report one-sided-ignore disagreement, both-ignore coverage, jointly labelable coverage, per-class metrics, and disagreement categories; adjudicate before expanding labels.
- [x] **Step 4: Record source decisions** in `docs/data-sources.md`; pending or excluded sources cannot be used by the training CLI.
- [x] **Step 5: Review the documentation** for consistent terminology, rights evidence, and no accidental claim that a dataset card license covers underlying images.
- [x] **Step 6: Commit** as `docs: define scene review dataset annotations`.

**Gate:** If no dataset has documented rights for the intended use, do not acquire it or train on it. Finish the source inventory and continue only with the offline pipeline mechanics; a real-scene training/evaluation run remains pending until an approved dataset is supplied or collected under explicit permission.

## Task 2: Define labels and validate indexed masks

**Files:**
- Create: `ml/src/ml/scene_review/__init__.py`
- Create: `ml/src/ml/scene_review/labels.py`
- Create: `ml/tests/test_scene_review_labels.py`

**Interfaces:**

```python
LABEL_IDS: dict[str, int]
BACKGROUND_ID: int
IGNORE_ID: int

def validate_mask(mask: numpy.ndarray, supported_labels: set[str]) -> None: ...
def mask_for_supported_labels(
    mask: numpy.ndarray, supported_labels: set[str],
) -> tuple[numpy.ndarray, dict[str, int]]: ...
def labels_for_ids(class_ids: set[int]) -> set[str]: ...
def training_id_map(supported_labels: Sequence[str]) -> dict[int, int]: ...
```

`LABEL_IDS` maps only the five canonical target labels to IDs `0`–`4`; `BACKGROUND_ID` is `5`, and `IGNORE_ID` is `255`. `validate_mask` checks canonical masks for dimensions, integer dtype, unknown IDs, and all-ignore masks; it accepts all five canonical target IDs regardless of the run subset. `mask_for_supported_labels` returns `(run_mask, remapped_pixel_counts_by_label)`. It copies the input mask, changes pixels for unsupported canonical target classes to `IGNORE_ID` (never background), and reports counts keyed by canonical label for metadata. Any resulting sample containing ignore pixels is loss-ineligible. A background-only mask is valid and produces no DETR targets. `training_id_map` maps only selected target IDs to contiguous model IDs; background is never mapped to a model class. Artifact metadata stores supported labels, remapping counts, and both training-map directions so inference can restore canonical labels.

- [ ] **Step 1: Write failing tests** for the exact IDs, valid canonical mask containing an unsupported target class, unsupported-pixel remapping to `255` (never `5`), remap counts, unknown ID, non-integer mask, wrong dimensions, all-ignore mask, background-only mask, and contiguous mappings for supported target-label subsets.
- [ ] **Step 2: Run** `pytest tests/test_scene_review_labels.py -v` from `ml/`; confirm failures are due to the missing functions or validation behavior.
- [ ] **Step 3: Implement** the label constants and public validation, remapping, and ID-mapping functions with type hints and no image I/O.
- [ ] **Step 4: Run** `pytest tests/test_scene_review_labels.py -v` and `ruff check src/ml/scene_review/labels.py tests/test_scene_review_labels.py` from `ml/`.
- [ ] **Step 5: Commit** as `feat: define scene review training labels`.

## Task 3: Add rights-aware dataset manifest validation

**Files:**
- Create: `ml/src/ml/scene_review/manifest.py`
- Create: `ml/tests/test_scene_review_manifest.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class SceneImageRecord:
    image_id: str
    image_path: str
    mask_path: str
    image_sha256: str
    mask_sha256: str
    group_id: str
    scene_type: str
    lighting: str
    occlusion: str
    image_quality: str
    source_image_id: str
    source_page_url: str
    original_image_source: str
    original_image_creator: str
    image_license_name: str
    image_terms_evidence_url: str
    image_retrieval_evidence_url: str
    image_release_or_retrieval_id: str
    image_rights_evidence_scope: str
    image_rights_evidence_reference: str
    image_rights_review_status: str
    image_rights_reviewer: str
    image_rights_decision_date: str
    image_rights_decision_reason: str
    image_permitted_uses: tuple[str, ...]
    image_derived_weight_status: str
    image_derived_weight_restrictions: str
    image_retention_limits: str | None
    image_attribution: str
    annotation_record_id: str
    annotation_provenance: str

@dataclass(frozen=True)
class SceneDatasetManifest:
    schema_version: int
    dataset_id: str
    source_url: str
    terms_evidence_url: str
    license_name: str
    retrieved_at: str
    retrieval_evidence_url: str
    immutable_release_or_retrieval_id: str
    rights_review_status: str
    rights_reviewer: str
    rights_decision_date: str
    rights_decision_reason: str
    permitted_uses: tuple[str, ...]
    derived_weight_status: str
    derived_weight_restrictions: str
    retention_limits: str
    attribution: str
    annotation_provenance: str
    label_schema_version: int
    supported_labels: tuple[str, ...]
    records: tuple[SceneImageRecord, ...]

def load_manifest(path: Path) -> SceneDatasetManifest: ...
def validate_dataset(
    manifest: SceneDatasetManifest,
    data_root: Path,
    *,
    split_by_image_id: Mapping[str, str] | None = None,
    sufficiency_policy: SufficiencyPolicy | None = None,
) -> DatasetValidationReport: ...

@dataclass(frozen=True)
class SufficiencyPolicy:
    maximum_exclusion_rate: float
    minimum_retained_samples_by_split: Mapping[str, int]
    required_scene_types_by_split: Mapping[str, tuple[str, ...]]
    minimum_retained_samples_by_scene_type: Mapping[str, int]
    minimum_retained_groups_by_split: Mapping[str, int]
    minimum_retained_samples_per_group_by_split: Mapping[str, int]
    required_group_ids_by_split: Mapping[str, tuple[str, ...]]

@dataclass(frozen=True)
class SampleExclusionSummary:
    total_sample_count: int
    excluded_sample_count: int
    retained_sample_count: int
    exclusion_rate: float

@dataclass(frozen=True)
class SplitExclusionSummary(SampleExclusionSummary):
    scene_type_summaries: Mapping[str, SampleExclusionSummary]
    group_summaries: GroupExclusionSummary

@dataclass(frozen=True)
class GroupExclusionSummary:
    total_group_count: int
    retained_group_count: int
    excluded_group_count: int
    minimum_retained_samples_per_group: int
    maximum_retained_samples_per_group: int

@dataclass(frozen=True)
class DatasetValidationReport:
    image_count: int
    pixel_counts: Mapping[str, int]
    unsupported_pixel_counts: Mapping[str, int]
    run_mask_ignore_pixel_count: int
    run_mask_ignore_sample_count: int
    loss_eligible_sample_count: int
    loss_excluded_sample_count: int
    exclusion_rate: float
    split_summaries: Mapping[str, SplitExclusionSummary]
    sufficiency_gate_passed: bool | None
    sufficiency_gate_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    manifest_sha256: str
    split_assignments_sha256: str
```

`label_schema_version` must be `2` (`scene-review-v2`). The source inventory in `docs/data-sources.md` is the candidate/review ledger; pending and excluded candidates stay there and must not be copied into a training manifest. A training manifest contains only approved dataset/image records, and validation explicitly rejects any non-approved status rather than silently filtering records. At dataset and image level, retain the reviewer, decision date, decision reason, terms evidence, exact immutable release/retrieval identifier and retrieval evidence URL, image/source and creator provenance, annotation provenance, attribution, permitted uses, derived-weight permission status, and explicit derived-weight restrictions. The dataset record also carries its annotation provenance and all source inventory fields; each `SceneImageRecord` carries source-image/page identifiers, original source/creator, image terms and retrieval evidence, rights decision fields, allowed uses, weight status/restrictions, attribution, and annotation record/provenance. `SceneDatasetManifest.retention_limits` is required and records the retention period/limits imposed by source terms; `SceneImageRecord.image_retention_limits` may be omitted only when the dataset-level limit applies unchanged, and is required when an image has a different source-specific retention term. Rights statuses are exactly `approved`, `pending_review`, or `excluded`; non-approved inventory entries require a decision reason. Both dataset-level permissions and every included record's `image_permitted_uses` must include `training`, `evaluation`, and `derived_weight_redistribution`; each dataset/image `derived_weight_status` must affirm redistribution and `derived_weight_restrictions` must state applicable conditions (use `none documented` only when the evidence supports no restrictions). Validation fails closed for missing, unresolved, or insufficient evidence, including a missing dataset retention limit or missing image override when terms differ. A shared grant URL is acceptable only if its written terms expressly cover the specific image; `image_rights_evidence_reference` must identify the image by stable source ID/page or expressly covered subset and point to the exact clause/scope, and that same evidence must support the per-image reviewer decision and all three uses. Generic dataset-card or repository terms do not qualify. Keep detailed rights fields in the local manifest/access-controlled local data root; CLI output is count-only. `DatasetValidationReport` reports canonical pixel totals, unsupported-pixel counts, and ignore-exclusion counts/rates by each declared split and controlled `scene_type` (`indoor`, `outdoor`, `mixed`, or `unknown`), plus retained counts and dataset totals. Each split also reports privacy-safe group aggregates only: distinct total/retained/excluded group counts and minimum/maximum retained samples among groups, including groups with zero retained samples. The report contains no image IDs, source/group IDs, paths, or arbitrary manifest text. `validate_dataset` uses the manifest's explicit `supported_labels` subset unless a future reviewed contract adds an explicit override. Split assignments are an explicit image-ID-to-`train`/`validation`/`test` mapping; a source group must remain within a single split; report keys are only controlled split and scene-type categories. A `SufficiencyPolicy` must be supplied with no numeric defaults to evaluate the gate: it declares maximum exclusion rate, minimum retained samples and groups per split, minimum retained samples per group, required scene types and required local group IDs per split, and any minimum retained count by scene type. Required group IDs are used only locally and must never appear in report fields, reasons, or warnings. The report returns `sufficiency_gate_passed=None` and a count-only undeclared-gate warning when no policy is supplied, allowing mechanics validation; training must fail closed unless the report says `True`. A declared gate reports generic reasons for excess exclusion, insufficient retained counts/groups, per-group shortfall, or missing required coverage; it does not invent thresholds or expose identifiers. Each split's group requirements must be explicitly declared with the policy; no group threshold is implicit. Validation also checks safe relative paths, file existence, SHA-256 values, JPEG/PNG readability, equal image/mask dimensions, valid canonical mask IDs, unique image IDs, and nonempty scene groups. Background ID `5` is valid; unsupported target IDs remain valid in canonical masks and are remapped to ignore for the run.

- [ ] **Step 1: Write failing tests** for an approved-only valid manifest; rejection of pending/excluded dataset or image records; missing reviewer, decision date/reason, release/retrieval evidence, dataset retention limits or required image-level retention override, image/creator or annotation provenance, attribution, derived-weight status/restrictions, and permission purposes; a shared grant that does not expressly cover the image; absolute/traversal paths; missing files; hash mismatch; invalid image/mask; dimension mismatch; duplicate IDs; unsupported-pixel remapping/counts; controlled scene-type categories; count-only split, scene-type, and aggregate group exclusion reports; no group/source identifiers in report output; source groups kept within one split; sufficiency-gate pass/failure for exclusion rate, retained counts, required scene/group coverage, retained group counts, and per-group retention; and absent-gate mechanics reporting/warning.
- [ ] **Step 2: Run** `pytest tests/test_scene_review_manifest.py -v`; confirm expected failures.
- [ ] **Step 3: Implement** dataclasses, JSON parsing, strict validation, file hashing, and a count-only report. Do not add network access.
- [ ] **Step 4: Run** `pytest tests/test_scene_review_manifest.py -v` and `ruff check src/ml/scene_review/manifest.py tests/test_scene_review_manifest.py`.
- [ ] **Step 5: Commit** as `feat: validate scene review dataset manifests`.

## Task 4: Generate deterministic group-separated splits

**Files:**
- Create: `ml/src/ml/scene_review/splits.py`
- Create: `ml/tests/test_scene_review_splits.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class DatasetSplits:
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]

def make_grouped_splits(
    records: Sequence[SceneImageRecord], *, seed: int = 42,
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
) -> DatasetSplits: ...

def validate_splits(records: Sequence[SceneImageRecord], splits: DatasetSplits) -> None: ...
```

Use a deterministic seeded shuffle of `group_id` values, then greedily assign whole groups to the split with the largest remaining target image count. Validate ratios sum to 1, every record appears exactly once, no group or image hash crosses splits, and all three splits are nonempty. Serialize sorted IDs and the seed as JSON.

- [ ] **Step 1: Write failing tests** for deterministic output, group isolation, hash leakage, ratio validation, duplicate/missing IDs, and insufficient group counts.
- [ ] **Step 2: Run** `pytest tests/test_scene_review_splits.py -v`; confirm expected failures.
- [ ] **Step 3: Implement** the split dataclass, algorithm, validator, and JSON serialization helper.
- [ ] **Step 4: Run** focused tests and Ruff for the changed files.
- [ ] **Step 5: Commit** as `feat: split scene images by source group`.

## Task 5: Load image/mask pairs for panoptic fine-tuning

**Files:**
- Create: `ml/src/ml/scene_review/dataset.py`
- Create: `ml/tests/test_scene_review_dataset.py`

**Interfaces:**

```python
class SceneReviewDataset:
    def __init__(self, manifest: SceneDatasetManifest, data_root: Path,
                 record_ids: Sequence[str], image_processor: DetrImageProcessor) -> None: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> dict[str, object]: ...
```

Load RGB images and canonical indexed PNG masks from the validated manifest. Call `mask_for_supported_labels` to obtain `(run_mask, remapped_pixel_counts_by_label)`; it remaps every canonical target pixel whose class is not in `supported_labels` to `ignore` (`255`), never `background` (`5`). Convert each connected component of a supported target class (`0`–`4`) into one DETR segmentation target with `class_labels`, `masks`, and `boxes`, matching the official [`DetrForSegmentation` training input](https://huggingface.co/docs/transformers/model_doc/detr#transformers.DetrForSegmentation). Do not make targets for `background` (`5`); unmatched DETR queries represent background. Convert target class IDs to contiguous training IDs using `training_id_map`. Return the run-specific ignore-pixel mask or equivalent per-sample flag. Use deterministic preprocessing; do not apply random augmentation in validation/test. Exclude any complete sample whose run-specific mask contains at least one `ignore` pixel from both training and validation loss because the stock mask loss treats outside-mask pixels as negatives. Evaluation metrics instead mask out all run-specific ignore pixels, including those remapped from unsupported classes. Record, for training and validation, total sample count, unsupported-pixel counts by canonical class, samples containing run-specific ignore pixels, loss-eligible sample count, and loss-excluded count; for test, record total, unsupported-pixel counts by canonical class, samples containing run-specific ignore pixels, and evaluated count. Stop if remapping and exclusions leave fewer samples than declared minimums. Never silently convert an unsupported class to background.

- [ ] **Step 1: Add tiny image and indexed-mask fixtures at runtime in tests** and write failing tests for RGB conversion, target class IDs, connected components, background-only samples, ignore-pixel masks/flags, ignored sample loss exclusion, empty class, and malformed dimensions.
- [ ] **Step 2: Run** `pytest tests/test_scene_review_dataset.py -v`; confirm expected failures.
- [ ] **Step 3: Implement** the dataset adapter against the pinned `DetrImageProcessor` interface. Add Pillow and NumPy to the optional vision extra only if absent from resolved transitive dependencies.
- [ ] **Step 4: Run** focused dataset and label tests plus Ruff.
- [ ] **Step 5: Commit** as `feat: prepare scene masks for panoptic training`.

## Task 6: Add pinned optional dependencies and deterministic training

**Files:**
- Modify: `ml/pyproject.toml`
- Create: `ml/src/ml/scene_review/train.py`
- Create: `ml/tests/test_scene_review_train.py`

**Interfaces:**

```python
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

def train_model(
    manifest: SceneDatasetManifest, splits: DatasetSplits,
    config: TrainingConfig, *, model_cache: Path,
) -> TrainingResult: ...
```

`TrainingResult` contains `checkpoint_path`, `best_epoch`, `best_validation_loss`, `seed`, `trained_labels`, and `training_metadata`. Metadata includes supported labels, code revision and dirty-worktree state, Python/dependency versions, initialization model revision, random seed, deterministic processor class/revision/configuration hash, epochs, batch size, learning rate, canonical manifest SHA-256, and per-split total, per-class unsupported-pixel, ignore-containing, loss-eligible, loss-excluded sample counts, exclusion rate, and retained counts by controlled scene-type slice. Do not include absolute local paths, per-image IDs, or rights evidence in this metadata. Before constructing the trainer or updating weights, training must call `validate_dataset` with the split assignment and required predeclared `config.sufficiency_policy`; fail closed unless `sufficiency_gate_passed is True`. Count-only mechanics validation may omit the policy, but such a report is not training authorization. Training and validation-loss calculations use only samples without run-specific ignore pixels; fail before training if the declared pilot exclusion-rate, minimum-count, or representation gate fails, or if remapping and exclusions leave fewer than the declared minimum samples.

Use `facebook/detr-resnet-50-panoptic` at revision `d53b52a799403a8867920f82c869e40732b47037` as initialization. Load local files only, replace the task classifier for the declared supported labels, set all random seeds, select checkpoints using validation loss, and never inspect test metrics during training. Before editing `pyproject.toml`, verify compatible CPU package versions for supported Python 3.11+ and the project’s Linux deployment target; add a `scene-review` optional dependency extra with explicit versions and documented install command, leaving base tabular installs unchanged.

Install from the `ml/` directory with the CPU wheel index first, then install the project extra:

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.12.0" "torchvision==0.27.0"
python -m pip install ".[scene-review]"
```

The exact PyTorch pair has an [official CPU install command](https://pytorch.org/get-started/previous-versions/); PyPI publishes CPython 3.11 Linux `manylinux_2_28` x86-64 and ARM64 wheels for [PyTorch 2.12.0](https://pypi.org/project/torch/2.12.0/). The [Transformers installation guide](https://huggingface.co/docs/transformers/installation) supports Python 3.10+ and PyTorch 2.5+. The DETR checkpoint config uses a timm backbone, so the optional extra also pins `timm`; the [official backbone docs](https://huggingface.co/docs/transformers/main_classes/backbones) describe timm-backed model initialization.

- [x] **Step 1: Write failing tests** for config validation including required declared sufficiency thresholds, missing local checkpoint failure, refusal to train when the validation report has no declared/passing sufficiency gate, deterministic seed propagation, class-head mapping, validation-only checkpoint selection, and no test split use.
- [x] **Step 2: Run** `pytest tests/test_scene_review_train.py -v`; confirm expected failures without downloads.
- [x] **Step 3: Implement** training entry function and result metadata. Keep model loading injectable so unit tests use a fake model and trainer.
- [x] **Step 4: Run** unit tests and a synthetic injected-runtime pipeline into `tmp_path`; label the output as pipeline-mechanics verification only.
- [x] **Step 5: Resolve and install** the optional dependency extra in an isolated environment; verify the pinned checkpoint loads from a local cache with network access disabled. Verified on Windows with Python 3.11 and CPU PyTorch 2.12.0: installed the complete extra, cached only the pinned 172 MB checkpoint/config/processor files, then loaded the resized two-label model and image processor with `local_files_only=True`, `HF_HUB_OFFLINE=1`, and `TRANSFORMERS_OFFLINE=1`. This was a load check only; no training data was used and no training was started.
- [x] **Step 6: Run** ML package verification and inspect dependency changes for unintended updates to the base seismic environment. The existing base dependencies are unchanged.
- [ ] **Step 7: Commit** as `feat: fine tune scene review segmentation model`.

## Task 7: Evaluate held-out scenes and compare with the baseline

**Files:**
- Create: `ml/src/ml/scene_review/evaluate.py`
- Create: `ml/tests/test_scene_review_evaluate.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class EvaluationThresholds:
    minimum_iou_by_label: Mapping[str, float]
    minimum_precision_by_label: Mapping[str, float]
    minimum_recall_by_label: Mapping[str, float]
    maximum_false_cue_rate: float
    maximum_false_cue_rate_regression: float
    maximum_metric_regression_by_label: Mapping[str, float]
    open_ground_component_overlap_iou: float
    minimum_open_ground_component_coverage: float
    maximum_open_ground_component_coverage_regression: float
    minimum_prediction_score: float
    minimum_samples_per_slice: int

def evaluate_model(model: object, dataset: SceneReviewDataset,
                   thresholds: EvaluationThresholds, *, splits: DatasetSplits,
                   sufficiency_report: DatasetValidationReport) -> EvaluationReport: ...
def compare_to_baseline(candidate: EvaluationReport,
                        baseline: EvaluationReport) -> BaselineComparison: ...
```

`EvaluationReport` contains `per_label_iou`, `per_label_precision`, `per_label_recall`, true/false-positive and false-negative pixel counts, `false_visual_cue_rate`, `open_ground_component_coverage`, `slice_metrics`, `sample_counts`, unsupported-pixel counts, threshold failures, and a fingerprint of the exact held-out test records. False visual-cue rate is the fraction of predicted non-ground cue components without a same-class ground-truth component match at or above the declared overlap IoU. Open-ground component coverage is the fraction of ground-truth connected open-ground components that overlap a predicted component at or above that same declared IoU. Slice reports include controlled scene-type, lighting, occlusion, and image-quality categories; unknown free-text values map to `other`. Source-group reporting contains aggregate counts and metric ranges without group identifiers.

Evaluation requires a declared passing Task 3 sufficiency report whose `manifest_sha256` matches the canonical current manifest and whose `split_assignments_sha256` matches the exact current train/validation/test assignment. Image-count and test-count matches alone do not authorize evaluation. The evaluation dataset's record IDs must exactly equal `splits.test_ids`. Fingerprints are internal validation values; reports must not expose image IDs. Baseline comparison requires an identical held-out-record fingerprint and matching prediction/overlap thresholds. All metric, false-cue, component-coverage, and slice-count thresholds are explicit inputs with no defaults; feature owners declare them before evaluating the held-out set. These thresholds are not tuned against test results.

Compute IoU, precision, and recall at pixel level for each supported target class using only non-ignore pixels in the run-specific mask; background pixels are negatives, while original ignore pixels and unsupported-class pixels remapped to ignore are absent from metric denominators. Report per-class unsupported-pixel counts, per-class metrics, false visual-cue rate, open-ground component coverage, total/ignore-containing/evaluated sample counts, ignore exclusion counts/rates and retained counts by split and relevant slices, and slices by scene type, lighting, occlusion, image quality, and source group where sample counts meet the declared minimum. Fail acceptance if the predeclared exclusion-rate, retained-count, or representation gate fails, required thresholds are absent, or any supported class regresses beyond `maximum_metric_regression_by_label` against baseline. Thresholds are written before full annotation/training and before the held-out test run; no tuning uses test results.

- [x] **Step 1: Write failing tests** with synthetic predictions for metric correctness, empty classes, insufficient slice counts, threshold enforcement, and baseline comparisons.
- [x] **Step 2: Run** `pytest tests/test_scene_review_evaluate.py -v`; confirm expected failures.
- [x] **Step 3: Implement** pure metric/report functions, then the prediction loop over held-out examples.
- [x] **Step 4: Run** focused metric tests and Ruff.
- [ ] **Step 5: Execute the real-scene held-out evaluation only when Task 1 rights and annotation gates pass.** This remains unrun because no approved scene images or feature-owner-declared numeric thresholds are available. When those gates pass, record dataset manifest hash, model/code revision, thresholds, metrics, runtime, and uncovered slices; keep images and report out of Git unless the report is scrubbed of local/private data.
- [x] **Step 6: Commit** as `feat: evaluate scene review segmentation quality`.

## Task 8: Export immutable artifact and document readiness

**Files:**
- Create: `ml/src/ml/scene_review/artifacts.py`
- Create: `ml/tests/test_scene_review_artifacts.py`
- Create: `ml/tests/test_scene_review_cli.py`
- Create: `ml/tests/test_scene_review_pipeline.py`
- Create: `ml/src/ml/scene_review/cli.py`
- Modify: `docs/project-status.md`

**Interfaces:**

```text
scene-review validate --manifest PATH --data-root PATH
scene-review split --manifest PATH --data-root PATH --seed 42 --output PATH
scene-review train --manifest PATH --data-root PATH --splits PATH --model-cache PATH --output-dir PATH
scene-review evaluate --manifest PATH --data-root PATH --splits PATH --checkpoint PATH --thresholds PATH --output PATH
scene-review export --checkpoint PATH --evaluation PATH --metadata PATH --version VERSION --output-root PATH
```

Register `scene-review = "ml.scene_review.cli:main"` under `[project.scripts]` in `ml/pyproject.toml`; these commands run after installing the project with the `scene-review` optional extra.

Artifact export writes only under `ml/model_artifacts/scene_review/<version>/`, refuses overwrite, verifies passing evaluation and complete provenance, records model/dataset/code hashes, supported labels, labels, thresholds, metrics, runtime versions, per-split unsupported-pixel counts by canonical class, total/ignore-containing/loss-eligible/loss-excluded counts and exclusion rates for training and validation, test total/ignore-containing/evaluated counts, and limitations, and never copies raw images, per-image rights records, or absolute local paths. Detailed per-image rights metadata remains in the local manifest/access-controlled data root; CLI success/error reports expose aggregate counts only, never per-image IDs, URLs, attribution, or paths.

- [ ] **Step 1: Write failing tests** for each CLI command, nonzero errors, refusal on pending rights or failed thresholds, immutable version path, metadata completeness, and absence of image/path content.
- [ ] **Step 2: Run** `pytest tests/test_scene_review_artifacts.py tests/test_scene_review_cli.py -v`; confirm expected failures.
- [ ] **Step 3: Implement** export validation, command argument parsing, and artifact metadata serialization.
- [ ] **Step 4: Run** all focused tests; then `pytest -v` and `ruff check .` from `ml/`.
- [ ] **Step 5: Run** the synthetic end-to-end pipeline test; verify it writes only under pytest `tmp_path` and uses a fake model with no network access.
- [ ] **Step 6: For an approved real dataset only,** run the held-out evaluation from Task 7, then load the exported artifact with network access disabled and record one-image CPU latency and peak resident memory on the target backend environment.
- [ ] **Step 7: Run** `python scripts\verify_structure.py` and `git diff --check` from the repository root.
- [ ] **Step 8: Update project status** with only verified outcomes. If rights/data gates are not met, state that training is pending approved labeled data and report only pipeline-mechanics checks; do not mark model recognition validated.
- [ ] **Step 9: Commit** as `feat: export reviewed scene review model artifacts`.

## Completion Gate

The training pipeline is complete when all code and documentation tasks pass and the artifact gate is exercised. A real model-quality result is complete only when a rights-approved, sufficiently annotated dataset passes held-out acceptance thresholds. If no such dataset is available, report the exact data-readiness blocker and leave real-scene training and model acceptance pending. Do not update `backend/app/services/scene_analysis_model.py`, change the SceneAnalysis API, or deploy the artifact in this plan.

## Notes for the executor

- Do not create a new worktree until implementation begins; this plan is documented on the current feature branch, which contains unrelated uncommitted camera-work changes. At execution, use the `using-git-worktrees` skill and start a clean worktree from the branch containing this plan, then stage and commit only planned files.
- The spec intentionally puts backend integration in a later plan. This plan ends with a locally exported artifact and evaluation evidence.
- Verify the annotation guide and dataset permissions before any real image download or training run. A model card or code license is not sufficient to clear image rights.
