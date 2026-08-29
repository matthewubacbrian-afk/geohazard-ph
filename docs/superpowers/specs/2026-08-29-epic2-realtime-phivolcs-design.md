# GeoHazard PH — Epic 2: Real-time + PHIVOLCS (Design)

**Date:** 2026-08-29

## Problem

Epic 1 wired the live USGS backbone: `USGS feed → ingestion → PostGIS hazard_events → GET /api/v1/events → map markers`. Epic 2 (real-time + PHIVOLCS local data) is still stubs:

- `backend/ingestion/sources/phivolcs_earthquake.py` returns `[]` — no real PHIVOLCS earthquake fetch/parse.
- `backend/ingestion/sources/phivolcs_volcano.py` and `gvp.py` are placeholders; `GET /api/v1/volcanoes` returns `[]`.
- `GET /api/v1/subscribe` returns `{"status": "realtime channel stub"}`.
- `web/src/hooks/useRealtimeAlerts.ts` returns `{connected: false}` — no WebSocket client, no live update.
- There is **no cross-source dedup**: a PHIVOLCS earthquake that also appears in USGS would be stored as two independent rows and the map would render **two markers for the same quake**, misrepresenting hazard counts. This is a P0 data-correctness gap for a disaster-risk platform.

This slice builds the real-time PHIVOLCS feed and push channel end-to-end, plus the canonicalization needed to stop double-counting the same earthquake across USGS and PHIVOLCS.

## Goals

Each is independently verifiable.

1. PHIVOLCS earthquake bulletins ingest into PostGIS as `hazard_type="earthquake"` and are served via `GET /api/v1/events`.
2. A USGS event and a PHIVOLCS event describing the same earthquake resolve to a single persisted `canonical_id`; **both source rows survive** with intact `source`/`external_id` attribution.
3. `GET /api/v1/events` defaults to primary-only (one row per canonical earthquake), with an opt-in raw-source view — so the map never shows duplicate markers by default.
4. Ingested/updated events broadcast over a WebSocket (`/ws/events`) so the dashboard updates without a manual refresh; broadcasts only ever carry already-resolved rows, including demoted rows.
5. `GET /api/v1/volcanoes` returns real PHIVOLCS volcano bulletin data (not `[]`).
6. Aftershock clusters are not incorrectly merged (fixture-tested; P0).

## Non-goals

- **Not** cursor pagination, authenticated/managed subscriptions, or WebSocket push to **mobile** (mobile stays on polling for now).
- **Not** the existing standards-gap remediation backlog (global error-envelope retrofit, ML fixture CWD-hardening, web-test unification, mobile API mapping, `WEB_STRUCTURE.md` refresh). New code must still conform to the target contracts where practical (`docs/error-handling-and-logging.md`).
- **Not** the ML training pipeline itself. This slice only records the magnitude source-of-truth decision so the pipeline consumes it deliberately (see Data considerations); it does not modify `ml/src/ml/`.
- **Not** staging deployment automation, Epic 3/4/5 artifacts, InSAR/landslide, GVP, or other sources.

## Context And Constraints

- Backend: FastAPI, SQLAlchemy 2, GeoAlchemy2, PostGIS, Redis. Redis is already in the stack (`app/core/redis.py`) and is the natural pub/sub for the push channel.
- Current dedup is per-source only: `app/services/dedup.py::dedup_key` returns `(source, external_id)` (or a content fallback scoped to a single source). It has no cross-source concept.
- `ingest_usgs_events(session, events)` in `app/services/ingest.py` commits internally and returns `int`; it is the single commit boundary for all ingestion.
- The `hazard_events` table has a `UniqueConstraint("source", "external_id")`; that constraint stays.
- Conventions: `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md` (snake_case wire, `response_model`), `docs/error-handling-and-logging.md`, `docs/glossary.md`.
- New concepts/functions added here must be added to `docs/glossary.md` per its workflow.

## Alternatives Considered

1. **Keep per-source rows, link only (no schema change).** Detect and flag matches but never persist an identity; consumers recompute the match per request. *Rejected:* recomputes a P0-correctness decision on every read, produces inconsistent results across consumers, and has no stable queryable grouping key.
2. **Collapse to a single merged row, delete the other source.** Simpler reads but destroys source attribution (violates the "preserve source identifiers" requirement) and makes provenance/audit impossible.
3. **Async canonicalization after the ingest transaction.** Lets the WS broadcast fire before matching resolves. *Rejected:* the dashboard could draw a marker that is immediately retroactively demoted, requiring a retraction protocol. Synchronous canonicalization avoids this entirely at this data volume.
4. **Chosen approach:** schema-backed canonical identity — both rows survive, grouped by a persisted `canonical_id` with a deterministic `is_primary`, computed synchronously once at ingest, read everywhere else. (Details below.)

## Design

### Architecture and data flow

```
USGS / PHIVOLCS earthquake adapters
   ▼
ingest_events(session, events, on_committed=None)
   1. upsert by (source, external_id)
   2. match_and_link(session)        // sync, SAME txn: assign canonical_id / is_primary / match_confidence
   3. commit()
   4. on_committed(EventChange[])    // Person B hook → Redis → /ws/events  (only after commit)
   ▼
PostgreSQL + PostGIS: hazard_events  (canonical columns + composite index)
   ▼
api: GET /events (primary-only default) / GET /events/summary (group by canonical_id) / GET /ws/events
   ▼
web: useRealtimeAlerts WebSocket client → React Query setQueryData append (live map/list)
```

### Components

- `ingestion/sources/phivolcs_earthquake.py` — real adapter (`fetch_recent_events`), typed like the USGS adapter.
- `ingestion/sources/phivolcs_volcano.py` — real volcano adapter feeding `/volcanoes`.
- `app/services/ingest.py` — generalize `ingest_usgs_events` → `ingest_events(session, events, on_committed=None)`; runs upsert + sync `match_and_link` before commit; invokes `on_committed` **after** commit. Person A owns this module.
- `app/services/dedup.py` — add cross-source matching (per-source key stays; new proximity matcher).
- `app/services/events_publisher.py` — Person B owns the Redis publish callback consumed as `on_committed` (never edited by Person A).
- `app/api/v1/events.py` + `app/services/events.py` — `source` filter, primary-only default, `include_duplicates` opt-in, `is_primary`/`canonical_id` grouping on list and summary.
- `app/api/v1/realtime.py` — `GET /ws/events` WebSocket subscribing to the Redis channel.
- `app/api/v1/subscribe.py` — replace stub with real channel status.
- `app/api/v1/volcanoes.py` — real list from the PHIVOLCS volcano adapter.
- `web/src/hooks/useRealtimeAlerts.ts` — real WebSocket client.
- `web/src/components/events/EventFilterBar.tsx` + related — source filter/badge.
- `web/src/components/dashboard/*` — live append + LIVE indicator.

### Interfaces

- `ingest_events(session, events, on_committed: Callable[[list[EventChange]], None] | None = None) -> int`
  - Person A implements; **only invokes** `on_committed` strictly after `session.commit()`.
  - Receives **all rows touched in the transaction** — the newly-ingested/matched rows *and* any row whose `is_primary` was flipped to `false` (e.g. a USGS row demoted when a matching PHIVOLCS row arrives). A match therefore yields two `EventChange` entries: the new primary and the demoted one.
- `EventChange` (dataclass / Pydantic, snake_case): `id`, `hazard_type`, `source`, `external_id`, `canonical_id`, `is_primary`, `latitude`, `longitude`, `magnitude`, `depth_km`, `occurred_at`, `place_name`.
- `events_publisher.publish(events: list[EventChange]) -> None` — publishes to Redis channel `events:updates`; never raises into the ingest path (failures logged, ingest unaffected).
- `GET /ws/events` — FastAPI WebSocket; receives `EventChange` broadcasts from the Redis channel.
- `GET /api/v1/events` — query params `since`, `source`, `include_duplicates: bool = false`.
  - Default: only rows where `is_primary = true` (map never shows duplicate markers).
  - `include_duplicates=true`: all source rows (attribution/debugging).
- `GET /api/v1/events/summary` — `west/south/east/north`, `region_name`, `source`, plus grouping **by `canonical_id`** and counting primaries.
- Migration `0002_add_hazard_event_canonical.py`: `canonical_id` (nullable UUID), `is_primary` (bool, **backfilled `true`**), `match_confidence` (float or null), **composite index `(canonical_id, is_primary)`**. Additive; existing rows are unchanged except `is_primary=true` and `canonical_id = id`.

### Configuration

- No new required secrets. PHIVOLCS earthquake/volcano bulletins are public. Add an ingest cadence setting if the scheduler needs it; reuse `app/config.py` conventions.

### Error handling

Per `docs/error-handling-and-logging.md`:
- Typed adapter exceptions (`PhivolcsFetchError`) distinguishing network vs parse vs credential.
- Scheduler uses `logging` (never `print()`); one logger per module.
- WS publish failures are logged, not fatal to ingest (the DB state is authoritative).
- New endpoints declare `response_model`; expected failures map to the error envelope.

### Data considerations

- **Canonicalization is synchronous, inside the ingest transaction, before commit and before broadcast.** The WS only ever pushes fully-resolved rows — no retraction protocol needed.
- **Matching algorithm** (`match_and_link`): proximity heuristic, computed once and persisted:
  - Time window: `±120s` (USGS/PHIVOLCS reporting lag).
  - Space: haversine distance tolerance (`distance_tolerance_km`, configurable, default ~a few km).
  - Magnitude delta tolerance (`magnitude_delta_tolerance`).
  - Only match within tolerance on **all three** dimensions.
- **Aftershock rule (P0):** tolerances must be tight enough that clustered aftershocks (genuinely distinct events near in time/space/magnitude) do **not** collapse into one canonical event.
- **`is_primary` tie-break (deterministic, order-independent):**
  1. PHIVOLCS row wins over USGS/GVP when a match resolves, regardless of arrival order.
  2. Fallback (no PHIVOLCS in the match): earliest `occurred_at`, then earliest `created_at`.
  - This is stable under re-ingestion in either order.
- **`is_primary` governs display authority, not per-field scientific authority.** Consumers that need a specific field's most authoritative value (e.g. magnitude) select by source preference independently of `is_primary`.
- **ML magnitude source-of-truth is a SEPARATE decision, not inherited from `is_primary`:** the risk-profiling pipeline (`ml/src/ml/clean_merge.py` and friends) trains on merged historical magnitude data and must use one consistent scale (USGS moment magnitude `Mww`) to avoid learning spurious regional clusters from a source-switching artifact. This slice records that decision (in ADR 0002) and the glossary; it does not change the ML code. When Epic 5 is wired to live data, the pipeline must select magnitude by source preference (USGS) independent of the display-primary flag.

## Rollout

1. **Shared-contract ADR (0002)** — lock the three decisions before parallel work: (a) `EventChange` WS shape, (b) `on_committed` hook ownership boundaries, (c) sync canonicalization + `is_primary` tie-break + ML magnitude provenance.
2. Person A: PHIVOLCS earthquake adapter → generalized `ingest_events` → migration → `match_and_link` + fixtures → endpoint filters.
3. Person B: `events_publisher` (consumes the hook) → `/ws/events` → `/subscribe` → volcano adapter + `/volcanoes` → web client + live append.
4. Web integration and docs sweep last.

Both people build on the shared `HazardEvent`/`/events` contract and the sealed ADR interfaces, which removes the only real file conflict (the ingest commit boundary).

## Files

### Backend
- Modify `backend/app/services/ingest.py` — generalize to `ingest_events(session, events, on_committed=None)`; sync `match_and_link` before commit; invoke hook after commit.
- Modify `backend/app/services/dedup.py` — cross-source matching helpers.
- Create `backend/app/services/events_publisher.py` — Redis publish callback (`publish`).
- Modify `backend/app/services/events.py` — primary-only default, `source` filter, `include_duplicates`, canonical grouping in list/summary.
- Modify `backend/app/api/v1/events.py` — new query params + summary filters.
- Create `backend/app/api/v1/realtime.py` — `GET /ws/events`.
- Modify `backend/app/api/v1/subscribe.py` — real channel status.
- Modify `backend/app/api/v1/volcanoes.py` — real PHIVOLCS data.
- Modify `backend/app/models/hazard_event.py` — `canonical_id`, `is_primary`, `match_confidence` columns.
- Create `backend/db/migrations/versions/0002_add_hazard_event_canonical.py` — canonical columns + backfill + composite index.
- Modify `backend/ingestion/sources/phivolcs_earthquake.py` — real fetch/parse.
- Create `backend/ingestion/sources/phivolcs_volcano.py` — real fetch/parse.
- Modify `backend/ingestion/scheduler.py` — run PHIVOLCS ingest, replace `print()` with `logging`.
- Modify `backend/app/main.py` — include `realtime` router.

### Backend tests
- Unit: `tests/unit/test_phivolcs_earthquake_parser.py`, `tests/unit/test_phivolcs_volcano_parser.py`, `tests/unit/test_canonicalize.py` (matching + tie-break + tolerance edges).
- Integration: `tests/integration/test_events_source_filter.py`, `tests/integration/test_canonical_dedup.py`, `tests/integration/test_realtime_ws.py`, `tests/integration/test_volcanoes.py`.

### Web
- Modify `web/src/hooks/useRealtimeAlerts.ts` — real WebSocket client.
- Modify `web/src/components/events/EventFilterBar.tsx` — source filter/badge.
- Modify `web/src/components/dashboard/DashboardMapArea.tsx`, `web/src/components/events/EventList.tsx` — live append (primary-only), LIVE indicator.
- Tests: `web/tests/useRealtimeAlerts.test.ts`, `web/tests/EventFilterBar.test.ts`, `web/tests/EventListLive.test.ts`.

### Docs
- Create `docs/adr/0002-epic2-realtime-phivolcs-contracts.md`.
- Modify `docs/glossary.md` (canonical_id, is_primary, match_confidence, EventChange, events_publisher, match_and_link), `docs/api-contracts.md` (new endpoints/params + Known Deviations updates), `docs/runbook.md`, and the `geohazard-*-.md` docs as needed.

## Testing Strategy

Per `docs/testing-standards.md`.

- **Backend unit (DB-free):**
  - PHIVOLCS earthquake/volcano parser tests against saved real response fixtures.
  - `test_canonicalize.py` — canonicalization logic (matching, tie-break, tolerance edges) against in-memory fixture pairs, no DB.
- **Backend integration (Dockerized PostGIS):**
  - `test_canonical_dedup.py` — persists fixture rows, asserts `canonical_id` grouping and `is_primary` under all four fixtures below, plus `GET /events` primary-only default vs `include_duplicates=true`.
  - `test_events_source_filter.py` — `source` filter and summary canonical grouping.
  - `test_realtime_ws.py` — connect a WS client, run an ingest, assert the expected `EventChange` broadcast (including the demoted-row entry).
  - `test_volcanoes.py` — real `/volcanoes` data.
  - Uses `app.dependency_overrides[get_db_session]` as in Epic 1.
- **Web:** Vitest + @testing-library (target style per `docs/testing-standards.md`) for the WS client state machine, source filter, and live append.

### Canonicalization fixtures (all four explicit, not incidental)

1. **True positive** — USGS and PHIVOLCS report the same earthquake within tolerance → one shared `canonical_id`, exactly one `is_primary=true`.
2. **Aftershock sequence non-merge (P0)** — a near-duplicate *sequence* (several events close in time/space/magnitude) stays as distinct canonical events; a wrong hazard count is the shipped-visible failure mode here.
3. **Late-arrival / tie-break reorder** — PHIVOLCS row arrives *second*; `is_primary` still lands on the PHIVOLCS row (per the tie-break rule), and the previously-primary USGS row flips to `false` and is included in the same broadcast.
4. **True-negative tolerance edges** — two events same time/place but magnitude delta just *over* tolerance; and two events same time/magnitude but distance just *over* tolerance — testing the edge of **each** tolerance dimension independently, not merely an obviously-unrelated pair.

## Acceptance Criteria

- [ ] `pytest -v` passes from `backend/` (unit + integration).
- [ ] `npm test` and `npm run build` pass from `web/`.
- [ ] `python scripts\verify_structure.py` passes.
- [ ] `git diff --check` clean.
- [ ] A PHIVOLCS earthquake ingested after a matching USGS row yields one shared `canonical_id`, PHIVOLCS `is_primary=true`, USGS row demoted — verified by `test_canonical_dedup.py` fixture 3, not just visually.
- [ ] `GET /events` returns one row per quake by default (fixture 1 + integration test); `include_duplicates=true` returns both rows.
- [ ] Ingesting a new PHIVOLCS/USGS event broadcasts an `EventChange` (including any demoted row) to a connected `/ws/events` client with no manual refresh.
- [ ] `/volcanoes` returns real PHIVOLCS bulletin data.
- [ ] `docs/adr/0002`, `docs/glossary.md`, `docs/api-contracts.md`, `docs/runbook.md` updated and consistent.

## Out Of Scope (backlog)

- Cursor pagination, subscription/auth model, WebSocket push to mobile.
- Standards-gap remediation backlog (tracked in `docs/superpowers/plans/2026-08-29-standards-gap-remediation.md`).
- Changing the ML training code to consume live canonical data (Epic 5 wiring) — the source-of-truth decision is recorded here for that future work.
- GVP, landslide/InSAR, static fault/volcano atlas layers, staging deployment.

---

## Spec self-review

- No `TBD`/`TODO` sections.
- Goals 1–6 each map to at least one acceptance criterion and a test.
- The `/events` primary-only default is explicit (goal 3, `Interfaces`, integration test, fixture 1) — the map-never-shows-duplicates invariant is load-bearing.
- The `on_committed` hook responsibility boundary (Person A invokes, Person B implements) is exact in `Interfaces`.
- Sync canonicalization + broadcast ordering resolves the timing ambiguity in `Data considerations`.
- `is_primary` tie-break and ML magnitude provenance are explicit, not implicit.
- Scope fits a single implementation plan (two parallel task tracks).

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-08-29-epic2-realtime-phivolcs.md` (see plan template).
- Decision record: `docs/adr/0002-epic2-realtime-phivolcs-contracts.md`.
- Terminology: `docs/glossary.md`.
