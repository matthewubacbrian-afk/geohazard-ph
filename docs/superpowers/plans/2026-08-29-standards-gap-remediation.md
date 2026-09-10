# Standards Gap Remediation — Implementation Plan (Backlog)

> **Status (2026-09-10):** Implemented on `epic3` at the user's request. Backend (including integration), web,
> ML and mobile verification completed against the local Docker services.
> No commits created in this working-tree change. Historical steps below retain their
> original ordering; not all tests were demonstrated failing before implementation.
> Mapping stays in `services/api.ts` per the current glossary contract and takes the
> base URL from the application caller, avoiding bundler-specific environment assumptions.
>
> **Orthogonal to:** `2026-08-29-epic1-polish.md`. No task overlap — epic1-polish covers the events summary endpoint, dashboard card wiring, loading/error UI, and dedup hardening; this plan covers standards-compliance work only.

**Goal:** Bring current code up to the target contracts in `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/glossary.md`, one deviation at a time.

**Architecture:** Bottom-up by blast radius. Task 1 (error envelope + backend logging) touches the widest surface — every endpoint and every log call — so it goes first and everything later builds on the envelope it registers. Task 2 hardens ML test paths. Task 3 unifies web test style. Task 4 introduces the mobile API mapping contract that must exist before mobile wires real fetches (a breaking-contract event). Task 5 refreshes the stale in-package doc.

**Tech Stack:** Python 3.11, FastAPI, pytest, Vitest, Jest, React Test Library.

## Global Constraints

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, and the applicable stack docs (`BACKEND_STANDARDS.md`, `docs/testing-standards.md`, `docs/api-contracts.md`, `docs/error-handling-and-logging.md`).
- Conventional Commits; imperative, lowercase after type.
- Python line length 100; type hints on public functions.
- Backend imports resolve from `backend/`; `pytest` runs from `backend/`.
- Do not commit credentials, generated artifacts, or large datasets.
- Each task keeps the corresponding "Known deviations" section in sync: delete the fixed bullet when the task lands.
- Verification: package tests, `npm run build` (web), `python scripts\verify_structure.py`, `git diff --check`.

---

### Task 1: Backend error envelope + logging retrofit

**Why first:** Touches every endpoint (envelope registration in `main.py`) and every log call path; retrofits get more expensive the longer new code is written against the old pattern.

**Files:**
- Modify: `backend/app/main.py` — register `RequestValidationError` and `Exception` handlers; wire `configure_logging()` at startup.
- Modify: `backend/app/core/logging.py` — provide the startup logging configuration (keep a `configure_logging()` entrypoint).
- Modify: `backend/ingestion/scheduler.py` — replace `print()` summary with `logging`.
- Create: `backend/app/core/errors.py` — `to_error_response(...)` helper and envelope constants.
- Modify: `backend/app/api/v1/risk_profile.py` — already raises `HTTPException` for 404; ensure detail flows through the envelope.
- Test: `backend/tests/integration/test_error_envelope.py` (create) — validation error, 404, and unexpected 500 shapes.

**Deviation trace:** `BACKEND_STANDARDS.md` → Known Deviations 1–3; `docs/error-handling-and-logging.md` → Known Deviations 1–3.

**Interfaces:**
- `app.core.errors.to_error_response(status: int, code: str, message: str, request_id: str | None = None) -> JSONResponse` returning the envelope: `{"error": {"code", "message", "status", "request_id"}}`.
- Global handlers map `RequestValidationError` → `code: "validation_error"`, `HTTPException` → its `detail`, and `Exception` → `code: "internal_error"` with `logger.exception(...)` and a safe message.
- `scheduler.main()` logs `logger.info("USGS ingest complete", extra={"fetched": ..., "processed": ...})`.

- [ ] Step 1: Write failing envelope tests (assert exact JSON shape for 422, 404, 500).
- [ ] Step 2: Run, verify fail (handlers absent).
- [ ] Step 3: Implement handlers + `errors.py` + startup logging.
- [ ] Step 4: Replace scheduler `print()`.
- [ ] Step 5: Run tests, verify pass.
- [ ] Step 6: Delete the fixed bullets from both Known Deviations sections.
- [ ] Step 7: Commit `feat: add api error envelope and startup logging`

---

### Task 2: ML test fixture hardening

**Files:**
- Create: `ml/tests/conftest.py` — provide fixtures located via `Path(__file__)` instead of CWD.
- Modify: `ml/tests/test_*.py` — replace `Path("tests/fixtures/...")` with conftest-provided fixture paths or `Path(__file__).resolve()`-derived absolute paths.
- Test: existing files, now passing from `ml/` and from the repo root.

**Deviation trace:** `docs/testing-standards.md` → Known Deviations 1–2.

**Interfaces:**
- `conftest.py` exposes fixture constants/paths, e.g. `PHIVOLCS_SAMPLE`, `USGS_SAMPLE` (absolute `Path`s), and possibly small `tmp_path` builders for artifact tests.
- No test file references a CWD-relative path.

- [ ] Step 1: Add conftest with absolute fixture paths.
- [ ] Step 2: Point each test at the new paths; run from `ml/` and from repo root.
- [ ] Step 3: Verify both invocations pass.
- [ ] Step 4: Delete the fixed bullets from `docs/testing-standards.md` Known Deviations.
- [ ] Step 5: Commit `test: make ml tests cwd-independent`

---

### Task 3: Web test unification + Vitest setup

**Files:**
- Modify: `web/vite.config.ts` — add a setup file registering `@testing-library/jest-dom`.
- Create: `web/tests/setup.ts` — `import '@testing-library/jest-dom'`.
- Modify: `web/tests/DashboardCard.test.tsx`, `web/tests/DashboardStates.test.tsx`, `web/tests/RiskProfile.test.tsx` — convert `renderToStaticMarkup` regex assertions to @testing-library `render`/`screen` queries.
- Test: `web/tests/*.test.tsx` all green; `npm run build` green.

**Deviation trace:** `docs/testing-standards.md` → Known Deviation 3.

**Interfaces:**
- Single component-test style: @testing-library/react `render`/`screen` + `describe`/`it`.
- No `renderToStaticMarkup` regex-based tests remain.
- jest-dom matchers available in every test via the shared setup file.

- [ ] Step 1: Add `vitest` setup file + config entry.
- [ ] Step 2: Convert one test file as the reference pattern.
- [ ] Step 3: Convert the remaining files; run `npm test` and `npm run build`.
- [ ] Step 4: Delete the fixed bullet from `docs/testing-standards.md` Known Deviations.
- [ ] Step 5: Commit `test: unify web component test style`

---

### Task 4: Mobile API/naming contract

**Why separate:** mobile's camelCase `HazardEvent` is a breaking contract decision once real fetches land; explicitly mapping at the `services/api.ts` boundary must exist first.

**Files:**
- Create: `mobile/src/services/api.ts` (replace constant-only version) — `API_BASE_URL` from env (mirror web's `VITE_API_BASE_URL` pattern) + `fetchEvents()` returning wire-shape data.
- Create: `mobile/src/services/mappings.ts` — `toServiceHazardEvent(wire)` converting snake_case fields to the UI-native type; reverse mapping where needed.
- Modify: `mobile/src/types/hazard.ts` — keep camelCase UI-native types; document that they are never raw API payloads.
- Test: `mobile/tests/mappings.test.ts`, `mobile/tests/api.test.ts` (create).

**Deviation trace:** `docs/glossary.md` → Field-Naming Rule note 3; `docs/api-contracts.md` → Known Deviation (mobile mapping); `docs/error-handling-and-logging.md` → Known Deviation 5.

**Interfaces:**
- `mappings.toHazardEvent(wire: WireHazardEvent): HazardEvent` — field-by-field conversion, unit tested against a fixture mirroring `backend/app/schemas/hazard_event.py`.
- `api.fetchEvents(): Promise<WireHazardEvent[]>` — typed fetch with named errors.

- [ ] Step 1: Write failing mapping tests (fixture payload; assert every field maps).
- [ ] Step 2: Implement `mappings.ts`.
- [ ] Step 3: Implement `api.ts` with env-driven base URL and typed errors.
- [ ] Step 4: Add service tests for the failure path.
- [ ] Step 5: Run `npm test` from `mobile/`.
- [ ] Step 6: Update the fixed Known Deviations bullets.
- [ ] Step 7: Commit `feat: add mobile api mapping layer`

---

### Task 5: Refresh `web/WEB_STRUCTURE.md`

**Files:**
- Modify: `web/WEB_STRUCTURE.md` — reflect current code: `DashboardMapArea`, `DashboardSidebar`, `TopNav`, live MapLibre `MapView`, `useEvents`/`useEventSummary`/`useRiskProfiles`; mark `useFaultLines` and `useRealtimeAlerts` as stubs; add `EventSummary` type; keep the endpoint list in sync with `docs/api-contracts.md`.

**Deviation trace:** Audit row #8 (staleness: 472-line in-package doc describing placeholder components and stubs as live).

- [ ] Step 1: Diff the doc against `web/src` (components, hooks, types, api client).
- [ ] Step 2: Rewrite the stale sections; keep the accurate ones.
- [ ] Step 3: Cross-check the endpoint list against `docs/api-contracts.md`.
- [ ] Step 4: Commit `docs: refresh web structure doc`

---

## Notes for the executor

- Tasks can run in any order (each self-contained), but Task 1 is the highest-value first fix per the standards-sequencing decision.
- Task 1 integration tests need the PostGIS test harness from `backend/tests/integration/conftest.py`.
- Before starting any task, re-read the "Known deviations" section it targets — sections may have been partially fixed by other work since this plan was written.

## Verification record (2026-09-10)

- Backend suite: 86 passed (67 unit and 19 integration) after starting Docker
  PostGIS and Redis. Coverage includes import refresh, rollback, provenance,
  projection, API contracts, canonical events and realtime delivery.
- Development database migrated from `0001` through `0003`; PostGIS 3.4 verified.
  Integration tests used the separate `geohazard_test` database.
- ML: 16 passed from `ml/` and the repository root.
- Web: 47 passed; production build passed (existing bundle-size warning remains).
- Mobile: 4 passed.
- Structure verifier, changed backend Ruff checks and `git diff --check` passed.
- GEM: 155 validated reference features imported into the development database.
  Local ignored subset retains provenance/checksums. PHIVOLCS vector loading remains pending.
