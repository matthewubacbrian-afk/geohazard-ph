# GeoHazard PH Web UI Elevation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate the existing GeoHazard PH web UI identity (not rebrand): introduce a design-token + CSS Modules foundation, refine hierarchy/spacing/motion, remove dead legacy code, replace stub pages with polished placeholders, gracefully gate missing data, and refresh the stale web docs.

**Architecture:** Styling-first structural refactor, no data-flow or backend changes. (1) create the token/base/utilities CSS layer and root import; (2) move the active components' styles into co-located CSS Modules; (3) delete dead components + the `revert` hack and convert stub pages to placeholders; (4) add intersection-reveal + micro-interaction motion; (5) update/extend web tests; (6) refresh docs. Verification every task via `npm test` + `npm run build` from `web/`, plus `python scripts\verify_structure.py` and `git diff --check` from root.

**Tech Stack:** React 18, TypeScript, Vite, Vitest + Testing Library (jsdom), plain CSS custom properties + CSS Modules, `maplibre-gl` (unchanged), `@tanstack/react-query` (unchanged). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-31-web-ui-elevation-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, and `docs/glossary.md` (keep domain terms like "risk label", "dominant fault system" in UI copy).
- Conventional Commits, imperative, lowercase after type (e.g. `feat: add web design tokens`).
- Web verification from `web/`: `npm test`, `npm run build`. Root: `python scripts\verify_structure.py`, `git diff --check`.
- Do not add npm dependencies. Do not touch backend/ML/mobile/infra.
- Do not rename or remove any public component prop/type interface consumed by the active `Hero`/`Dashboard` flow (only class/markup changes allowed).
- Do not commit credentials, generated artifacts, or large datasets.
- `prefers-reduced-motion: reduce` must disable all added motion.
- Keep the glossary term "not available" only in styled empty/`coming soon` subtext — never as bare header text; remove raw hex (`#dc2626`, `#e5e9ec`, `#5a716c`) from component `.tsx`/`.ts` source (move to tokens/modules).

## Task ordering

Tasks run sequentially (each depends on the styling layer established by its predecessor). Tasks **4 (motion)** and **5 (tests)** can be interleaved per component once modules exist, but keep verification green at each commit.

---

### Task 1: Design-token + base + utilities CSS layer

**Files:**
- Create: `web/src/styles/tokens.css`
- Create: `web/src/styles/base.css`
- Create: `web/src/styles/utilities.css`
- Modify: `web/src/main.tsx` (import the three new files after `index.css` or in place of it; the migration of `index.css` to modules happens in Task 2)
- Test: none (CSS-only); verified by build + later component modules referencing tokens

**Interfaces:**
- `tokens.css` exposes, scoped to `:root` (exact names consumed by modules; documented in `web/DESIGN_NOTES.md` in Task 6):
  - Primitives: `--gray-cream-0/50/100/150/200` ramp from existing palette; `--ink` (#181f21); `--ink-soft` (#434749); `--ink-faint` (#959c9f); `--outline` (#747879); `--outline-variant` (#c3c7c8); `--accent` (#c0392b); `--risk-high` (#c0392b); `--risk-medium` (#e3a655); `--risk-low` (#6bb4b1); `--white` (#ffffff).
  - Semantic surfaces: `--surface`, `--surface-raised`, `--surface-overlay`, `--surface-container`, `--surface-container-lowest` derived from the cream ramp.
  - Text: `--text`, `--text-muted`, `--text-faint`.
  - Border/shadows: `--border`, `--border-strong`; `--shadow-card`, `--shadow-overlay` (tinted, not pure black).
  - Type: `--font-sans` (Inter), `--font-mono` (JetBrains Mono); a type scale via `--text-*` sizes or documented clamp ramp.
  - Spacing: `--space-1..--space-12` on a 4px base.
  - Radius: `--radius-sm`, `--radius-md`, `--radius-panel`.
  - Motion: `--dur-fast`, `--dur-base`, `--ease-out`.
  - Z-index scale: `--z-topbar`, `--z-map-overlay`, `--z-map-controls`, `--z-status` (documented).
- `base.css`: reset/box-sizing, body background (`--surface`)/color/font, `:focus-visible` ring, font smoothing, and a `@media (prefers-reduced-motion: reduce)` block disabling transitions/animations.
- `utilities.css`: `.sr-only`, `.focus-ring` (or a `:focus-visible` shared rule), and reveal helper classes.
- `main.tsx`: import order `tokens.css` → `base.css` → `utilities.css` (before any module-imported styles are used).

- [ ] **Step 1: Create the three CSS files with token/base/utility contents**
- [ ] **Step 2: Update `main.tsx` imports**
- [ ] **Step 3: Run `npm run build` from `web/`, verify it passes**
- [ ] **Step 4: Commit** `feat: add web design token and base css layer`

---

### Task 2: Migrate active components to CSS Modules

Migrate the active `Hero`/`Dashboard` surface styles from the monolithic `index.css` into co-located `*.module.css`, refactoring to semantic tokens, consistent type/spacing/radius scale, tinted shadows, focus rings, and tactile `:active` presses.

**Files:**
- Create: `web/src/styles/` modules for each active component
- Create + modify per component (co-located):
  - `web/src/components/layout/TopNav.module.css` + modify `TopNav.tsx` (class imports for nav/brand/links/buttons, both hero + dashboard themes)
  - `web/src/pages/Hero.module.css` + modify `Hero.tsx` (hero section, title, subtitle, actions, process grid, about panels, footer)
  - `web/src/pages/Dashboard.module.css` + modify `Dashboard.tsx` (dashboard page + topbar + main layout)
  - `web/src/components/dashboard/DashboardSidebar.module.css` + modify `DashboardSidebar.tsx` (sections, date grid, range, checklist, tabs)
  - `web/src/components/dashboard/DashboardMapArea.module.css` + modify `DashboardMapArea.tsx` (map area, status banner, legend, controls, floating card, stats, fault box, footer)
  - `web/src/components/map/MapView.module.css` + modify `MapView.tsx` (map-canvas/map-container; move `#dc2626` marker color/pulse into a token + CSS)
  - `web/src/components/common/RiskMeter.module.css` + modify `RiskMeter.tsx`
  - `web/src/components/common/SectionHeader.module.css` + modify `SectionHeader.tsx`
- Remove/migrate: `web/src/styles/index.css` (after all kept rules are moved; delete the file and its `revert` hack)
- Test: `web/tests/DashboardCard.test.tsx`, `web/tests/DashboardStates.test.tsx`, `web/tests/MapView.test.tsx`, `web/tests/RiskProfile.test.tsx` updated as needed (see Task 5)

**Note on risk components:** `RiskProfileExplorer`, `RiskProfileCard`, `RegionLookup` are **not rendered by the active `Hero`/`Dashboard` flow** (the `useState` toggle renders only Hero or Dashboard) and depend on now-deleted legacy classes. They are **out of scope** for this task; they are candidates for the same treatment in a later pass. Do not convert or reference their legacy classes here.

**Interfaces:**
- Each module exports default `styles` object consumed as `styles.<className>` in its component.
- `DashboardMapArea` keeps its current props (`events`, `isLoading`, `error`, `onRetry`); only class/markup changes.
- `MapView` keeps props (`events`); replace the hardcoded red `#dc2626` with a token-driven class for event markers, adding magnitude-relative sizing and an optional pulse on the strongest event — pure CSS (no new deps, no `maplibre` API change). Wrap sizing logic in the GeoJSON `properties` already passed (e.g. `magnitude`), or keep radius constant if magnitude is null; do not alter the `maplibre` layer API.

- [ ] **Step 1: Create `TopNav.module.css` and update `TopNav.tsx`**
- [ ] **Step 2: Create `Hero.module.css` and update `Hero.tsx`**
- [ ] **Step 3: Create `Dashboard.module.css` / `DashboardSidebar.module.css` / `DashboardMapArea.module.css` and update components**
- [ ] **Step 4: Create `MapView.module.css` and update `MapView.tsx` (token marker styling)**
- [ ] **Step 5: Create `RiskMeter.module.css` / `SectionHeader.module.css` and update components**
- [ ] **Step 6: Remove `index.css` and the trailing `revert` hack after all rules are migrated (grep to confirm no active component still references legacy classes)**
- [ ] **Step 7: Run `npm run build` from `web/`**
- [ ] **Step 8: Commit** `refactor(web): migrate component styles to css modules`

---

### Task 3: Remove dead legacy code + convert stub pages

**Files:**
- Delete (not rendered by the active flow):
  - `web/src/components/layout/Header.tsx`
  - `web/src/components/layout/Sidebar.tsx`
  - `web/src/components/events/EventList.tsx`
  - `web/src/components/events/EventFilterBar.tsx`
  - `web/src/components/events/EventDetailPanel.tsx`
  - `web/src/components/map/LayerControls.tsx`
  - `web/src/components/map/FaultLineLayer.tsx`
  - `web/src/components/volcano/VolcanoAlertCard.tsx`
- Modify: `web/src/pages/HistoricalBrowser.tsx` → polished placeholder section
- Modify: `web/src/pages/About.tsx` → polished placeholder section
- Modify (optional, add only if it reduces duplication): `web/src/pages/App.tsx` (view switch wiring), `web/src/components/common/ComingSoon.tsx` + `ComingSoon.module.css`
- Modify: `web/src/pages/Hero.tsx` + `Hero.module.css` if nav items must keep working with the useState toggle (nav `onNavigate` still only supports `"dashboard"`; placeholders are documented surfaces with a "coming soon" body — they need no new navigation because `useState` can render them directly)

**Interfaces:**
- `App.tsx` view union becomes `"hero" | "dashboard" | "about" | "data-sources" | "historical"` (or keep `"hero" | "dashboard"` and render placeholder sections inline) — keep it minimal and do **not** add a router. Prefer the minimal reading: keep `useState<"hero" | "dashboard">`; render polished placeholder `<section>` blocks inside `Hero`/as a separate surface only if the user must click to reach them. If no new navigation is needed this pass, drop the extra union and simply ensure the stub pages are not reachable-but-broken: either render them in the toggle or leave them as clearly-marked, styled placeholders. Decision recorded here: **render the two placeholders (Historical/About) as styled sections reachable via the existing toggle** by extending the union minimally; do not add React Router.
- `ComingSoon` (if used) props: `{ title: string; description?: string }`.
- `About` and `HistoricalBrowser` render a full-width, token-styled placeholder with the domain text from the current stubs ("Data sources: USGS, PHIVOLCS, Smithsonian GVP, GEM." / "Historical event browser") in a polished empty state.

- [ ] **Step 1: Delete the eight dead component files**
- [ ] **Step 2: Grep the `web/src` tree and confirm no remaining import references the deleted files**
- [ ] **Step 3: Convert `About` and `HistoricalBrowser` to styled placeholders (optionally via a shared `ComingSoon` component)**
- [ ] **Step 4: Wire the placeholders into the `useState` view switch in `App.tsx` (extend the union minimally; no router)**
- [ ] **Step 5: Run `npm run build` from `web/`**
- [ ] **Step 6: Commit** `refactor(web): remove dead legacy components and style stub pages`

---

### Task 4: Motion — reveal + micro-interactions

**Files:**
- Create (optional): `web/src/hooks/useRevealOnScroll.ts`
- Modify: `web/src/pages/Hero.tsx` + `Hero.module.css` (scroll reveal on hero title/subtitle/CTAs and the process grid)
- Modify: interactive elements' modules (`TopNav`, `Hero`, `DashboardSidebar`, `DashboardMapArea`, `MapView`, buttons/links) — add `:active` `translateY(1px)` press, hover border/shadow transitions, focus rings
- Verify `prefers-reduced-motion: reduce` (in `base.css`) disables all of it

**Interfaces:**
- `useRevealOnScroll<T extends HTMLElement>(options?)` returns `{ ref, isVisible }` using a single `IntersectionObserver` (threshold ~0.2). Applied to reveal targets; while `isVisible` is false the element holds `opacity:0/translateY`, then transitions to visible. Must no-op/instant under reduced motion (read via `matchMedia('(prefers-reduced-motion: reduce)')` or rely on the CSS media block).
- Utility CSS classes: `.reveal` (pre-reveal hidden state) and `.reveal--visible` (shown), driven by the hook toggling a class/attribute.
- No `window.scroll` listeners, no `requestAnimationFrame` state loops, no new deps.

- [ ] **Step 1: Add `useRevealOnScroll` hook + utility reveal classes**
- [ ] **Step 2: Apply reveals to the Hero headline/subtitle/CTAs and process grid**
- [ ] **Step 3: Add tactile `:active` and hover micro-interactions to buttons/links/cards across the active modules**
- [ ] **Step 4: Verify `@media (prefers-reduced-motion: reduce)` disables transitions/reveals**
- [ ] **Step 5: Run `npm run build` from `web/`**
- [ ] **Step 6: Commit** `feat(web): add scroll reveal and micro-interaction motion`

---

### Task 5: Web tests + verification

**Files:**
- Modify: `web/tests/DashboardCard.test.tsx` — assert the card still renders real avg magnitude + event count from the summary, and that missing-data fields render the styled empty/`coming soon` state (not the literal string "Not available")
- Modify: `web/tests/DashboardStates.test.tsx` — assert loading skeleton + retry-able error markup after the redesign
- Modify: `web/tests/MapView.test.tsx` — assert markers still render from fixture events (adjust for any class/markup change)
- Modify: `web/tests/RiskProfile.test.tsx` — only if `RiskProfileCard`/`RegionLookup` classes changed (they are out of scope unless touched; if untouched, no change)

**Interfaces:**
- Tests use the existing `renderToStaticMarkup` + mocked `maplibre-gl` pattern (see `DashboardCard.test.tsx`) and `jsdom` env (already configured in `web/vite.config.ts`).
- Missing-data assertion: the styled empty state must render a distinct phrase such as "coming soon" / "no data yet" for Classification and Dominant Fault System; update the existing `toMatch(/Not available/i)` assertion to the new text.

- [ ] **Step 1: Update `DashboardCard.test.tsx` for the new empty-state text**
- [ ] **Step 2: Update `DashboardStates.test.tsx` for skeleton + error markup**
- [ ] **Step 3: Update `MapView.test.tsx` (and `RiskProfile.test.tsx` if classes changed)**
- [ ] **Step 4: Source audit — grep `web/src` for raw hex (`#dc2626`, `#e5e9ec`, `#5a716c`) and bare "Not available" in active components; confirm none remain**
- [ ] **Step 5: Run `npm test` and `npm run build` from `web/`; run `python scripts\verify_structure.py` and `git diff --check` from root**
- [ ] **Step 6: Commit** `test(web): update tests for elevated ui and empty states`

---

### Task 6: Documentation refresh

**Files:**
- Rewrite: `web/WEB_STRUCTURE.md` (actual structure, not the legacy layout)
- Create: `web/DESIGN_NOTES.md` (tokens + CSS Modules reference, the mobile-adoptable foundation)
- Modify: `CODING_STANDARDS.md` (web styling section → reference token system + CSS Modules convention)

**Interfaces (content):**
- `WEB_STRUCTURE.md` describes: `App.tsx` hero/dashboard (useState) toggle + placeholder pages; `main.tsx` root/bootstrap + style imports; `pages/` (`Hero`, `Dashboard`, `About`, `HistoricalBrowser`); `components/layout/TopNav`; `components/dashboard/` (`DashboardSidebar`, `DashboardMapArea`); `components/map/MapView` (live MapLibre, note marker styling moved to CSS module); `components/common/` (`SectionHeader`, `RiskMeter`, optional `ComingSoon`/`Skeleton`); `hooks/` (`useEvents`, `useEventSummary`, `useRiskProfiles`, optional `useRevealOnScroll`); `api/client.ts`; `types/hazard.ts`; `styles/` (tokens/base/utilities, CSS Modules per component). Remove all stale placeholder/legacy descriptions.
- `DESIGN_NOTES.md` documents: brand primitives (cream ramp, ink, accents), semantic tokens (surfaces, text, borders, shadows, radius, spacing, type, motion, z-index), the CSS Modules convention (`*.module.css` per component), breakpoints, and the `prefers-reduced-motion` approach. This is the hand-off for the mobile app.
- `CODING_STANDARDS.md`: in the web standards section, state that component styles live in co-located CSS Modules and reference the shared tokens in `web/src/styles/tokens.css`; point to `web/DESIGN_NOTES.md`.

- [ ] **Step 1: Rewrite `web/WEB_STRUCTURE.md` to the actual structure**
- [ ] **Step 2: Create `web/DESIGN_NOTES.md`**
- [ ] **Step 3: Update `CODING_STANDARDS.md` web styling section**
- [ ] **Step 4: Run `python scripts\verify_structure.py` and `git diff --check` from root**
- [ ] **Step 5: Commit** `docs: refresh web structure and add design notes`

---

## Notes for the executor

- **Ordering:** Tasks 1→2→3→4 must run in sequence (each builds on the styling layer or cleanup of the prior). Task 5 (tests) can run after each of Tasks 1–4 per commit to keep things green, but the full suite must pass at the end. Task 6 is last and depends on all.
- **Environment:** No docker/DB/credentials needed — this is a pure frontend + docs change. `maplibre-gl` is mocked in tests.
- **Risk components:** `RiskProfileExplorer`/`RiskProfileCard`/`RegionLookup` are not rendered in the active flow; leave them untouched this pass (their legacy classes are not used by active components after Task 3).
- **Do not add a router.** The nav stays a `useState` toggle. If extending the union to render placeholder pages, keep prop types on `TopNav` backward-compatible or update its `onNavigate` signature accordingly and update any test referencing it.
- **Reviewer double-check:** confirm (a) no new deps, (b) `index.css` + `revert` hack gone, (c) no raw hex/bare "Not available" in active `.tsx`, (d) `prefers-reduced-motion` honored, (e) `WEB_STRUCTURE.md` no longer documents the legacy `Header`/`Sidebar`/`EventList` layout or a placeholder map.
