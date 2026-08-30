# GeoHazard PH — Design Notes

This file records the design direction for the GeoHazard PH **web** app and serves as the hand-off foundation for the future React Native app. It documents the identity, tokens, type/motion conventions, and layout principles so subsequent work stays coherent.

> Scope: web UI, as of the 2026-08-31 "web UI elevation" effort. Mobile/infra/backend are out of scope here — the token layer is the shared contract.

---

## Design Direction: Elevate, Don't Rebrand

The redesign **kept the established identity** and raised its craft bar rather than replacing it:

- **Warm cream** surfaces (`--cream-*`) — soft, editorial, distinct from generic white SaaS.
- **JetBrains Mono, uppercase, letter-spaced** technical labels — the "instruments of a hazard terminal" voice.
- **Inter** for body/display type — quiet, legible, human.
- **Material Symbols** for iconography — crisp and consistent, same family as the original.
- **Brand red** (`--accent`) reserved for the most important signal: high risk and primary action.

The hierarchy leads with the red as a *risk signal*, not a decorative splash, so it always means something.

---

## Tokens (`src/styles/tokens.css`)

Single source of truth. Two layers:

1. **Primitives** — the raw palette and scales (`--cream-*`, `--ink*`, `--outline*`, `--accent`, type ramp, spacing, radius, motion, z-index, breakpoints).
2. **Semantic** — what components actually consume (`--surface*`, `--text*`, `--border*`, `--shadow-*`, `--risk-*`), mapping primitives to meaning.

### Conventions

- Components **never** hard-code hex values; they consume semantic tokens only. (Two exceptions live inside `MapView`'s runtime resolution of `--accent`/`--white` for MapLibre paint, and a few literal tile-backdrop tints in module CSS that are map-tile-adjacent, not brand.)
- Token names use the `--kebab-case` custom-property style.
- Adding a color means adding a primitive *and* (when it carries meaning) a semantic alias.

### Palette

| Role | Token | Value |
|------|-------|-------|
| App background | `--surface` | cream |
| Raised surface | `--surface-raised` | lighter cream |
| Primary text | `--text` | ink near-black |
| Muted text | `--text-muted` | soft gray |
| Faint text | `--text-faint` | light gray |
| Brand / high risk | `--accent` / `--risk-high` | red |
| Medium risk | `--risk-medium` | amber |
| Low risk | `--risk-low` | teal |

---

## Typography

- **Inter** — body and display copy. Ramp: `--text-2xs` … `--text-3xl`.
- **JetBrains Mono** — technical labels, buttons, kickers, badges. Uppercase + `~1.2px` letter-spacing + weight 700 (`var(--font-mono)`), see the shared `.mono-label` utility treatment.
- **Material Symbols Outlined** — icon glyphs (`--font-icon`).

### Voice

- Kickers/section headers: small mono uppercase label + large clean heading.
- Body copy: comfortable `--text-base`/`16px` with generous line-height and constrained measure.
- Avoid long wraps on the hero title; let the two-line "kicker + statement" pattern breathe.

---

## Motion

No animation library — **CSS transitions + an IntersectionObserver reveal**.

### Scroll reveal (`common/Reveal`)

- Reveals content once it enters the viewport (`useRevealOnScroll`).
- Entry: `opacity 0 → 1` + `translateY(16px) → 0`, `0.6s cubic-bezier(0.22, 1, 0.36, 1)`.
- Stagger children with incremental `delayMs` (hero: 0/100/200ms; process steps: `index * 100ms`).
- **Reduced motion:** the hook reveals instantly and the module disables the transition under `prefers-reduced-motion`.

### Micro-interactions

- Buttons: `transform: translateY(1px)` on `:active` for tactile press.
- Cards (e.g. process cards): subtle `translateY(-2px)` + background lift on hover.

### Motion tokens

- `--dur-fast: 0.15s`, `--dur-base: 0.25s`, `--dur-slow: 0.4s`
- `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`, `--ease-default: cubic-bezier(0.25, 1, 0.5, 1)`

---

## Layout & Radius

- **Radius:** `--radius-sm` (4px) for small controls, `--radius-md` (8px) for cards, `--radius-panel` (16px) for panel surfaces, `--radius-pill` for pills/badges.
- **Spacing:** 4px scale (`--space-1` … `--space-24`), typically paired with a 8px grid in components.
- **Z-index:** `--z-status` (3) in-map banners, `--z-map-overlay` (2) in-map cards/legend/controls, `--z-topbar` (50) sticky nav.
- **Shadows:** ink-tinted, low-opacity (`--shadow-card`, `--shadow-overlay`, `--shadow-control`) to stay warm and quiet rather than hard/black.

---

## Graceful Data States

- Loading surfaces use the shared `Skeleton` shimmer.
- Missing/unavailable features render polished "Coming soon" placeholders (see `ComingSoon`), never a bare "Not available" string or empty box.
- Error states offer a retry affordance (see `DashboardMapArea` status banner).

---

## A11y & Reduce Motion

- `:focus-visible` ring defined in `base.css`.
- `.sr-only` utility for screen-reader-only content.
- All motion is disabled (or instant-revealed) under `prefers-reduced-motion`.

---

## Moving to React Native

- Reuse this token vocabulary (surfaces, text, risk levels, radii, spacing) 1:1 where possible.
- Motion tokens map to Reanimated's `withTiming` durations/curves; port the `--ease-out` curve as `cubicBezier(0.16, 1, 0.3, 1)`.
- The upward-lift micro-interactions and stepped reveal translate well to RN with `Reanimated` + `entering`/`layout` animations.
