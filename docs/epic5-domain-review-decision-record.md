# Epic 5 Regional Risk Profile Domain Review

**Purpose:** Record seismic-domain review of the held regional risk-profile
export. This worksheet does not select policy or approve an export by itself.
The detailed quantitative evidence is in the [technical quality
review](risk-profile-quality-review-2026-10-14.md); project progress is tracked
in the [project status register](project-status.md).

## Review record

- Reviewer name and role: ______________________________
- Organization or discipline: _________________________
- Review date: ________________________________________
- Other participants: __________________________________
- Review state (select one at closeout):
  - [ ] `not_reviewed`
  - [ ] `review_incomplete`
  - [ ] `review_complete_hold_remains`
- Evidence versions and hashes reviewed: _______________

Review the [source-data assumptions](data-sources.md#kaggle-historical-earthquake-datasets)
and the local validation outputs described in the quality review. The held
bundle and local source files are not committed to the repository; identify the
exact versions and hashes actually reviewed above.

## Evidence to consider

- The export contains 17 regional profiles. The two source catalogs have
  different coverage periods and reporting thresholds; counts are not
  comparable regional rates.
- The implemented assignment rule maps events to the nearest region only when
  they are within 100 km of its boundary. Some source records remain
  unassigned; see the quality review for the source-level totals.
- The shared observation window is 2015-12-31 16:40 UTC through
  2026-10-02 23:10 UTC. In that window, NCR has three assigned events.
- The validation report evaluates 18 exploratory count cutoffs. At threshold
  4, NCR is excluded and 10 of 16 included labels change. The thresholds are
  observed breakpoints, not recommended minimum counts.
- Existing labels are descriptive statistical profiles. The review documents
  that classifier accuracy is in-sample and that `event_density` is a
  coordinate-spread proxy rather than an area-normalized rate.

These points summarize questions for review, not findings that establish a
policy. See the linked quality review for full methods, limitations, and
scenario results.

## 1. Offshore event assignment

Review the nearest-region assignment within the 100 km boundary distance,
including whether distance-to-boundary is suitable for the intended regional
summary and how unassigned offshore events should be handled.

- Decision: ___________________________________________
- Rationale and evidence: ______________________________
- Limitations or conditions: ___________________________
- Follow-up owner and action: __________________________

## 2. Sparse-region inclusion and count sensitivity

Review how regions with low shared-window counts should be represented. The
report includes the full set of observed breakpoints; none is preferred here.
Record whether a minimum-count policy is justified, whether another approach
should be evaluated, or whether no threshold should be used.

- Decision: ___________________________________________
- Rationale and evidence: ______________________________
- Limitations or conditions: ___________________________
- Follow-up owner and action: __________________________

If a cutoff is proposed, state its value, whether it applies to combined or
source-specific counts, its intended use, and the evidence required to validate
the regions retained under it: _________________________

## 3. Source coverage and observation window

Review the unequal catalog periods, reporting thresholds, catalog completeness,
and use of a common window. Decide what source refresh, provenance, and
coverage checks would be required before interpreting the profiles.

- Decision: ___________________________________________
- Rationale and evidence: ______________________________
- Limitations or conditions: ___________________________
- Follow-up owner and action: __________________________

## 4. Feature and category meaning

Review whether the current regional features and Low/Moderate/High categories
are meaningful for the intended use. Consider that the current categories are
statistical cluster descriptions, the Random Forest result is in-sample, and
the density feature is not an area-normalized rate.

- Decision: ___________________________________________
- Rationale and evidence: ______________________________
- Limitations or conditions: ___________________________
- Follow-up owner and action: __________________________

## 5. Evidence required to reconsider the export hold

Specify the validation design, review evidence, source provenance, and approval
needed before a new version could be considered for staging or user-facing
display. Completion of this worksheet alone does not lift the hold.

- Decision: ___________________________________________
- Rationale and evidence: ______________________________
- Limitations or conditions: ___________________________
- Follow-up owner and action: __________________________
- Required artifact version and source hashes: __________
- Separate approval record or authority: ________________

## Closeout

- Review summary: ______________________________________
- Unresolved questions: ________________________________
- Next review date or trigger: _________________________
- Reviewer confirmation: ______________________________

**Current project disposition:** the export remains on quality hold and must
not be transferred to staging. No sparse-region cutoff, reassignment policy,
label change, or export approval has been selected in this record. Any future
decision must be reflected in the [quality review](risk-profile-quality-review-2026-10-14.md)
and [project status register](project-status.md), with the reviewed artifact
version and source hashes recorded.
