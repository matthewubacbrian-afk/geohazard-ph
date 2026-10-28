# PHIVOLCS Earthquake Feed UTF-8 Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve UTF-8 PHIVOLCS earthquake place names from source response through the API and Android display.

**Architecture:** Decode raw response bytes at the earthquake feed adapter before the existing HTML parser. Keep the event schema and clients unchanged. Reingest a recent event to update its stored place name, then check the API and phone.

**Tech Stack:** Python 3.11, Requests, Beautiful Soup, pytest, Ruff, Docker Compose, Android Debug Bridge.

**Spec:** `docs/superpowers/specs/2026-10-29-phivolcs-earthquake-utf8-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.
- Use one isolated branch and Conventional Commits. Preserve the unrelated `web/index.html` edit on main and the scene-model preflight worktree.
- Run backend tests from `backend/`. Integration tests may use only the dedicated `geohazard_test` database, never the app database.
- Do not commit credentials, generated artifacts, caches, or source payloads.
- Verify the event API and phone separately; a successful parser test does not prove deployed or device behavior.

---

### Task 1: Reproduce and fix the response decoding defect

**Files:**
- Modify: `backend/tests/unit/test_phivolcs_earthquake_parser.py`
- Modify: `backend/ingestion/sources/phivolcs_earthquake.py`

**Interfaces:** `fetch_recent_events(settings, *, session=None) -> list[HazardEvent]` stays unchanged. A Requests-like response supplies `content: bytes`; the adapter decodes it as UTF-8 with strict errors.

- [x] **Step 1: Write the failing regression.** Change `FakeResponse` to model the observed Requests fallback and update the existing fake feed. Add the exact place-name assertion and a separate invalid-byte case:

  ```python
  class FakeResponse:
      def __init__(self, content: bytes):
          self.content = content
          self.text = content.decode("latin-1")

      def raise_for_status(self) -> None:
          return None

  # In fake_get for the existing configured-feed test:
  return FakeResponse(html.encode("utf-8"))

  # After fetch_recent_events(settings):
  assert events[0].place_name == "010 km N 46° W of Polillo (Quezon)"

  # In a new test, monkeypatch requests.get to return FakeResponse(b"\xff"):
  with pytest.raises(PhivolcsFetchError, match="parsing failed"):
      fetch_recent_events(get_settings())
  ```
- [x] **Step 2: Run the focused tests from `backend/`.** Use `py -3.11 -m pytest tests/unit/test_phivolcs_earthquake_parser.py -q`. The place-name assertion failed with the extra `Â` before code changes, and the invalid-byte case failed with the old missing-table error.
- [x] **Step 3: Implement the boundary fix.** Replace the parse call inside the existing parsing `try` block. The generic wrapper converts `UnicodeDecodeError` to `PhivolcsFetchError` without ingesting a row:

  ```python
  return _parse_bulletin_table(response.content.decode("utf-8"))
  ```

  Do not add fallback repair or client changes.
- [x] **Step 4: Verify green.** Focused tests passed 5/5, the full suite passed 151/151 against the dedicated `geohazard_test` DB, and `ruff check --config pyproject.toml .` passed from `backend/`.
- [x] **Step 5: Commit.** The backend fix was committed as `67963987` (`fix: decode phivolcs earthquake feed as utf8`).

### Task 2: Integrate Android evidence and verify the running flow

**Files:**
- Modify: `docs/mobile-runtime-smoke-test.md`
- Modify: `docs/project-status.md`
- Modify: `PLAN.md`

**Interfaces:** No API or schema change. The runtime result must identify app commit, Android version, API environment, observed event, and limits.

- [x] **Step 1: Bring in the existing evidence.** Cherry-pick the documentation-only Android observations `566205fc` and `f4e50737` from `codex/android-device-smoke`; both applied without conflict.
- [x] **Step 2: Exercise fresh ingestion.** A one-off backend image from this branch fetched 1,678 rows and updated 1,676 unique events on the existing `ghph-device_default` development network. The running API returned a recent place name with `°`. The 27 remaining malformed IDs were absent from the current feed. The command used PowerShell syntax:

  ```powershell
  docker build -t ghph-phivolcs-utf8:local .\backend
  docker run --rm --network ghph-device_default --env DATABASE_URL=postgresql+psycopg://geohazard:geohazard@postgres:5432/geohazard --env REDIS_URL=redis://redis:6379/0 ghph-phivolcs-utf8:local python -c "from ingestion.scheduler import run_phivolcs_ingest; print(run_phivolcs_ingest())"
  Invoke-RestMethod 'http://localhost:8000/api/v1/events?source=phivolcs'
  ```

  Record the event ID and response; do not assume old events outside the recent feed are repaired.
- [ ] **Step 3: Verify Android if connected.** Use the installed SDK tool at `C:\Users\matth\AppData\Local\Android\Sdk\platform-tools\adb.exe` to reapply `reverse tcp:8000 tcp:8000` and `reverse tcp:8081 tcp:8081`, refresh Nearby/Alerts, and inspect the corrected place name on the physical phone. If the device is unavailable, record the API result and mark device verification pending.
- [x] **Step 4: Update tracking.** The test and API observations are recorded; device verification remains explicitly pending. Scene-model 503, iOS, staging, and historical-backfill gates stay open. Structure verification and `git diff --check` passed.
- [x] **Step 5: Commit documentation** as `a85e5245` (`docs: record phivolcs encoding verification`); reviewer-requested source-data and date corrections followed in `e5b402da`.

### Task 3: Review and integrate

**Files:** No new source files.

- [x] **Step 1:** Reviewed branch scope and received independent read-only review. No code defect or generated-file issue was found; the reviewer required CI and phone display before merge and requested two documentation corrections, now committed.
- [ ] **Step 2:** Run required package verification and exact-head CI. Inspect all checks before reporting a pass; Android phone verification remains a separate result.
- [ ] **Step 3:** Open a focused PR with the actual tests and runtime limits. Merge only after the project workflow gates are met.

## Notes for the executor

The baseline focused parser suite passed 4/4 in the new worktree before changes. The local Docker API, Postgres, and Redis were running during planning, but the phone was not listed by ADB. Check both again before the runtime step. Existing Docker containers may be based on the previous worktree; never replace them without first identifying their Compose project and active data. The `codex/scene-model-preflight` branch records a separate Linux AMD64 finding and stays separate.
