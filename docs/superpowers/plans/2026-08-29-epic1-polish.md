# Epic 1 Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close gaps in the working Epic 1 live-earthquake slice (deployment deliberately deferred): add a region summary endpoint, wire the dashboard card + loading/error states to real data, harden dedup, and update docs/CI.

**Architecture:** Backend-first — add an `EventSummary` service + `GET /api/v1/events/summary` endpoint backed by the existing PostGIS `hazard_events` table and `Settings.ph_bbox`; then a web hook + type + fetcher and wire `DashboardMapArea`'s floating card (avg magnitude, event frequency real; risk label + dominant fault system show honest "Not available" states), plus loading/error UI in `Dashboard`/`DashboardMapArea`. Then harden `dedup_key` with a content-based fallback. Finally docs + CI.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, PostGIS (Docker); web: React 18, TypeScript, Vite, TanStack Query, Vitest.

## Global Constraints

- Follow `CODING_STANDARDS.md` and `AGENTS.md`.
- Conventional Commits, imperative, lowercase after type (e.g. `feat: add events summary endpoint`).
- Python line length 100; type hints on public functions.
- Backend imports resolve from `backend/`; `pytest` runs from `backend/`.
- Do not commit credentials, generated artifacts, or large datasets.
- Treat geohazard data-correctness bugs as P0.
- Route ordering: `/events/summary` must be declared in the events router **before** any `/events/{...}` route to avoid conflicts.
- Integration tests use the existing PostGIS `client`/`migrated_engine` fixtures from `backend/tests/integration/conftest.py`.
- Verification: `pytest -v` (backend), `npm test` + `npm run build` (web), `python scripts\verify_structure.py`, `git diff --check`.

---

### Task 1: Backend — EventSummary schema, service, and `/events/summary` endpoint

**Files:**
- Modify: `backend/app/schemas/hazard_event.py` (add `EventSummary`)
- Modify: `backend/app/services/events.py` (add `summarize_events`)
- Modify: `backend/app/api/v1/events.py` (add `GET /summary`)
- Test: `backend/tests/unit/test_events_service.py` (extend)
- Test: `backend/tests/integration/test_events_api.py` (extend)

**Interfaces:**
- `EventSummary` Pydantic model: `region_name: str | None`, `event_count: int`, `avg_magnitude: float | None`, `max_magnitude: float | None`, `latest_occurred_at: datetime | None`.
- `app.services.events.summarize_events(session, west, south, east, north, region_name=None) -> EventSummary` — queries `hazard_events` within the bbox (on `latitude`/`longitude`), returns count, avg/max magnitude, latest `occurred_at`.
- `GET /api/v1/events/summary?west=&south=&east=&north=&region_name=` — defaults bbox to `Settings.ph_bbox`.

- [ ] **Step 1: Write failing unit test**
- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement service + schema**
- [ ] **Step 4: Write failing integration test**
- [ ] **Step 5: Implement endpoint + wire route (declared before any `/{...}` route)**
- [ ] **Step 6: Run tests, verify pass**
- [ ] **Step 7: Commit** `feat: add events summary endpoint`

---

### Task 2: Frontend — summary hook, type, fetcher, and card wiring

**Files:**
- Modify: `web/src/types/hazard.ts` (add `EventSummary`)
- Modify: `web/src/api/client.ts` (add `fetchEventSummary`)
- Create: `web/src/hooks/useEventSummary.ts`
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx` (wire floating card)
- Test: `web/tests/DashboardCard.test.tsx` (create)

**Interfaces:**
- `EventSummary` TS type mirroring the backend model.
- `fetchEventSummary(params?: {west?;south?;east?;north?;region_name?}) -> Promise<EventSummary>`.
- `useEventSummary()` TanStack Query hook.
- The floating card shows avg magnitude + event frequency from real summary data; risk label and dominant fault system render an honest "Not available" state.

- [ ] **Step 1: Write failing component test**
- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement type, fetcher, hook**
- [ ] **Step 4: Implement card wiring**
- [ ] **Step 5: Run test + build, verify pass**
- [ ] **Step 6: Commit** `feat: wire dashboard card to events summary`

---

### Task 3: Frontend — loading and error states

**Files:**
- Modify: `web/src/pages/Dashboard.tsx` (surface `isLoading`/`error`)
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx` (loading indicator + retry-able error banner)
- Test: `web/tests/Dashboard.test.tsx` (create)

**Interfaces:**
- `Dashboard` passes loading/error through to the map area.
- `DashboardMapArea` shows a loading state while fetching and a retry-able error banner on fetch failure (matching existing JSX/style).

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement loading/error UI**
- [ ] **Step 4: Run test + build, verify pass**
- [ ] **Step 5: Commit** `feat: add loading and error states to dashboard`

---

### Task 4: Backend — dedup hardening

**Files:**
- Modify: `backend/app/services/dedup.py` (fallback content key)
- Test: `backend/tests/unit/test_dedup.py` (extend)

**Interfaces:**
- Keep `dedup_key(event) -> tuple[str, str | None]` for events with `external_id`.
- For events where `external_id` is `None`, return a content-based key derived from `occurred_at` + lat + lon + magnitude (stable hash/string).
- Unit test covers the no-`external_id` path.

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test, verify it fails**
- [ ] **Step 3: Implement fallback key**
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit** `fix: dedup events without an external id`

---

### Task 5: Docs + CI

**Files:**
- Modify: `README.md`
- Modify: `docs/runbook.md`
- Modify: `docs/geohazard-system-architecture.md` (or `docs/data-sources.md`) — document the new `/events/summary` endpoint
- Modify: `.github/workflows/web-ci.yml` (add `npm test`)

- [ ] **Step 1: Update README**
- [ ] **Step 2: Update runbook**
- [ ] **Step 3: Update architecture/data-source doc with the summary endpoint**
- [ ] **Step 4: Add `npm test` to web CI**
- [ ] **Step 5: Run structure verification + `git diff --check`**
- [ ] **Step 6: Commit** `ci: run web tests in ci` and `docs: document events summary endpoint`

---

## Notes for the executor
- Tasks 1–4 are independent in their own layers; Task 5 depends on all (documents their behavior).
- Backend integration tests require a running PostGIS test DB (`docker compose up postgres`, `geohazard_test` database). Unit tests are DB-free.
- `Dashboard.test.tsx` and `DashboardCard.test.tsx` must mock `useEvents`/`useEventSummary` (TanStack Query) and use `jsdom` env (already configured in `web/vite.config.ts`).
