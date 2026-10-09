# GeoHazard PH Web Design Notes

The full visual and interaction contract is in [REDESIGN_UI.md](REDESIGN_UI.md).
These notes summarize the rules for contributors; `src/styles/tokens.css` remains
the single source of truth for web colors, type, spacing, shape, focus, and motion.

## Direction

Build a map-led geohazard instrument with basalt and ash text, pumice and warm-sand
surfaces, clay actions, and restrained ochre. Use a four-step labeled risk scale
(Low, Moderate, High, Very High) and a separate neutral magnitude-marker scale.
Every category has a text label and non-color cue. Avoid gradients, neon, pure-black
dark themes, decorative cards, and controls that are hidden at smaller widths.

## Type and assets

- IBM Plex Serif for display headings, IBM Plex Sans for interface and body copy,
  and IBM Plex Mono with tabular numerals for magnitudes, depth, coordinates, and time.
- Self-host only the used weights from Fontsource packages for IBM Plex Sans, Serif,
  and Mono. The @fontsource/ibm-plex-sans, @fontsource/ibm-plex-serif, and
  @fontsource/ibm-plex-mono packages use the SIL Open Font License 1.1. Their
  package license files remain included with the installed dependencies. IBM Plex
  source: [IBM/plex](https://github.com/IBM/plex). Do not load fonts from a
  third-party runtime CDN.
- Use consistent SVG icon components (or inline SVG) with `currentColor`; do not use
  emoji or a remote icon font for interface controls.

## Layout and shapes

Wide dashboards keep a compact header, independently scrollable controls rail,
dominant map, and independently scrollable activity/detail panel. Tablet uses a
controls-plus-map row and full-width activity below. Mobile uses a single document
column with controls, map, then activity; all controls stay visible and page overflow
stays vertical. Breakpoints are 900px and 640px.

Use the 4px spacing base. Keep map controls square, inputs lightly rounded, larger
panels rounded-square, and filter chips pill-shaped. Use borders and flat surfaces
as the default; reserve shadows for overlays above map imagery.

## Data and accessibility

Keep the API, hooks, types, filter semantics, source attribution, map providers,
loading/error/retry/empty/stale states, and honest unavailable labels unchanged.
Regional risk profiles are descriptive statistics, not earthquake predictions.
GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory. Check contrast on each
token surface and all four basemaps; preserve keyboard access, visible focus, labels,
touch targets, semantic landmarks, and `prefers-reduced-motion` behavior.

## Basemaps

Use OpenFreeMap Positron for the pale Streets basemap; retain Esri Satellite, Hybrid,
and Terrain choices and all provider attribution. Keep hazard symbols and legends
legible above bright and dark imagery. See `REDESIGN_UI.md` for the exact token values,
contrast targets, view inventory, wireframes, and state requirements.
