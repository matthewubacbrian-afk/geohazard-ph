# Testing Standards

**Project**: GeoHazard PH
**Scope**: All packages — `backend/`, `ml/`, `web/`, `mobile/`. Read this before writing any test, in any stack.

This document defines where tests live, how they are named, what "done" means, and how mocking and fixtures work in each package. It supplements the command list and test rules in `CODING_STANDARDS.md`.

Related contracts:
- `BACKEND_STANDARDS.md` — backend module and service shape that tests exercise.
- `docs/api-contracts.md` — response shapes that integration tests assert against.
- `docs/error-handling-and-logging.md` — error envelope that API tests assert on.

---

## Table Of Contents

1. What "Done" Means
2. Backend
3. ML
4. Web
5. Mobile
6. Fixtures And Mocking Principles
7. Test Review Checklist
8. Known Deviations

---

## 1. What "Done" Means

A change is test-complete when:

- Every new behavior has a test that fails for the expected reason **before** the change, and passes after.
- Bug fixes add a regression test that fails on the old code.
- New API endpoints are covered at the route level (integration) and their services at the unit level.
- New ML pipeline steps are covered with small fixtures; training is exercised end-to-end from CSV fixtures without network or credentials.
- Frontend changes cover rendering, empty, and error states of the affected component.
- The package test suite passes, and the structure verifier passes when the file tree changed.
- No test depends on the process working directory, on live network access, or on a running service that the suite does not explicitly provision.

## 2. Backend

### Layout and naming

- Unit tests (DB-free): `backend/tests/unit/test_<module>.py` — for example `test_events_service.py`.
- Integration tests: `backend/tests/integration/test_<module>.py` — for example `test_events_api.py`.
- Shared fixtures: `backend/tests/conftest.py` and `backend/tests/integration/conftest.py`.
- Static payloads: `backend/tests/fixtures/`.

### Conventions

- Unit tests never touch a database or the network. Services that query are tested against a fake session or the service's pure functions.
- Mock HTTP with `monkeypatch` (for example replacing `requests.get`) or hand-rolled fakes; never spin up a live source.
- The shared integration harness in `backend/tests/integration/conftest.py` provides `migrated_engine` and `client`:
  - `migrated_engine` applies Alembic migrations to a dedicated test database.
  - `client` is a `fastapi.testclient.TestClient` with `app.dependency_overrides[get_db_session]` pointed at the test session, cleaned up in the fixture.
- Settings-dependent tests re-point config through the cached accessor:

```python
def test_endpoint(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")
```

  Always call `get_settings.cache_clear()` before every test that changes settings.

- API tests assert on the response body shape as well as the status code, including the error envelope for failure cases.

### Done for an endpoint

- [ ] Service unit test for each behavior and each error branch.
- [ ] Integration test for `200` success and each mapped error (`404`, `422`).
- [ ] When persistence changed: migration applied in CI against PostGIS.

## 3. ML

### Layout and naming

- Tests: `ml/tests/test_<module>.py` — one file per pipeline module (`test_clean_merge.py`, `test_clustering.py`, ...).
- Fixtures: `ml/tests/fixtures/` (small CSVs that mirror real source headers).
- No classes; plain `test_<behavior>` functions.

### Conventions

- Locate fixture paths by absolute paths derived from the test file, never by the working directory:

```python
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
```

  Tests must pass when run from `ml/` AND from any other directory.
- Generated artifacts and model outputs go to pytest's `tmp_path`; do not write into the repo tree during tests.
- Network and credentials are banned: Kaggle download paths are tested with a fake API object and missing-credential cases use `monkeypatch` + a redirected `Path.home()`.
- Keep training deterministic with explicit `random_state` arguments; tests assert explicit values.
- Assert on dataclass fields and exported artifact shapes (metadata keys, profile fields), not on floating-point equality of model internals.

### Done for an ML step

- [ ] Unit test per public function, including the failure branch (missing columns, missing credentials, insufficient regions).
- [ ] End-to-end `run_training` covered from CSV fixtures into a `tmp_path` artifact dir.

## 4. Web

### Layout and naming

- All tests in `web/tests/<Component>.test.tsx` — PascalCase matching the component under test (`MapView.test.tsx`, `RiskProfile.test.tsx`).
- One style only: `@testing-library/react` with `render`/`screen` and Vitest `describe`/`it`.

```tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import MapView from '../src/components/map/MapView';

describe('MapView', () => {
  it('shows an empty state when there are no events', () => {
    render(<MapView events={[]} />);
    expect(screen.getByText(/no events/i)).toBeTruthy();
  });
});
```

### Conventions

- The Vitest config in `web/vite.config.ts` sets `environment: 'jsdom'`; a setup file registers `@testing-library/jest-dom` matchers for the whole suite.
- Components that use React Query render inside a `QueryClientProvider`; hooks are mocked or the queries stubbed at the client boundary.
- External libraries with rendering or networking side effects (for example `maplibre-gl`) are mocked with `vi.mock(...)` so tests stay deterministic.
- Compose assertions with explicit states: render the component in loading, empty, and error states, not just the happy path.
- Keep tests behavior-focused; avoid asserting on implementation details such as class names or data attributes unless they are user-visible.

### Done for a component

- [ ] Render behavior for each exported state (loaded / empty / error).
- [ ] User-visible interactions (filtering, retry) exercised where present.
- [ ] `npm test` and `npm run build` pass from `web/`.

## 5. Mobile

### Layout and naming

- Tests: `mobile/tests/*.test.ts` — lowercase file matching the unit under test (`offlineCache.test.ts`, `api.test.ts`).
- Jest preset `react-native`; tests run in the `node` environment (no device runtime).
- Use `describe`/`it` for grouped cases.

### Conventions

- Offline-cache and mapping logic must be testable without a device: keep the behavior in pure functions that tests call directly.
- Screens are thin; test the services and the mapping layer rather than rendering native components.
- API mapping tests assert field-by-field conversion from the snake_case wire contract to the UI-native type.
- Test the failure path of each service, including "not configured" states.

### Done for a service

- [ ] Happy path and failure/offline path covered.
- [ ] Mapping functions unit tested against fixture payloads that mirror the backend schema.
- [ ] `npm test` passes from `mobile/`.

## 6. Fixtures And Mocking Principles

- Prefer small, representative fixtures over real payloads; never cache or commit private keys, credentials, or large raw datasets.
- Use `monkeypatch` (Python) and `vi.mock` / `vi.spyOn` (Vitest/Jest) over patching at production module scope.
- Mock at the boundary you own: HTTP and IO for backend/ML, the API client or query hook for web, services for mobile.
- A test that needs the real database or the real network belongs in the integration suite, explicitly provisioned, never in a unit test.
- Fixtures are data; build them at the top of the file or in a `conftest.py`, and assert against them rather than against literals scattered through tests.

## 7. Test Review Checklist

- [ ] Test file lives in the documented location for the package.
- [ ] Names follow the package convention (`test_<module>.py`, `<Component>.test.tsx`, `*.test.ts`).
- [ ] No CWD-relative fixture paths; no live network; no shared mutable state across tests.
- [ ] Every behavior and error branch has a test that fails before the change.
- [ ] Package command in the table below passes; run `python scripts\verify_structure.py` when files moved.

| Package | Command (run inside package dir) |
| --- | --- |
| backend | `pytest -v` |
| ml | `pytest -v` |
| web | `npm test` |
| mobile | `npm test` |

## 8. Known Deviations

Tracked as backlog items in `docs/superpowers/plans/2026-08-29-standards-gap-remediation.md`. New tests must conform today.

- `ml/tests/*` use CWD-relative fixture paths (`Path("tests/fixtures/...")`) instead of absolute paths.
- `ml/tests/` has no `conftest.py`.
- `web/tests/` mixes two styles: regex-over-`renderToStaticMarkup` and @testing-library; the vitest setup file and jest-dom registration are missing.
- `mobile/` has a single test (`offlineCache.test.ts`) in bare `test()` style, with no `describe`/`it` grouping and no service or mapping coverage.
- `backend/app/api/v1/risk_profile.py` has no `response_model`, so its API tests cannot assert the documented shape.