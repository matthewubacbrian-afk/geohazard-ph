# GeoHazard PH Web Design Notes

These notes document the web presentation system established by the October 2026 interface refresh. The work changes the React web presentation only; API contracts, hooks, shared data types, and risk calculations remain the source of behavior and values.

## Direction

The interface uses a quiet field-station character: basalt ink, pumice surfaces, terracotta emphasis, ochre for elevated risk, and mineral green for low-risk or connected states. A restrained serif display face adds an editorial hierarchy while sans-serif text stays readable and mono is reserved for technical labels and numerical values. Panels use clear edges and mostly flat surfaces; color reinforces labels rather than carrying meaning alone.

## Tokens and contrast

`src/styles/tokens.css` is the source of palette, semantic color, typography, spacing, radius, motion, z-index, and breakpoint values. Components should consume semantic tokens rather than add brand colors locally. Current text foreground contrast was checked against the light surface, raised, and container backgrounds. The faint text token is reserved for secondary text that still meets AA on its intended light surfaces; use the stronger muted token for normal body content.

| Purpose | Token | Value |
| --- | --- | --- |
| Base / raised / container | `--surface` / `--surface-raised` / `--surface-container` | `#F3F0E9` / `#FAF8F3` / `#E8E4DA` |
| Main / muted / faint text | `--text` / `--text-muted` / `--text-faint` | `#292824` / `#57554F` / `#68665F` |
| Border / accent | `--outline` / `--accent` | `#645F55` / `#9B3F2E` |
| Very high / elevated / low risk | `--risk-very-high` / `--risk-medium` / `--risk-low` | `#792D25` / `#805A0B` / `#49655F` |
| Focus | `--focus-ring` | `#74402E` |

## Typography and layout

- Inter is the body face; the system serif stack in `--font-display` is used for page and panel headings; JetBrains Mono is used for compact technical labels and tabular values.
- Use the shared 4px spacing scale, small control radius, and clear panel borders. Shadows are limited to map overlays that sit above map tiles.
- Desktop dashboard is map-led with sidebar and activity panels. Tablet and mobile reflow all existing controls and activity into reachable stacked layouts; do not hide data or controls. The shared breakpoints are `--bp-md: 900px` and `--bp-sm: 640px`.
- Informational content uses a constrained reading width, responsive single-column layout, and visible source attribution. Historical browsing remains explicitly planned and has no fake controls.

## Data and accessibility

- Live values, loading, error, empty, retry, stale-cache, and source states continue to come from existing hooks and components. Never fill a missing metric with a sample value.
- Risk profiles are descriptive statistics based on historical records, not predictions, forecasts, or official warnings. Volcano remote reference imagery and local vector zones remain distinct.
- Labels and text accompany risk colors. Interactive controls use visible focus, touch-sized targets, and keyboard-operable native buttons/links. Reduced-motion preferences are honored for decorative transitions and reveals.
- Keep basemap providers and attribution intact; verify overlays against streets, satellite, hybrid, and terrain before changing map paint or controls.
