# Frontend Backend Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect every visible web control to the existing backend API or a real local UI action.

**Architecture:** Keep the existing React Query and API-client boundaries. Dashboard controls own filter state in `Dashboard`, pass typed callbacks into the sidebar, and send supported event filters to `/api/v1/events`; view controls select existing panels. Navigation remains app-state based, while settings and detail/report actions use focused local panels or existing data views. Controls without backend contracts remain explicitly disabled.

**Tech Stack:** React 18, TypeScript, TanStack Query, Vite, Vitest, Testing Library, FastAPI REST API.

---

### Task 1: Extend event query contract

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useEvents.ts`
- Modify: `web/src/types/hazard.ts` only if the existing event type requires no changes
- Test: `web/tests/client.test.ts`

- [ ] Add typed optional `since`, `source`, `min_magnitude`, and `max_magnitude` query parameters.
- [ ] Add a focused test asserting only defined parameters are encoded and the response is parsed.
- [ ] Run the focused test and then the existing web tests.

### Task 2: Wire dashboard filters and layers

**Files:**
- Modify: `web/src/pages/Dashboard.tsx`
- Modify: `web/src/components/dashboard/DashboardSidebar.tsx`
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx`
- Modify: `web/src/components/map/MapView.tsx`
- Test: `web/tests/Dashboard.test.tsx`

- [ ] Lift date, magnitude, risk-level, and layer state into `Dashboard`.
- [ ] Pass the supported filters into `useEvents` and keep unsupported risk filtering local.
- [ ] Render only enabled event/risk layers and provide a working panel close action.
- [ ] Add tests for filter interaction and map/report controls.

### Task 3: Wire navigation, settings, and reports

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/TopNav.tsx`
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx`
- Modify: `web/src/pages/HistoricalBrowser.tsx`
- Create: `web/src/components/common/SettingsPanel.tsx` and its CSS module if needed

- [ ] Replace `href="#"` placeholders with app navigation or intentional external links.
- [ ] Add a functional settings panel with API endpoint display and close behavior.
- [ ] Make “View Detailed Report” navigate to the risk report view.
- [ ] Make report/detail controls expose the relevant existing data.

### Task 4: Verify frontend behavior

**Files:**
- No additional source files.

- [ ] Run `npm test` from `web/`.
- [ ] Run `npm run build` from `web/`.
- [ ] Start the dev server and verify the dashboard can fetch events from the backend.
