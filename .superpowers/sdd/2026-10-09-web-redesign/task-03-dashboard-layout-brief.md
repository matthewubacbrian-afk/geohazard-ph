# Task 3 — Dashboard layout and scrollable controls

## Scope

Implement the approved desktop, tablet, and mobile dashboard composition while keeping every existing sidebar callback and query-backed control. Preserve and integrate the pre-existing dirty scroll sizing edits in `Dashboard.module.css`, `DashboardSidebar.module.css`, and `DashboardLayout.test.mjs`.

## Acceptance

- Desktop uses bounded controls/map/activity columns; tablet puts activity below controls/map; mobile stacks controls, map, and activity in document order.
- Sidebar control body scrolls within bounded layouts and expands naturally on mobile.
- Views, basemap, all event/layer/category toggles, both date fields, and magnitude slider retain accessible names.
- Focused dashboard tests and web build pass; no APIs, hooks, types, or query-state behavior change.

## Verification

Run focused Vitest dashboard tests, `npm run build`, and `git diff --check`. Full browser viewport review is deferred to Task 7 because the user's instruction currently keeps project services stopped.
