# ADR 0003: Canonical Event Reconciliation

## Status

Accepted

## Context

The original cross-source matcher merged any pair of matching rows' existing groups.
That allowed a chain of partial matches to merge records whose endpoints did not match.
Persisted groups were never split when a source corrected an event's location or magnitude.

## Decision

- Recompute canonical groups from current source rows during each nonempty ingest.
- Every pair in a group must meet the time, distance, magnitude, and hazard-type tolerances.
- A group contains at most one row per source. If a row can join more than one group,
  choose the group with the strongest weakest-pair confidence; break ties by row ID.
- Keep the existing PHIVOLCS-first display-primary rule. Use the smallest row UUID as
  `canonical_id`, and recalculate `is_primary` and `match_confidence` for every row.
- Ingest publishes changes for all rows whose canonical identity or primary state changes.
- A maintenance command previews or applies reconciliation to persisted groups. Run it
  before enabling the worker when rolling this change into a populated environment.

## Consequences

Revisions can split and rejoin groups, and nearby same-source events cannot collapse
through a third-party report. Full-table matching remains quadratic in row count, as it
was before this change; partitioning by time and location is future scaling work.
Rows without a stable source `external_id` still use a content-based upsert key, so a
revised source record without that identifier may remain a separate row. Operators
must inspect those cases before treating a new row as a correction.
