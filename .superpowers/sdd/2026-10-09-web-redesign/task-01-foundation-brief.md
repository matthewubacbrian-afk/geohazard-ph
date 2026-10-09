# Task 01 — Design foundation

## Objective

Implement the approved semantic token system and self-hosted IBM Plex fonts from
the plan's Task 1. Add a test-first contrast check for risk and magnitude token
colors against each light dashboard surface.

## Scope

- `web/package.json`, `web/package-lock.json`
- `web/src/main.tsx`
- `web/src/styles/tokens.css`, `base.css`, `utilities.css`
- New `web/tests/DesignTokens.test.ts`
- Do not edit any component/page files, API clients, hooks, types, backend/mobile/ML,
  or pre-existing uncommitted sidebar files.

## Required design

Follow `web/REDESIGN_UI.md`: semantic surfaces and text, risk colors
`#315B4C/#75500E/#99422F/#702820`, neutral magnitude colors
`#69645A/#58544D/#413D37/#292824`, 4px spacing, radii 0/4/10/999px, IBM Plex
Serif/Sans/Mono tokens, tabular numerals, visible focus, and reduced-motion support.
Self-host through Fontsource and import only the needed IBM Plex weights. Preserve
CSS Modules and do not add runtime font/icon CDNs.

## TDD and acceptance

1. Write the token contrast test before changing tokens. It should read the
   stylesheet using a test-file-relative path, assert all required semantic tokens
   exist, compute WCAG relative luminance, require ≥4.5:1 for each risk/magnitude
   color against the three light surfaces, and confirm the risk and magnitude token
   sets are distinct.
2. Run the test and record the expected red failure due to missing tokens.
3. Implement the minimal token/font loading changes.
4. Run the focused test, `npm run build`, and `git diff --check`.
5. Confirm no API/component behavior changes and stage only Task 1 files plus this
   brief/report. Commit `style: add geohazard design tokens and fonts`.

## Report requirements

Record the red/green test evidence, build result, package versions, imported weights,
license/source note, contrast results, changed files, commit hash, and any limitation.
