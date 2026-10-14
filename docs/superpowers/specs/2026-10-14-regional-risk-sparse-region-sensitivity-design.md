# Regional Risk Sparse-Region Sensitivity — Design

**Date:** 2026-10-14

## Problem

The held regional risk-profile export has only five assigned events for NCR and
three NCR events in the common PHIVOLCS/USGS observation window. Its label is
therefore sensitive to which regions participate in clustering. The offline
validation report already records one leave-one-region-out comparison, but it
does not show how conclusions change across minimum-event count scenarios.
Reviewers need a repeatable view of that sensitivity before defining a
sparse-region policy.

## Goals

- Add an offline sensitivity section to `ml.validate_profiles` that measures
  label changes across minimum shared-window event-count cutoffs.
- Derive the cutoff transitions from the observed per-region counts so the
  report does not embed an unsupported policy value.
- For each cutoff, record the threshold, included and excluded regions, fitted
  labels when available, and changes from saved labels among included regions.
- Render the same evidence in JSON and Markdown, and keep every report in
  `requires_domain_review` state.
- Preserve the saved artifact bundle, training behavior, API behavior, and
  staging quality hold.

## Non-goals

- Do not select or recommend a minimum event count.
- Do not change saved risk labels, confidence values, training output, or the
  API/web/mobile response or display.
- Do not claim that a shared date window equalizes catalog completeness,
  source reporting thresholds, or event-detection probability.
- Do not approve the export, introduce a sparse-label in production, download
  data, or deploy to OCI.

## Context And Constraints

`ml/src/ml/validate_profiles.py` verifies saved inputs and currently reports
source coverage, a shared observation window, shared-window label refits, seed
sensitivity, and leave-one-region-out sensitivity. It builds refit features
from assigned rows inside the shared window. The held bundle's labels remain
unchanged. The current shared-window combined event counts range from three in
NCR to tens of thousands in several regions, so fixed example cutoffs could
make the report appear to endorse a policy.

The new analysis will use the combined PHIVOLCS and USGS count inside the
existing shared observation window only to decide whether a region enters a
scenario. It will use shared-window features for refitting. Counts by source
remain available beside these scenarios so readers can see the source mix.
Catalog completeness and reporting thresholds remain unequal. All refit
comparisons use the validator's documented current K candidates and fixed
seed; original training settings are still unverified.

Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`,
`docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and
`docs/git-workflow.md`. Keep reports and raw source files ignored and local.

## Alternatives Considered

1. **Data-derived cutoff transitions (chosen):** Evaluate zero plus each
   distinct observed region count plus one. This shows every point where the
   included set changes without choosing a scientific cutoff. The output is a
   sensitivity curve, not a policy recommendation.
2. **Fixed cutoff grid:** Simple to explain, but any chosen values could be
   mistaken for approved minimums and might miss transitions in this dataset.
3. **Counts-only report:** Avoids refits and policy implications, but does not
   answer how clustering labels respond when low-count regions are excluded.

## Design

### Architecture and data flow

After provenance verification and coverage calculation, the validator will
build the same regional feature rows already used for the shared-window refit.
It will sum each region's PHIVOLCS and USGS counts in that window. It will
derive a deterministic sequence of minimum-count thresholds: `0`, followed by
`count + 1` for each distinct observed region count. Each threshold therefore
represents one unique included-region set as the minimum count increases.

For each threshold, include a region only if it has a shared-window feature row
and its combined count is at least the threshold. Record excluded region names
and a reason (`below_minimum_event_count` or
`no_shared_window_observations`). If fewer than two feature rows remain, do not
fit K-Means; record `labels: null`, `change_count: null`, and
`unavailable_reason: insufficient_regions`. Otherwise fit with the current
`REFIT_K_CANDIDATES` and `REFIT_RANDOM_STATE`; compare refit labels to saved
labels only for included regions.

The result is added under `sparse_region_sensitivity` in the JSON report. Its
`count_basis` is `combined_sources_in_shared_window`; its
`thresholds_are_policy` field is always `false`; and each scenario contains:
`minimum_shared_window_events`, `included_regions`, `excluded_regions`,
`exclusion_reason_by_region`, `labels`, `changed_regions`, `change_count`, and
`unavailable_reason`. Regions and maps use deterministic name ordering.

Markdown will include one row per scenario with threshold, included/excluded
region counts, changed-label count, and unavailable reason. A following
compact list will identify included/excluded regions for each scenario. The
section will say explicitly that thresholds are data-derived breakpoints, not
recommended policy cutoffs, and that source completeness remains unequal.

### Components and interfaces

- `ml/src/ml/validate_profiles.py`: add a pure helper
  `_sparse_region_sensitivity(region_coverage: list[dict[str, object]],
  saved_labels: dict[str, str], shared_features: list[RegionFeatures]) ->
  dict[str, object]` and include its result in `build_validation_report` and
  `_render_markdown`.
- `ml/tests/test_validate_profiles.py`: cover deterministic thresholds,
  inclusive boundary behavior, source-count combination, saved-label
  comparisons for included regions, exclusion reasons, insufficient-region
  fits, and Markdown output.
- `docs/glossary.md`: define the report term `event-count cutoff sensitivity`
  as an exploratory comparison of regional profile inclusion and label changes
  across minimum shared-window event counts; it does not determine a policy.
- `docs/risk-profile-quality-review-2026-10-14.md`: record the generated
  sensitivity evidence and reiterate that the export remains held.
- `docs/project-status.md`: update Epic 5 evidence and next steps after the
  report is regenerated.
- `README.md`: document the updated JSON/Markdown report contents and command
  behavior if its usage changes; no CLI option is planned.

No API, database, frontend, configuration, or dependency change is required.

### Error handling

The helper consumes validated coverage counts and shared-window features. A
saved region absent from the coverage list represents zero assigned rows and
is recorded as excluded for `no_shared_window_observations`. A present region
entry with a missing source count, a negative count, or a region name absent
from saved labels raises `ValueError`. Existing CLI handling prints the
validation error and returns a nonzero exit code before writing outputs. A
scenario with too few regions is an expected unavailable result, not an error.

### Data considerations

Counts are integers from assigned canonical source rows after deduplication
and the existing 100 km offshore assignment. The cutoff uses the sum of the
two source counts within the shared UTC window. It is a coverage scenario only;
it does not normalize different source thresholds or claim a per-year rate.
The held artifact files and their hashes must remain unchanged.

## Rollout

Implement in one isolated feature branch. Regenerate ignored local JSON and
Markdown reports from the exact saved CSVs and bundle after unit verification.
Commit code and the explanatory documentation only; do not commit generated
reports, source data, or model artifacts. Integrate through a PR after relevant
checks pass. The quality hold remains in force.

## Files

- `ml/src/ml/validate_profiles.py` — compute and render cutoff sensitivity.
- `ml/tests/test_validate_profiles.py` — fixture tests for scenarios and edge
  cases.
- `docs/glossary.md` — define the new report term.
- `docs/risk-profile-quality-review-2026-10-14.md` — append full-data results.
- `docs/project-status.md` — update Epic 5 status after results are recorded.
- `README.md` — clarify report contents if needed.
- `docs/superpowers/specs/2026-10-14-regional-risk-sparse-region-sensitivity-design.md`
  — this design.
- `docs/superpowers/plans/2026-10-14-regional-risk-sparse-region-sensitivity.md`
  — implementation plan.

## Testing Strategy

Use tiny ML fixtures with controlled source rows and saved labels. Assert that
thresholds are sorted, unique, and equal to zero plus each distinct combined
shared-window count plus one. Assert a region exactly at a threshold is
included, and a region just below it is excluded. Verify PHIVOLCS and USGS
counts are summed only within the shared window, an absent coverage entry is
treated as zero, malformed coverage fails before writing, all exclusions have
a reason, and changed-label counts compare only included regions. Verify no
fit is attempted for fewer than two feature rows and the report still renders
deterministically in JSON and Markdown. Run the full ML test suite, Ruff on
the touched Python files, `python scripts/verify_structure.py`, and
`git diff --check`.

The local full-data run must verify all 17 regions, remain
`requires_domain_review`, preserve source/boundary hashes, and leave every held
bundle file unchanged.

## Acceptance Criteria

- [ ] JSON includes a deterministic `sparse_region_sensitivity` section with
  all data-derived inclusion transitions and no selected policy.
- [ ] Markdown explains the transitions and shows included/excluded regions
  and label-change counts for every scenario.
- [ ] Shared-window features and source counts are used consistently; saved
  labels are only comparison references.
- [ ] Insufficient scenarios are recorded without a K-Means fit or CLI failure.
- [ ] Unit tests cover cutoff boundaries, calculations, rendering, and
  unavailable scenarios.
- [ ] The full local report runs against the saved bundle without modifying
  it; export status remains held.
- [ ] ML tests, Ruff, structure verification, and diff checks pass.
- [ ] Status and quality-review documentation describe the evidence without
  treating it as a domain-approved policy.

## Out Of Scope (backlog)

- Selecting a sparse-region cutoff with a seismic-domain stakeholder.
- Defining label semantics or revising feature units, weights, or category
  descriptions.
- Refreshing source catalogs with verified Kaggle dataset versions or
  establishing catalog completeness.
- Releasing the export to staging or deploying a risk-profile endpoint.

## Spec self-review

- No placeholder text remains.
- Goals map to the JSON/Markdown behavior, tests, full-data check, and status
  update in the acceptance criteria.
- All threshold comparisons use the shared-window count and shared-window
  features consistently.
- Unavailable scenarios and exclusion reasons have explicit values.
- Scope is limited to one offline ML report enhancement and its documentation.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-regional-risk-sparse-region-sensitivity.md`.
- Terminology: `docs/glossary.md`.
