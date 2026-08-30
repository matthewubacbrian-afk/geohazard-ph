# GeoHazard PH — Web UI Elevation (Design)

**Date:** 2026-08-31

## Problem

The GeoHazard PH web app has a genuinely distinctive visual identity (warm cream surfaces,
near-black mono-uppercase technical labels, JetBrains Mono + Inter, Material Symbols, red risk
accent) but it is implemented as a **functional prototype** with classic maturity tells:

- **One monolithic 1269-line `web/src/styles/index.css`** with a `revert` hack at the end
  (`display: revert` on `.header`, `.workspace`, `.sidebar`, `.panel`, `.filter-bar`,
  `.toggle-row`) that exists only to undo styles for dead, unwired components.
- **Flat visual rhythm and weak interaction states** — sections read the same, there is no
  elevation hierarchy, no purposeful motion, most hovers are bare color changes, and buttons
  lack tactile `:active` feedback.
- **Dashboard overlay collision** — the floating stats card, events-status banner, legend, and
  map controls all float in translucent panels with an undocumented z-index model, and loading
  is a bare "Loading events…" string instead of a skeleton.
- **No shared token discipline** — several raw hexes are hardcoded in components/MapView
  (`#dc2626`, `#e5e9ec`, `#5a716c`) and breakpoints are magic numbers, so the design system is
  not a thing a second developer (or the React Native app) can adopt.
- **Dead legacy components and stale docs.** `Header`, `Sidebar`, `EventList`,
  `EventFilterBar`, `EventDetailPanel`, `LayerControls`, `VolcanoAlertCard`, `FaultLineLayer`,
  and stub pages `HistoricalBrowser`/`About` are not rendered by the active `App` flow but still
  ship. `web/WEB_STRUCTURE.md` documents a completely different (legacy) layout and describes a
  live map as a placeholder.

The user-facing goal is to **elevate the existing identity rather than rebrand it**, and to
establish a **design-token + CSS Modules foundation** that the React Native mobile app can adopt
later.

## Goals

1. **Preserve and elevate the existing identity** — keep the warm cream palette, mono-uppercase
   label motif, Inter/JetBrains Mono/Material Symbols, and red risk accent; do not rebrand.
2. **Introduce a design-token system** as a single source of truth: primitive + semantic CSS
   custom properties for color, type scale, spacing, radius, shadows, breakpoints, and motion.
   Portable (documented) so the mobile app can mirror it. **Verifiable:** `tokens.css` exists,
   all component modules reference tokens (no new raw hex in components), documented in a
   design-notes doc.
3. **Convert to CSS Modules** per component (`Name.module.css`), scoped and co-located. Delete
   the monolithic `index.css` (migrating kept rules) and remove the `revert` hack.
4. **Elevate hierarchy, spacing, and interaction states** — consistent type/spacing/radius
   scale, depth-aware tinted shadows, tactile `:active` press on interactive elements, focus
   rings, and polished loading/empty/error states. **Verifiable:** run `npm test` + `npm run
   build`.
5. **Add purposeful motion** — scroll reveals via IntersectionObserver and smooth CSS
   transitions, all gated behind `prefers-reduced-motion`. **Verifiable:** revealed elements
   have `.reveal`-class pattern; `prefers-reduced-motion: reduce` disables transitions.
6. **Remove dead legacy code** (unused components + the `revert` hack) and replace the stub
   pages (`HistoricalBrowser`, `About`) with polished "coming soon" placeholder sections. Keep
   the `useState` view toggle; do **not** add routing.
7. **Gracefully gate missing data** — replace bare "Not available" text with clear, styled
   empty/`coming soon` states for surfaces whose backend data does not exist yet (risk
   classification, dominant fault system, volcano alerts, fault layers). **Verifiable:** no raw
   "Not available" strings remain in the active UI after the redesign (verified by test/source
   audit).
8. **Refresh documentation** — rewrite `web/WEB_STRUCTURE.md` to match the actual structure, add
   a design-notes doc (`web/DESIGN_NOTES.md`), and update `CODING_STANDARDS.md` web styling
   guidance to reference the token + CSS Modules convention.

## Non-goals

- **No rebrand**: palette, typefaces, and mono-label motif stay. Not changing to a dark theme or
  a different visual language.
- **No router**: navigation stays a `useState` toggle; no React Router dependency added.
- **No new backend/ML data integration** for classification, dominant fault, or volcano/fault
  layers — missing data is presented as styled empty states, not fabricated.
- **No mobile (React Native) implementation**: only the web app is changed. The token/design-notes
  artifact is the hand-off for a future mobile styling pass.
- **No dependency additions** for styling or animation (no Tailwind adoption for this pass, no
  framer-motion/Motion). Styling stays CSS custom properties + CSS Modules; motion is CSS +
  IntersectionObserver.

## Context And Constraints

- **Current identity** lives implicitly in `web/src/styles/index.css` (design tokens in `:root`).
  These become the brand primitives; they are not to be discarded.
- **Tailwind is configured but unused** — `tailwind.config.ts` exists but styling is entirely
  hand-written CSS. Keeping pure CSS avoids a migration risk this pass; the choice is documented.
- **No router and no animation library** presently in `web/package.json`. Dependencies are
  `@tanstack/react-query`, `maplibre-gl`, `react`, `react-dom`; dev deps are Vitest +
  Testing Library + jsdom.
- **CODING_STANDARDS.md** (root) mandates: `PascalCase.tsx` component files, explicit props typing,
  React components under `web/src/components`, hooks under `web/src/hooks`, API under
  `web/src/api`, domain types under `web/src/types`. Web verification: `npm test` + `npm run
  build` from `web/`.
- **docs/testing-standards.md**: web tests render components (existing suite uses
  `renderToStaticMarkup` with mocked `maplibre-gl`) and cover user-visible behavior.
- **docs/glossary.md**: domain terms are fixed; UI renames of domain concepts must keep glossary
  terms (e.g. "risk label", "dominant fault system", "hazard event").
- **Architecture**: `App.tsx` holds `useState<"hero" | "dashboard">`; `Hero` renders
  `TopNav` + hero + process grid + about + footer; `Dashboard` renders `TopNav` +
  `DashboardSidebar` + `DashboardMapArea` (which wraps the live `MapView` map and floating
  overlays). `RiskProfileExplorer`, `RiskProfileCard`, `RegionLookup` exist but the route shell
  currently only surfaces Hero and Dashboard.

## Alternatives Considered

1. **Adopt Tailwind utilities (config already present).** Faster to write terse utilities and
   standardizes a utility vocabulary, but it is a broad migration with churn, and the project has
   zero existing Tailwind usage to conform to. Rejected for this pass in favor of keeping the
   project's pure-CSS identity while adding a token layer.
2. **Single tokenized CSS file only (no CSS Modules).** Lowest churn, but the 1269-line file
   remains a bear and provides no per-component scoping/encapsulation. Rejected: the user
   selected CSS Modules for maintainability and isolation.
3. **Add framer-motion / Motion for animation.** More expressive reveals and shared-element
   transitions, but adds a dependency and bundle weight for a data/trust product where restrained
   motion is more appropriate. Rejected: CSS transitions + IntersectionObserver cover the
   requirement while honoring `prefers-reduced-motion`.
4. **Delete nav stubs entirely.** Simplest, but removes planned surfaces readers expect from the
   nav. Rejected in favor of polished "coming soon" placeholder sections (user-selected).

## Design

### Architecture and data flow

The change is **presentational and structural**, not data-flow. Data flow (React Query →
`useEvents`/`useEventSummary` → components → map) is unchanged. The redesign touches the styling
layer and component structure:

```
web/src/styles/
  tokens.css        # primitive + semantic custom properties (the design system)
  base.css          # reset, body/typography, base focus styling
  utilities.css     # .sr-only, focus-ring, motion-reveal helpers, shared classes
web/src/components/  (each active component co-locates Name.module.css)
  layout/TopNav.tsx            + TopNav.module.css
  pages? -> Hero/Dashboard are pages, co-locating .module.css next to them
```

CSS Modules are imported per component; `tokens.css`/`base.css`/`utilities.css` are imported at
the app root (`main.tsx`) so custom properties and base styles are global, while class-scoped
component rules live in each module.

### Components

- **`tokens.css`** (new) — the single source of truth. Primitive tokens (color ramp, type scale,
  spacing, radius, shadow, breakpoint, motion) plus semantic tokens (surface layers, text
  emphasis, accent/risk colors, borders, shadows, radii, durations/easings).
- **`base.css`** (new) — box-sizing, body background/color/font, typography defaults, link/button
  base, `:focus-visible` ring, font smoothing, reduced-motion entry point.
- **`utilities.css`** (new) — `.sr-only`, `.focus-ring`, reveal/motion helpers.
- **`Name.module.css`** per active component — scoped class rules, consuming semantic tokens.
- **Unchanged logic** in `TopNav`, `Hero`, `Dashboard`, `DashboardSidebar`, `DashboardMapArea`,
  `MapView`, `RiskMeter`, `SectionHeader`, `RiskProfileExplorer`, `RiskProfileCard`,
  `RegionLookup` — only styling class names and markup for empty/loading states change where
  needed.
- **New small presentational sub-components** where reuse justifies them (e.g. a `<Skeleton>`
  block and a `<ComingSoon>` placeholder), each with its own module. Marked optional by the
  implementation plan; add only if it reduces duplication.

### Interfaces

- **`tokens.css`** exports CSS custom properties (scope `:root`), e.g.:
  - Color: `--color-cream-*` ramp, `--color-ink`, `--color-muted-*`, `--color-accent`,
    `--color-risk-high/medium/low`.
  - Semantic: `--surface`, `--surface-raised`, `--surface-overlay`, `--text`,
    `--text-muted`, `--text-faint`, `--border`, `--border-strong`, `--accent`,
    `--risk-high/medium/low`, `--shadow-card`, `--shadow-overlay`, `--radius-sm/md/panel`,
    `--ease-out`, `--dur-fast/base`, `--z-map-overlay`, `--z-topbar`, and a documented
    `--z-*` scale.
  - Exactly named in `web/DESIGN_NOTES.md` so consumers (and the future mobile pass) do not
    guess.
- **`base.css` / `utilities.css`** — no JS exports; imported for global side effects.
- **Components** — import their `*.module.css` and use `styles.<className>`; no changes to
  component prop signatures (public TS interfaces stay stable). Only class/markup changes.
- **`useRevealOnScroll`** (optional) — a tiny hook returning a ref + visible boolean for
  IntersectionObserver reveals. If added, no external dependency.
- **Placeholder pages** — `HistoricalBrowser` and `About` convert to shared `<ComingSoon>`-style
  sections rendered in the `useState` view switch.

### Configuration

- No new env vars, no new settings fields, no backend config changes.
- No new npm dependencies. (Optionally document that Tailwind remains unused.)

### Error handling

- Existing loading/error paths stay. `DashboardMapArea`'s error banner keeps its retry button
  but is restyled via tokens.
- Missing-data surfaces (risk classification, dominant fault system, volcano alerts, fault
  layers) render a styled empty/"coming soon" state instead of bare "Not available". This is UI
  presentation only; no error path change.
- All interactive states (focus, hover, active, disabled) visible and WCAG-contrast-correct per
  `docs/error-handling-and-logging.md`/CODING_STANDARDS accessibility expectations.

### Data considerations

- No schema, migration, coordinate, datetime, or dedup changes. Purely presentational.
- UI wording for domain concepts must match `docs/glossary.md` (e.g. "risk label",
  "dominant fault system", "hazard event"). Avoid inventing new names.

## Rollout

1. Phase 0 — write this spec + the implementation plan under `docs/superpowers/` (this commit).
2. Phase 1 — create `tokens.css`, `base.css`, `utilities.css`; set up module imports at the root.
3. Phase 2 — migrate each active component to its own `.module.css`, refactoring type/spacing/
   radius/shadow/token usage.
4. Phase 3 — remove dead components + the `revert` hack; convert stub pages to polished
   placeholders.
5. Phase 4 — add IntersectionObserver reveals + micro-interactions (gated by
   `prefers-reduced-motion`).
6. Phase 5 — update/extend web tests; run `npm test` + `npm run build` from `web/`.
7. Phase 6 — refresh docs (`WEB_STRUCTURE.md`, new `DESIGN_NOTES.md`, `CODING_STANDARDS.md`).

All on the current `main` via focused feature commits using Conventional Commits. No feature
flagging required (no behaviour change to data flow).

## Files

```
docs/superpowers/specs/2026-08-31-web-ui-elevation-design.md   (this spec)
docs/superpowers/plans/2026-08-31-web-ui-elevation.md          (implementation plan)

web/src/styles/
  tokens.css                 (new)  design-token system
  base.css                   (new)  reset, typography, base focus
  utilities.css              (new)  sr-only, focus-ring, motion helpers
  index.css                  (delete/migrate)  1269-line monolithic file + revert hack

web/src/components/
  layout/TopNav.tsx          (modify markup/classes)  + add TopNav.module.css
  map/MapView.tsx            (modify: token-based marker styling, sizing/pulse)
  dashboard/DashboardSidebar.tsx + DashboardSidebar.module.css
  dashboard/DashboardMapArea.tsx + DashboardMapArea.module.css
  common/RiskMeter.tsx + RiskMeter.module.css
  common/SectionHeader.tsx + SectionHeader.module.css

web/src/pages/
  Hero.tsx  + Hero.module.css      (type/spacing/motion refinement)
  Dashboard.tsx + Dashboard.module.css
  HistoricalBrowser.tsx   (convert to placeholder using shared ComingSoon)
  About.tsx              (convert to placeholder using shared ComingSoon)

web/src/components/  (candidate new presentational modules, added only if they
                      reduce duplication:)
  common/Skeleton.tsx / common/Skeleton.module.css
  common/ComingSoon.tsx / common/ComingSoon.module.css

web/src/hooks/useRevealOnScroll.ts  (optional IntersectionObserver reveal hook)

web/tests/
  DashboardCard.test.tsx     (modify: adjust for changed markup/classes/empty-state)
  DashboardStates.test.tsx   (modify: adjust for skeleton/empty state markup)
  MapView.test.tsx           (modify if marker markup changes)
  RiskProfile.test.tsx       (modify if risk components change)

web/
  WEB_STRUCTURE.md           (rewrite to actual structure)
  DESIGN_NOTES.md            (new: design tokens + CSS Modules reference)
  main.tsx                    (modify: import tokens.css/base.css/utilities.css)

CODING_STANDARDS.md           (modify: web styling section -> tokens + CSS Modules)

(delete, unused/not rendered by active flow:)
  web/src/components/layout/Header.tsx
  web/src/components/layout/Sidebar.tsx
  web/src/components/events/EventList.tsx
  web/src/components/events/EventFilterBar.tsx
  web/src/components/events/EventDetailPanel.tsx
  web/src/components/map/LayerControls.tsx
  web/src/components/volcano/VolcanoAlertCard.tsx
  web/src/components/map/FaultLineLayer.tsx
```

## Testing Strategy

Per `docs/testing-standards.md` and CODING_STANDARDS, from `web/` (Vitest, jsdom-configured):

- **`DashboardCard.test.tsx`** — assert the floating card still renders real avg magnitude and
  event frequency from the summary, and that missing-data fields render the styled
  empty/"coming soon" state (not the literal "Not available" string).
- **`DashboardStates.test.tsx`** — assert the loading skeleton and retry-able error state
  markup after the redesign.
- **`MapView.test.tsx`** — assert markers still render from fixture events (if marker markup
  changes).
- **`RiskProfile.test.tsx`** — assert risk components render (if their classes/markup change).
- **Application audit** — grep the active components for raw `#dc2626`/`#e5e9ec`/`#5a716c` and
  bare "Not available" strings; require tokens + styled empty states instead. (Lightweight,
  done via source grep during Phase 3/5.)
- **Verification commands** (from `web/`): `npm test`, `npm run build`; from repo root:
  `python scripts\verify_structure.py`, `git diff --check`.

## Acceptance Criteria

- [ ] `web/src/styles/tokens.css`, `base.css`, `utilities.css` exist; `main.tsx` imports them.
- [ ] Every active component has a co-located `*.module.css`; the monolithic `index.css` and its
      `revert` hack are removed.
- [ ] No raw hex colors remain in web component `.tsx`/`.ts` source (all via tokens/modules); no
      bare "Not available" strings remain in the active UI.
- [ ] Dead components (`Header`, `Sidebar`, `EventList`, `EventFilterBar`, `EventDetailPanel`,
      `LayerControls`, `VolcanoAlertCard`, `FaultLineLayer`) are deleted and nothing imports them.
- [ ] `HistoricalBrowser` and `About` render polished placeholder sections (not bare `<main>`
      stubs), reachable from the nav via the existing `useState` toggle (no router added).
- [ ] Motion reveals/micro-interactions are present and disabled under
      `@media (prefers-reduced-motion: reduce)`.
- [ ] `npm test` and `npm run build` pass from `web/`; `python scripts\verify_structure.py` and
      `git diff --check` pass from root.
- [ ] `web/WEB_STRUCTURE.md` is rewritten to the actual structure; `web/DESIGN_NOTES.md` documents
      the token system + CSS Modules convention; `CODING_STANDARDS.md` web section references them.
- [ ] No new npm dependencies added.

## Out Of Scope (backlog)

- **Tailwind adoption** — config remains but stays unused this pass; a later pass may migrate.
- **Motion/framer-motion** — deferred; CSS + IntersectionObserver only.
- **React Router / multi-page routing** — the `useState` toggle stays.
- **Mobile (React Native) styling pass** — the token/design-notes artifact is the hand-off.
- **Real data for classification / dominant fault / volcano / fault layers** — Epic 2/3
  follow-ups; this pass only styles their empty states.

---

## Spec self-review

- No `TBD`/`TODO`/unfinished sections remain.
- No section contradicts another: "no new deps", "no Tailwind", "no router", "no mobile" are
  consistent with the component/rollout/files/testing sections.
- Every goal maps to an acceptance criterion (goals 1–8 -> criteria list).
- Interfaces are concrete enough to implement without guessing (token names + component/file
  list).
- Scope fits a single implementation plan (presentational + structural + docs; no backend/ML).

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-08-31-web-ui-elevation.md`
- Terminology: `docs/glossary.md`
- Standards: `CODING_STANDARDS.md`, `docs/testing-standards.md`
