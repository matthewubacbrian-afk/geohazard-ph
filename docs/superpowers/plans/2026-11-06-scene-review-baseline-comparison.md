# Scene Review Baseline Comparison — Implementation Plan

> **For agentic workers:** Use test-driven-development and verification-before-completion.

**Goal:** Add an offline, same-sample comparison with the pinned DETR baseline.

**Architecture:** `evaluate --baseline-model-cache` loads the immutable
pretrained model revision and its processor from an existing local cache. The
baseline uses the same held-out manifest records and decoding thresholds as the
candidate. Compare ground metrics and report unsupported cues as unavailable.

**Tech Stack:** Python 3.11+, PyTorch, Transformers, NumPy, pytest.

## Global Constraints

- Follow the repository ML, test and documentation standards.
- Keep existing candidate-only calls compatible and preserve the strict export gate.
- Use only cached model files and rights-approved manifest inputs.
- Keep private paths and image IDs out of CLI output.

### Task 1: Evaluate and report baseline coverage

**Files:** Update `ml/src/ml/scene_review/evaluate.py`,
`ml/src/ml/scene_review/cli.py`, and their tests. Update `README.md` and
the project status and vision-training plan.

**Interfaces:** `scene-review evaluate --baseline-model-cache PATH` attaches
`baseline_comparison` and `baseline_coverage` to the existing report. The
coverage contains the pinned ID and revision, test split fingerprint and
comparable and unsupported labels. The command exits 2 for an incomplete or
failing comparison and preserves its diagnostic report.

- [x] Test actual decoding and aggregation of mapped ground predictions,
  unsupported labels, changed held-out identity and CLI forwarding.
- [x] Run the tests and observe the expected failures before implementation.
- [x] Reuse the existing decoder and comparison policy. Count floor and ground
  classes as `open_ground`. Report absent cue metrics as null.
- [x] Run the full offline ML suite, Ruff, structure and whitespace checks.
- [x] Review the diff before updating the training PR.

## Notes for the executor

The pinned taxonomy lacks directly mapped visual cues. Preserve the incomplete
comparison as evidence while retaining the export hold for unavailable metrics.

Verification on 2026-11-06 covered 221 offline ML tests and inference with the
cached pinned checkpoint on a synthetic image.
