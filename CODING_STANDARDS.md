# GeoHazard PH - Coding Standards & Guidelines

**Last Updated**: August 27, 2026  
**Project**: GeoHazard PH

---

## Table Of Contents

1. Purpose
2. Technology Stack
3. Project Architecture
4. File Naming Conventions
5. Code Style And Formatting
6. Import Standards
7. Git Workflow
8. Feature Implementation Checklist
9. Bug Fix Checklist
10. Backend API Standards
11. ML Pipeline Standards
12. Web App Standards
13. Mobile App Standards
14. Data And Ingestion Standards
15. Error Handling
16. Security Standards
17. Testing Standards
18. CI And Pull Request Requirements
19. Local Development Setup
20. Dependency Management
21. Quick Reference

---

## Purpose

This document is the source of truth for all human-written and generated code in this repository.

All new code, documentation, tests, scripts, generated scaffolds, and future AI-assisted changes must follow these standards unless a pull request explicitly documents a justified exception.

When another document conflicts with this one, follow the more specific rule for the affected package. If there is still a conflict, update the documentation before changing behavior.

### Documentation Hub

This document is the general standard. Detailed, stack-specific contracts live next to it and take precedence for their scope — read the relevant one before work in that area:

- `BACKEND_STANDARDS.md` — backend code contract (routes, DI, services, models, ingestion).
- `docs/api-contracts.md` — endpoint naming, response shapes, error envelope, versioning.
- `docs/testing-standards.md` — per-stack test locations, naming, and what "done" means.
- `docs/error-handling-and-logging.md` — error envelope and logging rules for all stacks.
- `docs/glossary.md` — canonical domain vocabulary and field names.
- `docs/git-workflow.md` — worktrees, agent commit checklist, merge policy.
- `docs/superpowers/templates/` — spec and plan templates.

---

## Technology Stack

- **Backend API**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, GeoAlchemy2, PostGIS, Redis.
- **Ingestion**: Python workers and scheduled source adapters under `backend/ingestion`.
- **ML Pipeline**: Python 3.11+, pandas, scikit-learn, joblib, Kaggle datasets.
- **Web App**: React 18, TypeScript, Vite, TanStack Query, MapLibre GL.
- **Mobile App**: Expo / React Native, TypeScript.
- **Infrastructure**: Docker Compose, Nginx, Terraform placeholder, GitHub Actions.
- **Testing**: pytest for Python packages, Vitest for web, npm test for mobile.
- **Formatting/Linting**: Ruff for Python where configured, TypeScript compiler for web build validation.
- **Package Managers**: pip for Python packages, npm for JavaScript and TypeScript packages.

---

## Project Architecture

### Directory Structure

```text
backend/
  app/
    api/          # FastAPI dependency and route modules
    core/         # Database, Redis, logging, security primitives
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request and response schemas
    services/     # Business logic and reusable backend operations
  ingestion/      # External source adapters, scraping helpers, schedulers
  tests/          # Backend unit and integration tests

ml/
  src/ml/         # Regional risk-profile pipeline modules
  tests/          # ML unit tests and fixtures

web/
  src/
    api/          # HTTP clients and API adapters
    components/   # Reusable UI components
    hooks/        # React hooks and async data access
    pages/        # Route-level screens
    styles/       # Global CSS
    types/        # Shared TypeScript types
  tests/          # Web tests

mobile/
  src/
    navigation/   # Mobile navigation setup
    screens/      # Screen-level React Native views
    services/     # API, cache, push notification helpers
    types/        # Shared TypeScript types
  tests/          # Mobile tests

.github/workflows/ # GitHub Actions workflows
docs/              # Architecture, runbooks, ADRs, specs, and plans
scripts/           # Local verification, imports, and training helpers
data/              # Local static data drop zones
infra/             # Deployment and infrastructure support files
```

### Architectural Principles

1. **Keep boundaries clear**
   - API route modules should handle HTTP concerns and delegate behavior.
   - Services should hold business rules, external integrations, and reusable operations.
   - Schemas should define input and output contracts.
   - Models should represent database persistence only.
   - Frontend components should render UI; hooks and API clients should handle data access.

2. **Prefer small modules**
   - A file should have one clear responsibility.
   - Split code when route handling, business logic, data mapping, and UI state start mixing.
   - Do not introduce broad abstractions until at least two concrete use cases need them.

3. **Treat geohazard data carefully**
   - Generated risk labels are descriptive statistical profiles, not predictions.
   - Do not imply earthquake prediction, official warning status, or government endorsement unless an official source is explicitly cited.
   - Preserve source names, timestamps, coordinates, and units when importing external data.

4. **Document behavior-changing decisions**
   - Architecture decisions belong in `docs/adr/`.
   - Operational procedures belong in `docs/runbook.md`.
   - Source-data assumptions belong in `docs/data-sources.md`.

---

## File Naming Conventions

| Area | Convention | Example |
| --- | --- | --- |
| Python modules | `snake_case.py` | `risk_profile.py` |
| Python tests | `test_<module>.py` | `test_usgs_parser.py` |
| FastAPI route modules | plural resource name | `events.py` |
| Backend services | noun or capability | `proximity.py` |
| Backend schemas | resource name | `hazard_event.py` |
| Backend models | resource name | `fault_line.py` |
| React components | `PascalCase.tsx` | `RiskProfileCard.tsx` |
| React hooks | `useThing.ts` | `useRiskProfiles.ts` |
| TypeScript types | domain name | `hazard.ts` |
| Pages/screens | `PascalCase.tsx` | `Dashboard.tsx` |
| Scripts | action-oriented name | `import_fault_lines.py` |
| Docs | lowercase kebab-case | `data-sources.md` |
| Workflow files | lowercase kebab-case | `backend-ci.yml` |

Use clear domain names over abbreviations. Accept common abbreviations only when they are already established in the project or source data, such as `USGS`, `GVP`, `PHIVOLCS`, `API`, `ML`, and `CI`.

---

## Code Style And Formatting

### General Rules

- Keep files ASCII unless the existing file already uses non-ASCII or the domain requires it.
- Use 100 columns as the default Python line length.
- Keep TypeScript and Markdown lines readable; do not force awkward wrapping for URLs or tables.
- Prefer explicit names over comments.
- Add comments only for complex domain rules, non-obvious source-data handling, or operational caveats.
- Remove debug logs, commented-out code, and temporary scripts before committing.
- Do not commit generated build artifacts such as `web/dist/`, Python caches, or local model artifacts unless explicitly required.

### Python

- Use type hints for public functions, service functions, and ML pipeline entry points.
- Use `snake_case` for functions, variables, and module names.
- Use `PascalCase` for classes and Pydantic schemas.
- Keep pure data transformations easy to test without network or database dependencies.
- Prefer standard library functionality before adding a dependency.

### TypeScript

- Use TypeScript for all web and mobile source files.
- Use `PascalCase` for components and screens.
- Use `camelCase` for variables, functions, hooks, and props.
- Keep component props typed explicitly.
- Avoid `any`. If the incoming data is unknown, model it with a type, validate it, or narrow it before use.
- Keep UI text and API data mapping separate when practical.

### Markdown

- Use concise headings.
- Prefer fenced code blocks with language tags.
- Keep setup instructions command-oriented and testable.
- Update docs in the same change when behavior, setup, or commands change.

---

## Import Standards

### Python Imports

Use standard-library imports first, third-party imports second, and local imports last.

```python
from datetime import UTC, datetime

import pandas as pd
from fastapi import APIRouter

from app.schemas.hazard_event import HazardEvent
```

Rules:

- Do not use wildcard imports.
- Avoid import-time network calls, file writes, or database connections.
- Keep optional heavyweight dependencies inside the function that needs them when startup cost matters.
- Backend imports are resolved from `backend/`; ML imports are resolved from `ml/src`.

### TypeScript Imports

Use ES module imports.

```typescript
import { useQuery } from '@tanstack/react-query';

import { fetchRiskProfiles } from '../api/client';
import type { RiskProfile } from '../types/hazard';
```

Rules:

- Use `import type` for type-only imports.
- Keep relative paths readable; avoid deeply nested imports by moving shared code to the right folder.
- Do not add path aliases unless the repo is configured and tests/builds support them.

---

## Git Workflow

> See `docs/git-workflow.md` for worktree-per-feature mapping, the agent commit checklist, and the merge policy.

### Branching Strategy

Use feature branches for non-trivial work. Keep `main` deployable and reviewable.

Branch naming examples:

```bash
feat/risk-profile-api
fix/usgs-parser-timezone
docs/coding-standards
ci/web-build-check
```

### Commit Message Convention

Use Conventional Commits:

```bash
feat: add regional risk profile endpoint
fix: handle empty earthquake dataset
docs: add coding standards
ci: move workflows into github actions directory
test: add parser regression coverage
refactor: split map layer controls
chore: update package metadata
```

Allowed types:

- `feat`
- `fix`
- `docs`
- `ci`
- `test`
- `refactor`
- `style`
- `perf`
- `chore`

Keep commit messages imperative, lowercase after the type, and focused on one change.

---

## Feature Implementation Checklist

Before implementing a feature:

- [ ] Read this coding standard.
- [ ] Check existing modules for the closest local pattern.
- [ ] Define the smallest useful behavior.
- [ ] Identify package-specific test commands.
- [ ] Add or update tests before changing behavior when practical.
- [ ] Keep unrelated refactors out of the feature change.

For backend features:

- [ ] Add or update Pydantic schemas in `backend/app/schemas`.
- [ ] Add route handling in `backend/app/api/v1`.
- [ ] Put business logic in `backend/app/services`.
- [ ] Add database models only when persistence is needed.
- [ ] Add unit tests for services and integration tests for API behavior.

For ML features:

- [ ] Keep source ingestion, feature building, clustering/classification, evaluation, and persistence separated.
- [ ] Add small fixtures under `ml/tests/fixtures`.
- [ ] Make training outputs deterministic where possible.
- [ ] Document generated artifacts and assumptions.

For web or mobile features:

- [ ] Add typed API contracts.
- [ ] Keep network calls in `api/` or `services/`.
- [ ] Put reusable UI in components and route-level composition in pages or screens.
- [ ] Cover important rendering, state, and data-mapping behavior with tests where the test setup exists.

Final checks:

- [ ] Run the relevant package tests.
- [ ] Run build commands for changed frontend packages.
- [ ] Run `python scripts\verify_structure.py` when project structure changes.
- [ ] Update README or docs for setup, command, API, or workflow changes.
- [ ] Confirm `git diff --check` passes.

---

## Bug Fix Checklist

1. **Reproduce**
   - Capture the failing command, request, screen, or data sample.
   - Read the full error message and stack trace.

2. **Find root cause**
   - Trace the bad value or behavior to its source.
   - Compare with a similar working module.
   - Avoid broad changes until the cause is understood.

3. **Add regression coverage**
   - Add the smallest failing test that proves the bug.
   - Verify the test fails for the expected reason before fixing.

4. **Fix minimally**
   - Change the source of the bug.
   - Avoid unrelated style edits.

5. **Verify**
   - Run the targeted test.
   - Run the affected package test suite.
   - Document any remaining risk in the PR.

---

## Backend API Standards

> See `BACKEND_STANDARDS.md` for the full backend contract and `docs/api-contracts.md` for the wire contract.

### Route Structure

Use versioned API modules under `backend/app/api/v1`.

Recommended REST patterns:

```text
GET    /api/v1/resources
GET    /api/v1/resources/{id}
POST   /api/v1/resources
PUT    /api/v1/resources/{id}
DELETE /api/v1/resources/{id}
```

Only add mutating endpoints when the data lifecycle is clear. Read-only source-data endpoints are preferred for imported public hazard datasets until persistence and authority rules are defined.

### FastAPI Pattern

```python
from fastapi import APIRouter, HTTPException

from app.schemas.hazard_event import HazardEvent
from app.services.events import list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[HazardEvent])
def get_events() -> list[HazardEvent]:
    return list_events()
```

Rules:

- Keep route functions thin.
- Use `response_model` for public responses.
- Validate inputs with Pydantic models or FastAPI parameter types.
- Return typed schema objects or dictionaries that match the response model.
- Use `HTTPException` at the route boundary for expected HTTP errors.

### Response Standards

- Single resource endpoints return the resource object.
- List endpoints return a list for simple collections, or a structured object when pagination or summary metadata is needed.
- Error responses should be clear, stable, and safe to expose.
- Use ISO 8601 strings for datetimes in API responses.
- Preserve latitude and longitude names consistently.

### Status Codes

| Code | Use Case |
| --- | --- |
| 200 | Successful read or update |
| 201 | Created resource |
| 400 | Invalid request or unsupported parameters |
| 401 | Missing or invalid authentication |
| 403 | Valid identity without permission |
| 404 | Resource not found |
| 409 | Duplicate or conflicting state |
| 422 | Pydantic validation error |
| 500 | Unexpected server error |

---

## ML Pipeline Standards

- Keep pipeline steps composable: ingest, clean, feature-build, train, evaluate, persist.
- Functions should accept paths or data frames and return explicit values.
- Avoid hidden writes unless the function name clearly communicates persistence.
- Keep random seeds configurable or fixed for repeatable tests.
- Persist model artifacts with metadata that includes source datasets, artifact version, generated timestamp, row counts, and feature names.
- Do not label outputs as forecasts or predictions unless the model and validation actually support forecasting.
- Tests should use small fixtures and avoid network access.

Example function shape:

```python
from pathlib import Path

import pandas as pd


def load_region_events(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)
```

---

## Web App Standards

- Keep `web/src/App.tsx` focused on app composition and providers.
- Put route-level screens under `web/src/pages`.
- Put reusable UI under `web/src/components`.
- Put async data fetching hooks under `web/src/hooks`.
- Put HTTP client functions under `web/src/api`.
- Keep shared domain types under `web/src/types`.
- Prefer controlled, typed state over implicit `any` objects.
- Keep map rendering concerns isolated in map components.
- Do not block the main UI on optional realtime or map overlay data; handle loading and empty states explicitly.

### Web styling (CSS Modules + design tokens)

- Style every component with a colocated `*.module.css`; import as `import styles from './X.module.css'`.
- Consume **design tokens** from `web/src/styles/tokens.css` (single source of truth). Never hard-code brand hex values in component source or modules — add a token (primitive + semantic alias) if a new color is needed. See `web/DESIGN_NOTES.md`.
- Keep the three global stylesheets thin: `tokens.css` (variables), `base.css` (reset/typography/a11y), `utilities.css` (small shared helpers). No Tailwind.
- Gate all motion behind `prefers-reduced-motion`; prefer CSS transitions + an `IntersectionObserver` reveal (`components/common/Reveal`) over animation libraries.
- Render missing data as loading skeletons or styled "Coming soon" placeholders — never a bare "Not available" or an empty box.

Component pattern:

```typescript
type RiskProfileCardProps = {
  regionName: string;
  riskLabel: string;
};

export function RiskProfileCard({ regionName, riskLabel }: RiskProfileCardProps) {
  return (
    <article>
      <h2>{regionName}</h2>
      <p>{riskLabel}</p>
    </article>
  );
}
```

---

## Mobile App Standards

- Keep screen components under `mobile/src/screens`.
- Keep navigation setup under `mobile/src/navigation`.
- Keep API, offline cache, and push notification code under `mobile/src/services`.
- Keep shared types under `mobile/src/types`.
- Do not assume network availability.
- Keep offline-cache behavior testable without a device runtime.
- Avoid platform-specific code unless the feature requires it.

---

## Data And Ingestion Standards

- Treat external source adapters as unreliable I/O boundaries.
- Validate source payload shape before mapping to internal schemas.
- Preserve source identifiers and timestamps for deduplication.
- Normalize units and coordinate order explicitly.
- Cache or fixture sample payloads only when licenses and size are appropriate.
- Never commit private API keys, credentials, or large raw datasets.
- Prefer small representative fixtures for tests.

Source adapter pattern:

```python
def parse_usgs_feature(feature: dict) -> HazardEvent:
    # Map source payload into the internal schema.
    ...
```

---

## Error Handling

> See `docs/error-handling-and-logging.md` for the error envelope and logging rules that apply to every stack.

### Backend

- Raise clear domain errors in services when useful.
- Convert expected failures to `HTTPException` in API routes.
- Keep unexpected exceptions visible to logs but safe in client responses.
- Do not leak credentials, file paths with secrets, or raw tokens in errors.

### ML

- Fail fast for missing required files, columns, or credentials.
- Include the missing path, column, or configuration key in the error message.
- Keep network-dependent errors separate from parsing and model-training errors.

### Frontend

- Render loading, empty, and error states for API-backed views.
- Keep user-facing error messages concise.
- Log technical details only where appropriate for local debugging.

---

## Security Standards

- Never commit `.env`, credentials, tokens, private keys, or Kaggle secrets.
- Keep required environment variables documented in `.env.example`.
- Use environment variables for secrets and environment-specific URLs.
- Validate incoming API inputs.
- Sanitize or reject untrusted source data before persistence.
- Do not log sensitive request headers or credentials.
- Keep CORS, authentication, and authorization rules explicit when they are introduced.
- Review dependency licenses and security impact before adding packages.

---

## Testing Standards

> See `docs/testing-standards.md` for per-package test locations, naming, fixture rules, and what "done" means.

### Required Commands

Run backend tests from `backend/`:

```powershell
pytest -v
```

Run ML tests from `ml/`:

```powershell
pytest -v
```

Run web tests and build from `web/`:

```powershell
npm test
npm run build
```

Run mobile tests from `mobile/`:

```powershell
npm test
```

Run structure verification from the repository root:

```powershell
python scripts\verify_structure.py
```

Run whitespace/conflict-marker checks from the repository root:

```powershell
git diff --check
```

### Test Rules

- Tests should be deterministic and independent.
- Use fixtures instead of live network calls.
- Test data transformations directly.
- For bug fixes, add a regression test that fails before the fix.
- For API changes, cover the route behavior and service behavior when practical.
- For frontend changes, cover rendering and user-visible behavior where the test setup supports it.

---

## CI And Pull Request Requirements

GitHub Actions workflows must live under `.github/workflows`.

Current workflow responsibilities:

- `backend-ci.yml`: install backend package and run backend pytest.
- `web-ci.yml`: install web dependencies and run web build.
- `mobile-ci.yml`: install mobile dependencies and run mobile tests.
- `deploy-staging.yml`: manual staging deployment placeholder.

Before opening or merging a PR:

- [ ] Use a feature branch for reviewable work.
- [ ] Keep commits conventional and focused.
- [ ] Run relevant local checks.
- [ ] Confirm CI workflow files are under `.github/workflows`.
- [ ] Describe testing performed in the PR.
- [ ] Document database, API, environment, or setup changes.
- [ ] Call out breaking changes explicitly.

Suggested PR description:

```markdown
## Summary

- Added or changed ...

## Testing

- `pytest -v` from `backend`
- `pytest -v` from `ml`
- `npm run build` from `web`

## Notes

- Environment changes: none
- Breaking changes: none
```

---

## Local Development Setup

Follow `README.md` for complete setup. Keep this quick reference aligned with README changes.

Linux users should follow the README's **Linux (Bash)** setup, which uses separate
`backend/.venv` and `ml/.venv` environments and applies database migrations before
starting the API. The commands below use PowerShell.

First-time setup:

```powershell
Copy-Item .env.example .env
docker compose up postgres redis
Set-Location backend
pip install -e ".[dev]"
Set-Location ..\ml
pip install -e ".[dev]"
Set-Location ..\web
npm install
Set-Location ..\mobile
npm install
Set-Location ..
```

Daily development:

```powershell
docker compose up postgres redis
```

Backend:

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

Web:

```powershell
Set-Location web
npm run dev
```

ML training:

```powershell
.\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Download
```

---

## Dependency Management

### Python

- Add runtime dependencies to the relevant `pyproject.toml`.
- Add test, lint, and developer-only packages under `[project.optional-dependencies].dev`.
- Keep backend and ML dependencies separated unless both packages truly need the same package.
- Verify imports after adding dependencies.

### JavaScript And TypeScript

- Use npm for `web/` and `mobile/`.
- Commit `package-lock.json` changes when dependency changes affect packages that have lockfiles.
- Consider bundle size for web dependencies.
- Avoid adding UI libraries for one-off controls.

Checklist before adding a dependency:

- [ ] Existing standard library or local code cannot reasonably solve the problem.
- [ ] Package is maintained.
- [ ] License is compatible with this project.
- [ ] Security impact is acceptable.
- [ ] Tests and builds pass after installation.

---

## Quick Reference

### New Backend Endpoint

1. Add schema in `backend/app/schemas`.
2. Add service logic in `backend/app/services`.
3. Add route in `backend/app/api/v1`.
4. Register router in `backend/app/main.py` when needed.
5. Add backend tests.
6. Run `pytest -v` from `backend/`.

### New ML Pipeline Behavior

1. Add or update fixture in `ml/tests/fixtures`.
2. Add failing test in `ml/tests`.
3. Update focused module under `ml/src/ml`.
4. Run `pytest -v` from `ml/`.
5. Document artifact or source-data changes.

### New Web Feature

1. Add or update type in `web/src/types`.
2. Add API client or hook if data-backed.
3. Add component or page.
4. Add/update tests where practical.
5. Run `npm test` and `npm run build` from `web/`.

### New Mobile Feature

1. Add or update type in `mobile/src/types`.
2. Add service logic under `mobile/src/services`.
3. Add screen or navigation changes.
4. Add/update tests where practical.
5. Run `npm test` from `mobile/`.

### Final Pre-Commit Check

```powershell
git status --short
git diff --check
python scripts\verify_structure.py
```

Run package-specific tests for every package touched by the change.
