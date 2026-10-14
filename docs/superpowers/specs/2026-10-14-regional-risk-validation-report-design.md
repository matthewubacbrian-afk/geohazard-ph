# Regional Risk Validation Report — Design

**Date:** 2026-10-14

## Problem

The local Epic 5 bundle is structurally valid, but its risk labels are on quality hold. The
[technical review](../../risk-profile-quality-review-2026-10-14.md) found only five events assigned
to NCR, unequal PHIVOLCS and USGS observation spans, and labels that change when NCR is removed.
The current `ml/src/ml/train.py` metadata gives only source totals and in-sample model metrics.
Reviewers need repeatable per-region coverage and label-stability evidence before deciding how to
revise the model or consider any export for staging.

## Goals

- Produce a repeatable, offline validation report for an existing versioned artifact bundle and
  explicitly supplied PHIVOLCS and USGS CSV files.
- Verify the supplied input-file SHA-256 values and regional boundary SHA-256 against the bundle's
  `metadata.json` before analysis. Recompute parser and assignment counts and compare them with
  recorded metadata, so the report is tied to the same data and assignment rule.
- Show each region's assigned event count by source and UTC observation span, plus each source's
  overall assigned span. Define the shared observation window as the intersection of those two
  overall spans; show per-region counts in that window.
- Compare the saved labels with labels refit on the shared-window rows, and quantify sensitivity
  across K-Means seeds 0–19 and leave-one-region-out refits using the saved regional features.
- Write machine-readable `validation-report.json` and readable `validation-report.md` to an
  explicitly selected ignored output directory. Always state `requires_domain_review`; no report
  result automatically approves or publishes the bundle.

## Non-goals

- No change to `risk_profiles.json`, model files, training labels, API responses, or web display.
- No earthquake forecast, calibrated confidence claim, official hazard designation, or numerical
  pass threshold invented without domain review.
- No Kaggle download, external service call, OCI deployment, or source-license conclusion.
- No attempt to make source counts scientifically comparable by windowing alone; reporting
  thresholds and catalog completeness remain review questions.

## Context And Constraints

`ml/src/ml/clean_merge.py` parses and deduplicates source rows; `ml/src/ml/regions.py` assigns
events to the pinned 17-region boundary asset, including events within 100 km offshore.
`ml/src/ml/features.py` builds regional summaries and `ml/src/ml/clustering.py` assigns labels.
The saved bundle contains `metadata.json`, `region_features.csv`, and `risk_profiles.json`.
Its two offline source versions are unknown, so exact file hashes are the only provenance claim.
Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`,
`docs/error-handling-and-logging.md`, and `docs/git-workflow.md`. Generated reports and raw CSVs
remain outside Git under ignored local paths.

## Alternatives Considered

1. **Reproducible offline report (chosen):** Adds a small command and testable analysis functions.
   It supplies evidence for review while preserving the held artifact and current user behavior.
2. **One-off notebook or spreadsheet:** Faster to draft, but harder to repeat against a refreshed
   snapshot and easier to disconnect from recorded hashes and assignment rules.
3. **Automatic training rejection or label change:** Could prevent weak exports, but a numerical
   threshold or revised category meaning needs scientific agreement that this project lacks.

## Design

### Architecture and data flow

`python -m ml.validate_profiles` accepts `--artifact-dir`, repeatable `--phivolcs-csv` and
`--usgs-csv`, and `--output-dir`. It validates paths and hashes, reads the saved profiles and
metadata, then reuses the existing source normalization, deduplication, and region assignment.
It compares recomputed source and assignment totals with metadata before building report rows.
Pure report functions compute coverage and label comparisons. The command writes JSON and Markdown
only after all validation succeeds. It never writes to the input artifact directory.

### Components and interfaces

- `ml/src/ml/validate_profiles.py`: `build_validation_report(artifact_dir: Path,
  phivolcs_paths: list[Path], usgs_paths: list[Path]) -> dict[str, object]` computes the report;
  `main(argv: list[str] | None = None) -> int` exposes the CLI and writes two files to the
  required `--output-dir` only on success. File paths may be absolute or relative to invocation.
- `validation-report.json`: `artifact_version`, `input_files`, `boundary_sha256`,
  `assignment_rule`, `source_coverage`, `shared_window`, `regions`, `label_stability`,
  `review_state: "requires_domain_review"`, and `limitations`. `regions` is sorted by
  `region_name`; each entry has `assigned_by_source`, `first_occurred_at_by_source`,
  `last_occurred_at_by_source`, and `shared_window_count_by_source`. UTC datetimes use ISO 8601.
- `label_stability` contains saved labels, shared-window refit labels for regions with usable
  shared-window rows, seed-sweep change counts per region (20 fits), and leave-one-region-out
  change counts for every retained region (16 comparable refits per region). Unavailable
  comparisons have an explicit reason, not an invented label.
- `validation-report.md`: concise tables of source and regional coverage, changed-label counts,
  limitations, and the review hold. It contains no raw event rows or local source paths.
- `ml/tests/test_validate_profiles.py`: small fixtures and synthetic saved bundles cover
  provenance mismatch, count mismatch, empty overlap, deterministic report ordering, comparison
  counts, and no output on failure.
- `README.md`, `docs/data-sources.md`, `docs/project-status.md`, and the quality review: explain
  how to run and interpret the report and record the observed local result without publishing it.

### Comparison semantics

The shared window is inclusive from the later source minimum to the earlier source maximum,
computed from assigned deduplicated events. A missing or empty intersection, or fewer than two
regions with events in that window, is reported and skips the shared-window refit. Otherwise use
the existing feature builder and `fit_kmeans` defaults on regions with at least one event in the
window; compare labels only for those regions. Seed sweep fits the saved regional features with
seeds 0–19. Leave-one-region-out
fits remove each region in turn and compare labels of the other regions against saved labels.
Each comparison records its included region set, so label shifts caused by changing membership
are visible. The existing metadata does not record the training K candidates or random seed;
the report records its own K candidates 3–5 and seeds, and explicitly marks parameter matching
to the original run as unverified. These are sensitivity checks, not external validation or
predictive accuracy.

### Configuration

No environment variables or API settings. CLI paths are required. The report records the
current fixed 100 km offshore assignment rule from metadata and rejects any unsupported rule
instead of silently using a different one. Seed range and K choices match the current training
defaults and are recorded in the report.

### Error handling

Missing bundle files, missing source CSVs, duplicate path assignment, hash mismatch, malformed
metadata, or recomputed count mismatch raise `ValueError` with the offending field or path.
The CLI prints a short reason to stderr and exits nonzero. The output directory is not created
until inputs and report calculations have succeeded. A scientifically weak or unstable result is
still a successful report with `requires_domain_review`, not a command failure.

### Data considerations

Source reports count parsed rows before deduplication; assignment counts follow deduplication.
Regional coverage uses assigned deduplicated rows. The shared window aligns dates, but cannot
correct reporting thresholds, catalog completeness, or exposure. The existing `event_density`
is a coordinate-spread proxy. A classifier's in-sample accuracy and confidence are not validation
metrics; the report calls this out. No raw event rows or local file paths appear in report output.

## Rollout

Add the report command and fixture tests, then run the ML suite and repository structure and
diff checks. Generate a report locally from the held bundle and exact saved source files; inspect
its values and document the observed result. Keep the generated files ignored and the staging
export on hold. Open a PR with source and documentation; merge only after review and CI.

## Files

- `ml/src/ml/validate_profiles.py` — provenance checks, coverage, comparisons, serialization, CLI.
- `ml/tests/test_validate_profiles.py` — offline deterministic success and failure coverage.
- `docs/glossary.md` — canonical meaning of validation report.
- `README.md` — operator command and report interpretation.
- `docs/data-sources.md` — source provenance and coverage caveats.
- `docs/project-status.md`, `docs/risk-profile-quality-review-2026-10-14.md` — current hold and
  local validation outcome.
- `docs/superpowers/plans/2026-10-14-regional-risk-validation-report.md` — execution plan.

## Testing Strategy

Use tiny fixture source CSVs and a temporary bundle built from them; no network or large source
files in tests. Verify path/hash/count failures before any report files are written. Assert exact
per-source/per-region counts and UTC windows, stable sort order, and recorded comparison counts.
Run `pytest -v` from `ml/`, `python scripts/verify_structure.py`, and `git diff --check`.
Run the command once against the held local bundle and inspect the generated report separately.

## Acceptance Criteria

- [ ] A CLI report for the held bundle verifies both source hashes and the boundary hash.
- [ ] The report reproduces source and assignment totals, all 17 region names, and per-region
      source counts and spans.
- [ ] The shared-window, seed-sweep, and leave-one-region-out sections show their included
      regions, parameters, and label-change counts without claiming external accuracy.
- [ ] Mismatched or missing inputs fail before output; empty overlap reports why comparison is
      unavailable.
- [ ] JSON and Markdown carry `requires_domain_review`; no model artifact or API behavior changes.
- [ ] ML tests, structure check, and diff check pass; generated reports remain ignored.

## Out Of Scope (backlog)

- Domain-stakeholder review of feature meaning, sparse-region policy, source catalog completeness,
  and category semantics before any release decision.
- Versioned source refresh and a revised training model.
- OCI host setup and deployed endpoint checks.

---

## Spec self-review

- The report inputs, hashes, comparison sets, failure paths, and outputs are explicit.
- Every goal has an acceptance criterion; the scope is one offline ML command and its docs.
- The report cannot promote a held export or imply scientific validation.

## Related documents

- Implementation plan: to be created as
  `docs/superpowers/plans/2026-10-14-regional-risk-validation-report.md`.
- Terminology: `docs/glossary.md`.
