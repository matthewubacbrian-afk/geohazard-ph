# Task 3 — Dashboard layout and scrollable controls

## Result

- Kept the dashboard grid bounded at desktop widths with fixed-range controls and activity rails around a flexible map column.
- Kept the tablet two-column controls/map row with activity below, and stacked the complete controls, map, then activity for mobile.
- Integrated the pre-existing sidebar `min-height: 0` and vertical scrolling changes, plus the pre-existing bounded grid row regression test. On mobile, the sidebar body expands in document flow instead of becoming a nested scroll area.
- Added an accessible name to the minimum-magnitude slider. Existing view, basemap, layer/category toggle, and date labels remain intact; assertions cover all of them.
- Preserved all component props/callbacks and dashboard query-state behavior. No API, hook, type, backend, mobile, or ML files changed.

## Pre-existing dirty work integrated

At task start, the checkout contained uncommitted edits in `web/src/components/dashboard/DashboardSidebar.module.css` and `web/src/pages/Dashboard.module.css`, plus the untracked `web/tests/DashboardLayout.test.mjs`. These were specifically assigned to Task 3. The sidebar min-height/scroll sizing and bounded grid row were inspected, retained, completed for responsive layouts, and committed with this task.

## Verification

- Red check: removing `.body { overflow-y: auto; }` made `DashboardLayout.test.mjs` fail; restoring it made the layout assertion pass.
- Red check: removing the minimum-magnitude accessible name made the new sidebar assertion fail; restoring it made the assertion pass.
- `npm test -- --run tests/DashboardSidebar.test.tsx tests/DashboardLayout.test.mjs`: passed, 2 files / 8 tests.
- `npm run build`: passed (TypeScript and Vite production build).
- `git diff --check`: passed.
- Full browser inspection at 1440px, 900px, and 390px remains for Task 7. Project services were kept stopped as instructed, so no browser layout claim is made here.
