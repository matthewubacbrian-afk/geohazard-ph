# Source-Safe Offline Risk Training — Design

**Date:** 2026-10-14

## Problem

`ml.train.run_training(download=False)` currently discovers every CSV under
`ml/data/raw/` as a PHIVOLCS file when the caller omits source paths. The
PowerShell wrapper and Python CLI expose only this implicit offline route.
USGS timestamps then receive PHIVOLCS Manila-time normalization, and training
metadata reports zero USGS input rows. A fixture reproduction reported four
PHIVOLCS rows and zero USGS rows from two rows of each source. This can change
deduplication and regional features without an obvious training failure.

Offline artifacts also record `datasets[].version` as `null`, with no way to
identify the exact CSV contents used for a retrain.

## Goals

- Require explicit PHIVOLCS and USGS CSV assignments for offline training.
- Make those assignments available through repeatable Python CLI flags and
  corresponding PowerShell wrapper parameters.
- Reject missing, non-CSV, or duplicate input paths before training writes an
  artifact bundle. Reject explicit CSV paths in download mode.
- Record each input file's source, filename, byte count, and SHA-256 digest in
  `metadata.json` for both offline and downloaded training.
- Preserve existing dataset version behavior: resolved Kaggle versions for
  downloads and `null` for offline inputs.
- Document the source-specific commands and the remaining need for real data
  and live staging verification.

## Non-goals

- No Kaggle download, source parser, K-Means, classifier, API, web, or mobile
  behavior changes.
- No automatic source inference from filenames or directory names.
- No generated model artifacts or raw datasets committed to Git.
- No claim that fixture training validates model quality on real snapshots.

## Context And Constraints

`ml/src/ml/clean_merge.py` normalizes PHIVOLCS timestamps from Asia/Manila and
USGS timestamps from UTC. `run_training` already accepts separate
`phivolcs_paths` and `usgs_paths`; only its offline default and command entry
points lose that distinction. The training corpus consists of both Kaggle
datasets listed in `docs/data-sources.md`. Follow `CODING_STANDARDS.md`,
`docs/glossary.md`, `docs/testing-standards.md`, and
`docs/error-handling-and-logging.md`.

## Alternatives Considered

1. **Explicit source flags (chosen):** The caller assigns every CSV to a
   source. This is auditable and works with files stored anywhere, at the cost
   of longer commands.
2. **Infer source from directory names:** This keeps a short command but relies
   on a naming convention outside the parser contract and can misclassify a
   manually moved file.
3. **Infer source from CSV headers:** This is convenient for known snapshots but
   the adapters accept overlapping aliases; an ambiguous file could be routed
   silently to the wrong timestamp rule.

## Design

### Architecture and data flow

`ml.train.main` accepts repeatable `--phivolcs-csv PATH` and `--usgs-csv PATH`
arguments with `--offline`. It forwards typed `Path` lists to `run_training`.
The PowerShell wrapper accepts `-PhivolcsCsv` and `-UsgsCsv` string arrays,
resolves paths before changing to `ml/`, and forwards the same flags. Download
mode continues to use the Kaggle dataset slug for source assignment.

Before normalization, `run_training` verifies that each source has at least
one file, every path identifies an existing `.csv` file, and no resolved file
appears more than once across the two groups. It sorts the resolved files for
stable processing. It rejects explicit paths when `download=True` so they are
never silently ignored. Each validated file contributes a record to
`metadata.json`:

```json
{
  "source": "usgs",
  "filename": "usgs_snapshot.csv",
  "size_bytes": 12345,
  "sha256": "64 lowercase hexadecimal characters"
}
```

The metadata field is `input_files`, ordered by source (`phivolcs`, then
`usgs`) and filename. It contains no local absolute paths. The file digest is
calculated in chunks so large historical CSVs need not be loaded into memory
again. Existing `datasets`, `source_reports`, `metrics`, and profile exports
remain in place.

### Components and interfaces

- `ml/src/ml/train.py`: add source-specific CLI flags, validate input groups,
  compute `input_files`, and pass validated lists to `load_and_merge_sources`.
- `scripts/train_risk_profile_models.ps1`: add source-specific array parameters
  and forward resolved paths to the Python CLI.
- `ml/tests/test_train.py`: cover CLI forwarding, rejected input cases, correct
  per-source reports, and digest records using small fixtures.
- `README.md`, `docs/data-sources.md`, `docs/glossary.md`, and
  `docs/project-status.md`: describe the command, provenance, and updated Epic 5
  capability accurately.

### Configuration

No new environment variables. The existing `--offline` or `-Offline` switch
selects local CSVs. Both source-specific argument groups are required in that
mode. Download mode remains the default.

### Error handling

Invalid source assignments raise `ValueError` with the missing source or path
named. The Python CLI catches it, prints a short failure to stderr, and exits
nonzero. The PowerShell wrapper propagates an invalid path or Python failure
as a failed command. No sample-data fallback is introduced.

### Data considerations

Source assignment controls timestamp conversion and deduplication. The digest
documents the exact bytes used, while offline `datasets[].version` remains
`null` because no Kaggle version is resolved. Source reports continue to
count accepted and rejected rows before cross-source deduplication.

## Rollout

Implement on `feat/offline-source-safe-training` from merged `main`. Land the
ML behavior and tests before updating the PowerShell wrapper and docs. Run the
ML suite and required repository checks, then open a PR. Existing offline
commands without explicit source lists must be updated by operators.

## Files

- `ml/src/ml/train.py` — source validation, manifest, CLI flags.
- `ml/tests/test_train.py` — source routing and metadata regression tests.
- `scripts/train_risk_profile_models.ps1` — source-specific wrapper parameters.
- `README.md` — offline training command and artifact explanation.
- `docs/data-sources.md` — provenance and source assignment guidance.
- `docs/glossary.md` — metadata field definition.
- `docs/project-status.md` — Epic 5 status after implementation.
- `docs/superpowers/plans/2026-10-14-offline-source-safe-training.md` — execution plan.

## Testing Strategy

Use existing PHIVOLCS and USGS CSV fixtures. First show that a missing source
fails before artifacts are created and that a valid pair reports two accepted
rows per source. Verify CLI argument forwarding, duplicate/missing file errors,
and SHA-256 values against the fixture bytes. Run `pytest -v` and `ruff check .`
from `ml/`, then `python scripts/verify_structure.py` and `git diff --check`
from the repository root. Review the PowerShell command syntax without using
real or secret datasets.

## Acceptance Criteria

- [ ] Offline CLI and PowerShell commands accept explicit repeatable paths for
      both sources; no implicit all-PHIVOLCS discovery remains.
- [ ] Missing, non-CSV, duplicate, or mis-mode input paths fail before an
      artifact bundle is written.
- [ ] Fixture training reports PHIVOLCS and USGS input rows separately.
- [ ] Metadata contains the input manifest and preserves dataset version rules.
- [ ] README, data-source guidance, glossary, and Epic 5 status match behavior.
- [ ] ML tests, Ruff, structure verification, and diff checks pass.

## Out Of Scope (backlog)

- Obtaining the Kaggle snapshots, training on real historical data, and
  deploying the resulting export to Oracle staging require separate operator
  inputs and live verification.

---

## Spec self-review

- The failure, source-sensitive behavior, file list, and acceptance checks are
  explicit and fit one ML-focused implementation plan.
- Each new metadata field and CLI argument is named; no placeholder remains.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-offline-source-safe-training.md`.
- Terminology: `docs/glossary.md`.
