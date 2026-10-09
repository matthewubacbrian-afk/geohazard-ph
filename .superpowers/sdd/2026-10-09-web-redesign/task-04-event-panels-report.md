# Task 4 report: Event and summary panels

## Changes

- Restyled event filters, list rows, event detail, summary overlay, and realtime
  status with the approved semantic tokens and compact data hierarchy.
- Kept map and list consuming the page's same `visibleEvents` array. API, hooks,
  event models, filters, query params, and refresh behavior were not changed.
- Preserved the server-backed average magnitude and event count, with explicit
  units and readable numeric formatting. Kept classification and dominant fault
  system labeled “Coming soon.”
- Added contextual loading semantics, strong keyboard focus, selected-state
  assertions, and feed retry coverage.
- Kept event magnitude numerals neutral because rows do not assign magnitude
  classifications.
- Added the required advisory disclaimer to realtime/data status context.

## Verification

- Focused tests: `npm test -- --run tests/EventFeed.test.tsx
  tests/EventListLive.test.tsx tests/EventSelection.test.tsx
  tests/DashboardSummary.test.tsx tests/DashboardStates.test.tsx` — passed, 5 files,
  16 tests.
- Production build: `npm run build` — passed. Vite reports its existing large
  JavaScript chunk advisory (2.32 MB minified).
- `git diff --check` — passed.

## Protected scope

No hook, API client, realtime client, type, backend, ML, or mobile files were
modified. No services were started.
