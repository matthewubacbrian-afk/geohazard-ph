# Epic 5 Domain Review Decision Record — Design

**Date:** 2026-10-14

## Problem

Epic 5 has reproducible evidence showing instability in the held regional risk
profile export, but the next status-register milestone depends on seismic-domain
judgment. The evidence is documented in
`docs/risk-profile-quality-review-2026-10-14.md`; there is no concise place for a
qualified reviewer to record decisions, rationale, or remaining validation
without confusing exploratory results with approved policy.

## Goals

- Provide a concise, evidence-linked record for a seismic-domain review.
- Capture reviewer identity/role, date, evidence reviewed, decisions, rationale,
  unresolved questions, and follow-up actions.
- Make the 100 km assignment rule, unequal source coverage, sparse-region cutoff
  sensitivity, feature/label semantics, and export-release criteria explicit.
- Keep every decision unanswered by default and preserve the existing staging
  hold until a reviewed export meets documented criteria.

## Non-goals

- Select or recommend a sparse-region cutoff or change a risk label.
- Recompute model outputs, modify the held artifact, or create a release export.
- Claim official endorsement, calibrated hazard, forecasting, or prediction.
- Contact an external stakeholder or represent that a review occurred.

## Context And Constraints

- The quality review documents the saved bundle and CSV hashes, 17 regions,
  common observation window, 100 km assignment, and 18 exploratory cutoff
  scenarios. It records three NCR events in the shared window and label changes
  under refits.
- The quality review disposition is to hold the export from staging and
  user-facing risk guidance pending validation.
- `docs/project-status.md` is the authoritative status register. PR #30 merged
  the sensitivity report implementation; all required CI checks subsequently
  passed.
- Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/superpowers/templates/`
  and `docs/git-workflow.md`. This is a documentation-only change.

## Alternatives Considered

1. **Wait for a stakeholder before preparing review material.** This avoids
   writing a record, but does not reduce the effort needed to hold a structured
   review and leaves no common place for its outcome.
2. **Change the risk labels or select a cutoff from the current report.** This
   would convert exploratory comparisons into policy without the domain review
   already required by the quality hold, so it is rejected.
3. **Create a companion decision record linked to the quality review.** This
   keeps the quantitative evidence in one source of truth while providing a
   place to record domain decisions; this is the selected approach.

## Design

Create `docs/epic5-domain-review-decision-record.md` as an evidence-linked
Markdown worksheet. It will link to the current quality review, project status,
and relevant source-data assumptions. A short evidence summary will identify
the common observation window, source-coverage limitation, 100 km assignment,
NCR's shared-window count, and cutoff sensitivity. The quality review remains
the source for detailed numbers and methods.

The worksheet will have unfilled fields for reviewer name/role, review date,
and evidence versions/hashes reviewed. Its decision sections will ask the
reviewer to assess (1) the offshore assignment rule, (2) sparse-region
inclusion/cutoff policy, (3) source coverage and observation-window treatment,
(4) feature and category meaning, and (5) the validation evidence required to
lift the export hold. Each section provides fields for decision, rationale,
confidence/limitations, and follow-up owner/action. The sparse-region section
will list no preferred threshold; all options remain undecided until reviewed.

The closeout section will record one of `not_reviewed`, `review_incomplete`, or
`review_complete_hold_remains`, and identify any separately approved outcome.
There will be no field or wording that implies a completed review by default.
The export disposition will remain “held” unless a future, distinct review
updates the quality review and status register with the reviewed export version,
input hashes, and approval rationale.

## Rollout

Documentation-only, on a feature branch. Add the decision record and update
`docs/project-status.md` to record PR #30's completed checks and link the review
worksheet as the next action. Preserve all existing Epic 5 hold language. No
artifact, model, endpoint, or runtime behavior changes.

## Files

- `docs/epic5-domain-review-decision-record.md` — stakeholder worksheet with
  evidence links and unanswered policy/validation fields.
- `docs/project-status.md` — completed PR #30 CI evidence and next review link.
- `docs/superpowers/specs/2026-10-14-epic5-domain-review-record-design.md` —
  this approved design.
- `docs/superpowers/plans/2026-10-14-epic5-domain-review-record.md` —
  implementation steps derived from this spec.

## Testing Strategy

No code tests are needed. Review Markdown links and headings, check that all
decision fields are unanswered, confirm no cutoff is selected, verify the
project status still states that the export is held, and run `git diff --check`.

## Acceptance Criteria

- [ ] The worksheet links to the existing reproducible quality review and
  source-data assumptions without duplicating the full analysis.
- [ ] All five domain decision areas have fields for a decision, rationale,
  limitations, and follow-up action.
- [ ] No cutoff, assignment rule, label, or export approval is selected by
  default.
- [ ] The closeout state is explicitly unreviewed and export hold remains
  explicit in both the worksheet and status register.
- [ ] Project status records PR #30 CI completion and links the worksheet as the
  next review step.
- [ ] Markdown link/heading checks and `git diff --check` pass.

## Out Of Scope (backlog)

- Recruiting or contacting a domain stakeholder.
- Choosing a cutoff policy or approving a specific model feature or label.
- Refreshing source datasets or producing a revised export.
- Obtaining an OCI host or performing live deployment checks.

---

## Spec self-review

- No placeholders or unfinished sections remain.
- The worksheet does not claim a review took place or change the held disposition.
- Every goal maps to a concrete worksheet section and acceptance criterion.
- The change is documentation-only and fits one implementation plan.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-epic5-domain-review-record.md`
- Terminology: `docs/glossary.md`
