# GeoHazard PH — Web Application Structure

This document explains the structure and components of the GeoHazard PH web app, a React-based geologic hazard monitoring platform for the Philippines. It reflects the current (elevated-identity) styling foundation: **CSS Modules per component** on top of a small set of global stylesheets driven by design tokens.

For the design rationale, tokens, and motion conventions, see [DESIGN_NOTES.md](./DESIGN_NOTES.md).

---

## Folder Structure Overview

```
web/
├── src/
│   ├── App.tsx                  # View switch (hero / dashboard / placeholders)
│   ├── main.tsx                 # React DOM bootstrap + global style imports
│   ├── vite-env.d.ts            # Vite environment types
│   ├── api/                     # API client layer
│   ├── components/
│   │   ├── common/              # Presentational primitives (shared)
│   │   ├── dashboard/           # Dashboard page interior
│   │   ├── layout/              # TopNav (the only surviving layout component)
│   │   ├── map/                 # MapLibre integration
│   │   └── risk/                # Risk profile UI (legacy / out of active flow)
│   ├── hooks/                   # Custom React hooks
│   ├── pages/                   # Page-level components
│   ├── styles/                  # Global stylesheets (tokens, base, utilities)
│   └── types/                   # TypeScript type definitions
├── tests/                       # Vitest test files
├── package.json                 # Dependencies and scripts
├── tsconfig.json                # TypeScript configuration
├── vite.config.ts               # Vite bundler configuration
└── index.html                   # HTML entry point
```

---

## Application Architecture

### Entry Point: `src/App.tsx`

`App` keeps a single piece of UI state — the current `View` — and renders the matching page. There is deliberately **no router**: the app switches views through a `useState<View>` toggle, keeping the surface small while the product scope is still being defined.

```tsx
export type View = "hero" | "dashboard" | "about" | "data-sources" | "historical";
```

- `hero` → `Hero` (marketing landing + methodology)
- `dashboard` → `Dashboard` (interactive map + controls)
- `about` / `data-sources` → styled `ComingSoon` placeholder pages
- `historical` → styled `ComingSoon` placeholder page (reserved, not yet reachable from nav)

View navigation is threaded through an `onNavigate(nextView)` callback so presentational pages stay unaware of routing concerns.

### Bootstrap: `src/main.tsx`

Mounts React to `#root`, sets up the TanStack Query `QueryClient`, and imports global styles in a deliberate cascade:

```tsx
import './styles/tokens.css';     // design tokens (primitives + semantic)
import './styles/base.css';       // reset, typography, reduced-motion
import './styles/utilities.css';  // shared a11y + button helpers
```

Every other style lives in a colocated `*.module.css` next to its component.

---

## Styling Model

- **Design tokens** are defined once in `src/styles/tokens.css` as CSS custom properties on `:root`.
- **Global stylesheets** are intentionally thin: reset/base, typography, `prefers-reduced-motion`, and a handful of global utilities (`.sr-only`, `.primary-button`, `.secondary-button`).
- **Component styles** live in `*.module.css` files, scoped by Vite's CSS Modules. Components reference them via `import styles from './X.module.css'`.
- **No Tailwind.** The old `tailwind.config.ts` was removed as dead legacy code.

See `DESIGN_NOTES.md` for the token naming convention and design decisions.

---

## Pages

### `src/pages/Hero.tsx`

The marketing landing page. Sections: hero headline + CTAs, "Methodology & Pipeline" (4-step process grid), "About" panels, and a footer. Uses `Reveal` for scroll-in motion on the headline/subtitle/CTAs and each process step.

### `src/pages/Dashboard.tsx`

The interactive risk dashboard. Calls `useEvents()` for live hazard data, then composes `DashboardSidebar` (controls) and `DashboardMapArea` (map + overlays) inside a `TopNav`-scaffolded workspace.

### `src/pages/About.tsx`, `src/pages/DataSources.tsx`, `src/pages/HistoricalBrowser.tsx`

Styled placeholder pages built from the shared `ComingSoon` component. They are reachable from the nav (`About`, `Data Sources`) or reserved for future work (`Historical`). They present real copy and data-source credits rather than bare stubs.

### `src/pages/RiskProfileExplorer.tsx`

**Out of the active flow.** Legacy ML risk-profile exploration surface (plus `components/risk/RiskProfileCard.tsx` and `RegionLookup.tsx`). Not rendered by `App`; retained for a future risk surface.

---

## Components

```
components/
├── common/
│   ├── RiskMeter / RiskMeter.module.css       # animated risk label meter
│   ├── SectionHeader / SectionHeader.module.css# section kicker + title
│   ├── Skeleton / Skeleton.module.css         # loading shimmer placeholder
│   ├── ComingSoon / ComingSoon.module.css     # polished placeholder page body
│   └── Reveal/Reveal.tsx + Reveal.module.css  # IntersectionObserver scroll reveal
├── dashboard/
│   ├── DashboardSidebar.tsx / .module.css     # controls panel
│   └── DashboardMapArea.tsx / .module.css     # map with overlays + loading/empty states
├── layout/
│   └── TopNav.tsx / TopNav.module.css         # primary navigation (hero/dashboard themes)
├── map/
│   ├── MapView.tsx / MapView.module.css       # live MapLibre map
│   └── EventMarker.tsx                        # non-MapLibre legacy marker (reference)
└── risk/                                      # legacy, out of active flow
    ├── RiskProfileCard.tsx
    └── RegionLookup.tsx
```

### Custom Hooks (`src/hooks/`)

- **`useEvents.ts`** — TanStack Query fetch of hazard events (`fetchEvents`).
- **`useEventSummary.ts`** — derived summary counts per hazard type.
- **`useFaultLines.ts`** — legacy fault-line fetch (not in active flow).
- **`useRealtimeAlerts.ts`** — realtime alert subscription (not in active flow).
- **`useRiskProfiles.ts`** — ML risk-profile fetch (used by the out-of-flow `RiskProfileExplorer`).
- **`useRevealOnScroll.ts`** — IntersectionObserver hook that toggles visibility; respects `prefers-reduced-motion`.

### Types

- **`src/types/hazard.ts`** — `HazardEvent`, `RiskProfile`, and related domain types.
- **`src/types/views.ts`** — the `View` union used by the `App` switch and `TopNav`.

---

## API Client (`src/api/client.ts`)

Central API client. Base URL from `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api/v1`). Exposes `fetchEvents()` and the risk-profile functions (`fetchRiskProfiles`, `fetchRiskProfile`) used by the out-of-flow risk surface.

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **React** | UI framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Build tool and dev server |
| **CSS Modules** | Scoped component styling |
| **React Query (TanStack)** | Server state management, caching, sync |
| **MapLibre GL** | Interactive maps |
| **Vitest + Testing Library** | Unit testing |

---

## Running the Web App

```bash
cd web
npm run dev        # dev server at http://localhost:5173
npm run build      # type-check (tsc) + production build to dist/
npm test           # Vitest suite
```

---

## Data Flow

```
API Backend (FastAPI)
        ↓
src/api/client.ts (HTTP calls)
        ↓
src/hooks/ (useEvents, useRiskProfiles, etc.)
        ↓
React Query QueryClient (caching, sync)
        ↓
Pages/Components (consume hooks)
        ↓
UI rendered (Dashboard, Hero, placeholders)
```

---

## Notes

- **Styling:** Use CSS Modules for all component styles; tokens from `tokens.css`. See `DESIGN_NOTES.md`.
- **Navigation:** No router — views switch via `useState<View>` in `App`. Keep the `View` union and `TopNav`'s label→view mapping in sync when adding views.
- **Environment config:** Set `VITE_API_BASE_URL` in `.env` to point the API client at the backend.
- **Accessibility:** Components use semantic HTML and ARIA; focus-visible and `prefers-reduced-motion` are handled globally.
