# GeoHazard PH — Epic 2: Real-time + PHIVOLCS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the real-time PHIVOLCS feed and push channel, and canonicalize USGS↔PHIVOLCS earthquake identity so the map shows one marker per quake with live updates.

**Architecture:** Two parallel vertical tracks (Person A, Person B) that build on a single sealed shared contract (ADR 0002) and the shared `HazardEvent`/`/events`/ingest-commit boundary. Task 0 seals the shared contract before either track starts. Person A owns the ingest-commit seam (`ingest_events`), Person B owns the publish callback (`events_publisher`) consumed through that seam — neither edits the other's body, eliminating the only real file-conflict surface.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, GeoAlchemy2, PostGIS, Alembic, Redis pub/sub, pytest; React 18, TypeScript, TanStack Query, WebSocket, Vitest + @testing-library.

**Spec:** `docs/superpowers/specs/2026-08-29-epic2-realtime-phivolcs-design.md`

**Reading order for the two executors:**
1. `docs/adr/0002-epic2-realtime-phivolcs-contracts.md` — **both people** read this first; it seals the shared `EventChange` / hook-ownership / timing contracts that both tracks depend on.
2. This plan — **Person A** executes tasks A1–A6, **Person B** executes tasks B1–B6 (in parallel, after Task 0).
3. The spec (`docs/superpowers/specs/2026-08-29-epic2-realtime-phivolcs-design.md`) is background context, not required reading for execution.

## Global Constraints

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, `docs/glossary.md`.
- Conventional Commits; imperative, lowercase after type (`feat:`, `test:`, `docs:`, `refactor:`).
- Python line length 100; type hints on public functions; imports resolve from `backend/`; `pytest` runs from `backend/`.
- Do not commit credentials, generated artifacts, or large datasets.
- Route ordering: static segments before `/{param}` routes.
- All new concepts/fields/functions added to `docs/glossary.md`.
- Verification: package tests, `npm run build`, `python scripts\verify_structure.py`, `git diff --check`.
- Integration tests require Dockerized PostGIS + Redis (see `backend/tests/integration/conftest.py`); unit/canonicalization tests must be DB-free.
- Read-only source-data endpoints preferred; publish/readership rules stay read-only.

---

### Task 0 (shared): Seal the shared contract — ADR 0002

Locks the three decisions both tracks depend on, so parallel work has no guessing.

**Files:**
- Create: `docs/adr/0002-epic2-realtime-phivolcs-contracts.md`

**Interfaces:**
- Consumes: nothing (documents decisions).
- Produces: the authoritative contract for `EventChange`, the `on_committed` hook boundary, sync canonicalization, `is_primary` tie-break, and ML magnitude source-of-truth.
- The ADR body records, in Status/Context/Decision/Consequences form (match `docs/adr/0001` style):

  1. **`EventChange` shape** (snake_case): `id`, `hazard_type`, `source`, `external_id`, `canonical_id`, `is_primary`, `latitude`, `longitude`, `magnitude`, `depth_km`, `occurred_at`, `place_name`.
  2. **Ingest-commit hook ownership:** Person A owns `ingest_events(session, events, on_committed=None)` and **invokes** `on_committed(list[EventChange])` strictly after `session.commit()`. Person B owns `services/events_publisher.py::publish(events)` and never edits `ingest.py`. The hook receives **all rows touched in the transaction** — including rows demoted to `is_primary=false` in the same commit (e.g. a USGS row demoted when a matching PHIVOLCS row arrives), so the frontend retracts/updates the previously-drawn marker.
  3. **Sync canonicalization + tie-break + ML magnitude provenance:** `match_and_link` runs synchronously inside the ingest transaction, before commit, before broadcast (WS only ever carries resolved rows; no retraction protocol). `is_primary` tie-break: PHIVOLCS wins, else earliest `occurred_at`, else earliest `created_at` (order-independent). `is_primary` governs **display** authority only; the ML pipeline selects magnitude by **source preference (USGS)** independent of `is_primary` — a separate, explicit decision recorded here (not modifying ML code this slice).

- [ ] **Step 1:** Write the ADR following `docs/adr/0001` format.
- [ ] **Step 2:** Update `docs/glossary.md` with the new terms (`canonical_id`, `is_primary`, `match_confidence`, `EventChange`, `match_and_link`).
- [ ] **Step 3:** Commit `docs: record epic2 realtime/phivolcs shared contracts`

```bash
git add docs/adr/0002-epic2-realtime-phivolcs-contracts.md docs/glossary.md
git commit -m "docs: record epic2 realtime/phivolcs shared contracts"
```

---

## Person A track — PHIVOLCS earthquake feed + cross-source canonicalization

### Task A1: PHIVOLCS earthquake adapter

**Files:**
- Modify: `backend/ingestion/sources/phivolcs_earthquake.py`
- Test: `backend/tests/unit/test_phivolcs_earthquake_parser.py` (create)

**Interfaces:**
- Consumes: `app.schemas.hazard_event.HazardEvent`, `app.config.get_settings`, a saved real PHIVOLCS bulletin fixture.
- Produces:
  - `fetch_recent_events(settings) -> list[HazardEvent]` (mirrors `ingestion/sources/usgs.py`).
  - Adapter maps bulletin fields onto `HazardEvent` with `hazard_type="earthquake"`, `source="phivolcs"`, preserving `external_id` where available; `magnitude`/`depth_km` nullable.

- [ ] **Step 1: Write the failing parser unit test** against a saved real PHIVOLCS bulletin fixture (assert `HazardEvent` field mapping, `source="phivolcs"`).
- [ ] **Step 2: Run, verify it fails** (function absent/stub).
- [ ] **Step 3: Implement** `fetch_recent_events` + parsing; define `PhivolcsFetchError` for network vs parse failures.
- [ ] **Step 4: Run, verify passes.**
- [ ] **Step 5: Commit** `feat: add phivolcs earthquake adapter`

---

### Task A2: Generalize `ingest_events` with `on_committed` seam

Person A owns this module AND the seam; Person A does **not** implement the publish callback (Person B does).

**Files:**
- Modify: `backend/app/services/ingest.py`
- Test: `backend/tests/unit/test_ingest_events.py` (create, DB-free where possible)

**Interfaces:**
- Consumes: existing `dedup_key`, `HazardEvent` schema.
- Produces:
  - `ingest_events(session, events, on_committed: Callable[[list[EventChange]], None] | None = None) -> int`
  - Generalizes `ingest_usgs_events` to accept any source. Runs upsert → `match_and_link(session)` (Task A4) → `commit()` → `on_committed(changes)` where `changes` is the complete list of `EventChange` for rows touched in this commit (created OR `is_primary`-flipped). If `on_committed` is `None`, skip the call.
  - `_to_event_change(row) -> EventChange` helper (or equivalent).
- The existing `ingest_usgs_events` shim may be kept as a thin wrapper delegating to `ingest_events` with USGS-specific behavior removed, or call sites updated to `ingest_events` directly — keep `scheduler.py` updated to the new signature.

- [ ] **Step 1: Write failing tests** for `ingest_events` upsert + the `on_committed` invocation (assert it is called **after** commit with the right `EventChange` list). Add a `EventChange` schema to `app/schemas/` (backed by glossary).
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** generalization + hook seam.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** `refactor: generalize ingest with post-commit hook`

---

### Task A3: Migration — canonical columns

**Files:**
- Modify: `backend/app/models/hazard_event.py`
- Create: `backend/db/migrations/versions/0002_add_hazard_event_canonical.py`

**Interfaces:**
- Consumes: current `hazard_events` schema (unique `(source, external_id)` stays).
- Produces three additive columns on `hazard_events`:
  - `canonical_id` — nullable `UUID`; grouped identity.
  - `is_primary` — `Boolean`, **backfilled `true`** for existing rows.
  - `match_confidence` — nullable `Float`.
  - Composite index `idx_hazard_events_canonical` on `(canonical_id, is_primary)` — every consumer filters on it, non-optional load-performance.
- Migration sets `canonical_id = id` for existing rows (each existing row is its own sole representation), `is_primary = true`.
- Model reflects the new columns; `raw_payload` untouched.

- [ ] **Step 1:** Write the Alembic migration (add columns + backfill + composite index). Confirm `alembic upgrade head` against PostGIS works.
- [ ] **Step 2:** Add model columns; run a quick migration check.
- [ ] **Step 3:** Commit `feat: add canonical identity columns to hazard_events`

---

### Task A4: Cross-source `match_and_link` + canonicalization fixtures

**Files:**
- Modify: `backend/app/services/dedup.py`, `backend/app/services/ingest.py`
- Test: `backend/tests/unit/test_canonicalize.py` (create, DB-free)

**Interfaces:**
- Consumes: `dedup_key`, `HazardEvent` schema, new canonical columns.
- Produces:
  - `match_and_link(session) -> None` — synchronous, **within the ingest transaction before commit**. For each unmatched/late-arriving row, find cross-source matches within tolerance; assign `canonical_id`, `is_primary`, `match_confidence`. Leaves rows already grouped untouched.
  - Matching tolerances (constants or settings): time window `±120s`; `distance_tolerance_km` (default ~5 km, haversine); `magnitude_delta_tolerance` (default ~0.5). Match only when **all three** are within tolerance.
  - `is_primary` tie-break helper: PHIVOLCS wins; else earliest `occurred_at`; else earliest `created_at`. Deterministic and order-independent (same result whether PHIVOLCS is ingests first or second).
- Must be implemented with the four explicit fixtures below — DB-free against in-memory rows where the matching logic is pure, or via a minimal unit harness.

- [ ] **Step 1: Write the four failing fixture tests** in `test_canonicalize.py`:
  1. **True positive** — same quake from both sources → one `canonical_id`, exactly one `is_primary=true`.
  2. **Aftershock sequence non-merge (P0)** — near-duplicate *sequence* stays distinct (correct hazard count is the shipped-visible failure mode).
  3. **Late-arrival / tie-break reorder** — PHIVOLCS arrives second; `is_primary` still PHIVOLCS; previously-primary USGS row flips to `false`; both appear in the same commit's change list.
  4. **True-negative tolerance edges** — same time/place with magnitude delta just over tolerance; and same time/magnitude with distance just over tolerance (each tolerance dimension independently, not an obviously-unrelated pair).
- [ ] **Step 2: Run, verify all four fail** (no matcher).
- [ ] **Step 3: Implement** `match_and_link` + tie-break + tolerances.
- [ ] **Step 4: Run, verify all four pass.**
- [ ] **Step 5: Commit** `feat: add cross-source canonical event matching`

---

### Task A5: `/events` + `/events/summary` primary-only + source filter

**Files:**
- Modify: `backend/app/services/events.py`, `backend/app/api/v1/events.py`
- Test: `backend/tests/integration/test_events_source_filter.py`, `backend/tests/integration/test_canonical_dedup.py`

**Interfaces:**
- Consumes: canonical columns, `question`ed endpoints.
- Produces:
  - `list_events(session, since=None, source=None, include_duplicates=False)` — **default filters `is_primary = true`**; `source` filter; `include_duplicates=True` returns all rows.
  - `summarize_events(...)` — group/roll up **by `canonical_id`**; count primaries; add optional `source` filter.
  - `GET /api/v1/events` — query params `since`, `source`, `include_duplicates` (default `false`). Declare `response_model`.
  - `GET /api/v1/events/summary` — `source` param; canonical grouping.
- Integration test asserts: two matching rows → `/events` returns exactly one (primary) by default, both with `include_duplicates=true`; `source=phivolcs` returns only PHIVOLCS rows.

- [ ] **Step 1: Write the failing integration tests** (primary-only default, `include_duplicates`, `source` filter, summary canonical grouping) against PostGIS with seeded fixture rows.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** service + route changes.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Update** `docs/api-contracts.md` (new params, Known Deviations) and glossary if needed.
- [ ] **Step 6: Commit** `feat: primary-only events with source filter and duplicate opt-in`

---

### Task A6: Scheduler + logging (Person A closes the loop)

**Files:**
- Modify: `backend/ingestion/scheduler.py`

**Interfaces:**
- Adds `run_phivolcs_ingest()` alongside `run_usgs_ingest()`; both call `ingest_events(...)`.
- Replaces `print()` with `logging.getLogger(__name__).info(..., extra={...})` per `docs/error-handling-and-logging.md`.

- [ ] **Step 1:** Refactor scheduler to use `logging` and run PHIVOLCS ingest.
- [ ] **Step 2:** Run `pytest -v` from `backend/`, `python scripts\verify_structure.py`, `git diff --check`.
- [ ] **Step 3: Commit** `refactor: log phivolcs ingest in scheduler`

---

## Person B track — Realtime push channel + PHIVOLCS volcano feed

### Task B1: `events_publisher` (Redis publish callback)

Person B owns this module. Person B consumes the `on_committed` seam from Task A2 — **never edits `ingest.py`**.

**Files:**
- Create: `backend/app/services/events_publisher.py`
- Test: `backend/tests/unit/test_events_publisher.py` (create)

**Interfaces:**
- Consumes: `on_committed` contract (`list[EventChange]`), `app.core.redis`.
- Produces:
  - `publish(events: list[EventChange]) -> None` — publishes to Redis channel `events:updates` (JSON serialization). Never raises into the ingest path; logs on failure (DB state is authoritative).

- [ ] **Step 1: Write failing test** — `publish` writes the expected JSON to the expected Redis channel (monkeypatched Redis), and swallows/logs a Redis failure without raising.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `publish`.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** `feat: add redis events publisher`

---

### Task B2: `/ws/events` WebSocket endpoint

**Files:**
- Create: `backend/app/api/v1/realtime.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/integration/test_realtime_ws.py`

**Interfaces:**
- `GET /ws/events` under `/api/v1`. Subscribes to Redis channel `events:updates`; forwards each `EventChange` to the connected client. Handles disconnect cleanup. Registered via `app.include_router(realtime.router, prefix="/api/v1")`.
- Integration test: connect a WS client, run an ingest (via service directly), assert the expected `EventChange` broadcast — including the demoted-row entry in the late-arrival case.

- [ ] **Step 1: Write the failing integration test** (connect, ingest, assert broadcast + demoted row).
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** the WS endpoint + router registration.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** `feat: add realtime ws event broadcast`

---

### Task B3: `/subscribe` real status

**Files:**
- Modify: `backend/app/api/v1/subscribe.py`
- Test: `backend/tests/unit/test_subscribe.py` (create)

**Interfaces:**
- Replaces the stub with a real status response reporting the WS/Redis channel: e.g. `{"status": "ok", "channel": "events:updates", "endpoint": "/api/v1/ws/events"}`. Per `docs/error-handling-and-logging.md`, report readiness, never leak internals.

- [ ] **Step 1: Write failing test** for the new shape.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** `feat: report realtime channel status`

---

### Task B4: PHIVOLCS volcano feed → `/volcanoes`

**Files:**
- Create: `backend/ingestion/sources/phivolcs_volcano.py`
- Modify: `backend/app/api/v1/volcanoes.py`, `backend/app/schemas/volcano.py`
- Test: `backend/tests/unit/test_phivolcs_volcano_parser.py`, `backend/tests/integration/test_volcanoes.py`

**Interfaces:**
- Produces `fetch_volcano_bulletins(settings) -> list[Volcano]` from PHIVOLCS volcano bulletins. New/updated `Volcano` schema if the current `VolcanoModel` (`id`, `name`, `current_alert_level`) is insufficient; keep it additive.
- `/volcanoes` returns the real list (replaces hardcoded `[]`), `response_model=list[Volcano]`.
- `PhivolcsFetchError` taxonomy shared with A1.

- [ ] **Step 1: Write failing parser unit test** (fixture) + integration test for `/volcanoes`.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** adapter + endpoint + schema.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Update** `docs/api-contracts.md` and glossary if new types added.
- [ ] **Step 6: Commit** `feat: serve phivolcs volcano bulletins`

---

### Task B5: Web `useRealtimeAlerts` WebSocket client

**Files:**
- Modify: `web/src/hooks/useRealtimeAlerts.ts`
- Test: `web/tests/useRealtimeAlerts.test.ts` (create)

**Interfaces:**
- `useRealtimeAlerts()` returns `{ connected, events }` (or a stable interface the live-append task consumes). Replaces the `{connected:false}` stub. Reconnect with backoff; exposes received `EventChange`-shaped events.
- Follow `docs/error-handling-and-logging.md` web rules: typed errors, explicit states, retry path.

- [ ] **Step 1: Write failing tests** for connect/disconnect/reconnect state transitions (Vitest + @testing-library, mocked WebSocket).
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** the client.
- [ ] **Step 4: Run `npm test` and `npm run build`, verify pass.**
- [ ] **Step 5: Commit** `feat: add realtime websocket client`

---

### Task B6: Web live map/list append + LIVE indicator

**Files:**
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx`, `web/src/components/events/EventList.tsx`, `web/src/components/dashboard/DashboardSidebar.tsx`, `web/src/components/events/EventFilterBar.tsx`
- Test: `web/tests/EventListLive.test.ts`, `web/tests/EventFilterBar.test.ts` (create)

**Interfaces:**
- Live-update path: on each received `EventChange`, append/update the corresponding primary event via React Query `setQueryData`/invalidation (primary-only — a received non-primary/demoted row updates/removes the previously-displayed marker rather than adding a duplicate).
- `EventFilterBar` gains a **source filter/badge** (USGS / PHIVOLCS), wired to `useEvents`' `source` param.
- A `LIVE` indicator + last-updated timestamp in `DashboardSidebar`.
- Consumes: `useEvents` (`source`, and primary-only defaults from A5), `useRealtimeAlerts` (B5).

- [ ] **Step 1: Write failing component tests** — live append of a new event, demotion of an existing marker, source filter, badge.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `npm test` and `npm run build`, verify pass.**
- [ ] **Step 5: Commit** `feat: live map updates and source filter`

---

## Notes for the executor

- Tasks A1–A6 and B1–B6 run in parallel after Task 0. The only cross-track dependency is the sealed seam from Task 0/A2: Person B's `publish` consumes `on_committed`, Person A invokes it — neither edits the other's module. Do not start B1 until A2 is merged (or agree on the `EventChange` signature at Task 0 and code to it), and do not start A5's Web source filter before B5/B6 in the Web, but backend endpoints are independent.
- Environment: Dockerized PostGIS + Redis for integration tests (`backend/tests/integration/conftest.py`); migration requires `alembic upgrade head`. Unit/canonicalization tests are DB-free.
- P0 correctness: the four canonicalization fixtures (Task A4) and the `/events` primary-only default (Task A5) are the load-bearing bars — a regression here ships wrong hazard counts.
- The ML magnitude source-of-truth decision is recorded in ADR 0002 only this slice; do not modify `ml/src/ml/`.
- Before closing each task, re-read the target "Known deviations"/glossary sections — partial fixes from other work may have changed them.
- Final sweep: run `pytest -v` (backend), `npm test` + `npm run build` (web), `python scripts\verify_structure.py`, `git diff --check`, and update `docs/runbook.md`, `docs/api-contracts.md`, and the `geohazard-*-.md` docs.
