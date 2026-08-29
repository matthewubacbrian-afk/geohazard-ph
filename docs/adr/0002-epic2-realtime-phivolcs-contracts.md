# ADR 0002: Epic 2 Real-time / PHIVOLCS Shared Contracts

## Status

Accepted

## Context

Epic 2 (real-time + PHIVOLCS feed) is built as two parallel vertical tracks by two people:

- **Person A** owns the PHIVOLCS earthquake feed and cross-source canonicalization (ingest, dedup, `/events` filters).
- **Person B** owns the realtime push channel (Redis → `/ws/events` → web live updates) and the PHIVOLCS volcano feed.

Both converge on the same internal boundaries, and the work can only land conflict-free and correctness-safe if three contracts are decided once, in advance:

1. The shape of the realtime update message (`EventChange`) — the wire contract between ingest and the WebSocket broadcast.
2. The ownership boundary at the ingest-commit seam — who invokes the publish hook and who implements it, so two people do not edit the same function body.
3. The timing of canonicalization relative to the broadcast, plus the `is_primary` tie-break rule and whether display-primary authority carries into the ML pipeline's per-field source-of-truth.

The broader design is in `docs/superpowers/specs/2026-08-29-epic2-realtime-phivolcs-design.md`.

## Decision

### 1. `EventChange` message shape

Every realtime update broadcast to clients is one `EventChange` (snake_case, JSON), mirroring the hazard-event wire fields plus canonical fields:

```json
{
  "id": "<uuid>",
  "hazard_type": "earthquake",
  "source": "phivolcs",
  "external_id": "<source id or null>",
  "canonical_id": "<uuid>",
  "is_primary": true,
  "latitude": 15.0,
  "longitude": 121.0,
  "magnitude": 5.2,
  "depth_km": 10.0,
  "occurred_at": "2026-08-29T09:30:00Z",
  "place_name": "12 km E of Sample, Philippines"
}
```

### 2. Ingest-commit hook ownership boundary

- **Person A** owns `ingest_events(session, events, on_committed=None)`. Person A only **invokes** `on_committed(list[EventChange])`, strictly **after** `session.commit()`.
- **Person B** owns `services/events_publisher.py::publish(events)`, consumed as the `on_committed` callback. Person B **never edits** `ingest.py`.
- The hook receives **all rows touched in the transaction** — newly-ingested rows **and** any row whose `is_primary` was flipped to `false` in the same commit (e.g. a USGS row demoted when a matching PHIVOLCS row arrives). A match therefore yields two `EventChange` entries (the new primary and the demoted one), so the frontend can update or retract a marker it already drew instead of leaving a phantom duplicate.

### 3. Synchronous canonicalization, tie-break, and ML magnitude source-of-truth

- **Canonicalization is synchronous and inside the ingest transaction.** `match_and_link(session)` runs before `commit()`, which runs before the broadcast hook. The WebSocket only ever carries fully-resolved rows (`canonical_id`, `is_primary` already assigned). No retraction/superseding protocol is needed for the sync path; if a future change makes canonicalization async, the `EventChange` shape must gain `event_updated`/`event_superseded` variants before that lands.
- **`is_primary` tie-break (deterministic, order-independent):**
  1. PHIVOLCS row wins over USGS/GVP when a match resolves, regardless of arrival order (PHIVOLCS is the local source with stronger PH depth/felt-intensity calibration and is the appropriate display authority).
  2. Fallback (no PHIVOLCS row in the match): earliest `occurred_at`, then earliest `created_at`.
- **`is_primary` governs display authority, not per-field scientific authority.** Consumers that need a specific field's most authoritative value select by source preference independently.
- **ML magnitude source-of-truth is a separate, explicit decision, not inherited from `is_primary`:** the risk-profiling pipeline (`ml/src/ml/clean_merge.py` and friends) trains on merged historical magnitude data and must use one consistent scale (USGS moment magnitude `Mww`) so it does not learn spurious regional clusters from a source-switching artifact. When Epic 5 is wired to live/canonical data, the pipeline must select magnitude by source preference (USGS) independent of the display-primary flag. This slice does **not** modify ML code; it records the decision now so it is not later assumed implicitly.

## Consequences

- Both source rows of a matched earthquake survive with intact `source`/`external_id` attribution; only `canonical_id`/`is_primary`/`match_confidence` are shared.
- `/events` defaults to primary-only (`include_duplicates=true` opts into all raw source rows), so the map shows one marker per quake.
- Aftershock clusters must not merge: matching tolerances (time `±120s`, haversine distance, magnitude delta) are set tight enough that genuinely distinct near-duplicate events stay distinct (P0, fixture-tested).
- Parallel work is safe: Person A and Person B touch disjoint modules at the seam (`ingest.py` vs `events_publisher.py`), with the `EventChange` contract sealed here.
- Future work that makes canonicalization async, adds subscription/auth, or pushes to mobile must revisit this ADR before changing the message shape or timing.
