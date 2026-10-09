# Task 01 — Design foundation report

## Verification

- TDD red: `npm test -- --run tests/DesignTokens.test.ts` failed before implementation with `missing required token --risk-moderate`.
- Focused green: `npm test -- --run tests/DesignTokens.test.ts` passed (1 test).
- Production build: `npm run build` passed (`tsc` and Vite build). Vite emitted the existing large JavaScript chunk advisory; the build completed successfully.
- `git diff --check` passed.

## Inline SVG icon follow-up

A post-commit review found remaining Material Symbols text glyphs in the existing dashboard controls after removing the remote font import. Replaced those glyphs with a shared inline SVG icon component. Its SVGs inherit `currentColor`, use fixed 18px dimensions, and are hidden from assistive technology because their surrounding controls already have visible labels or accessible names. The focused icon test was written first, failed on the missing component, then passed after the implementation. The existing dirty sidebar CSS scroll sizing was preserved; no sidebar CSS edit was needed for the SVGs.

The follow-up cleanup also removed the now-obsolete Material Symbols font-family and variation declarations from the sidebar icon style while retaining its 18px sizing and both pre-existing scroll sizing changes.

## Fonts

Installed Fontsource package versions: `@fontsource/ibm-plex-sans` 5.3.0, `@fontsource/ibm-plex-serif` 5.3.0, and `@fontsource/ibm-plex-mono` 5.3.0. IBM Plex Sans weights 400/500/600, Serif weights 400/600, and Mono weights 400/500 are imported in `web/src/main.tsx`. Fontsource packages include their SIL Open Font License 1.1 license files; source and license are recorded in `web/DESIGN_NOTES.md` and IBM's source repository is https://github.com/IBM/plex.

## Contrast

Measured minimum contrast against `--surface` (#F3F0E9), `--surface-raised` (#FAF8F3), and `--surface-container` (#E8E4DA):

| Token | Minimum |
| --- | ---: |
| `--risk-low` | 6.06:1 |
| `--risk-moderate` | 5.68:1 |
| `--risk-high` | 5.21:1 |
| `--risk-very-high` | 8.22:1 |
| `--magnitude-low` | 4.63:1 |
| `--magnitude-moderate` | 5.93:1 |
| `--magnitude-high` | 8.49:1 |
| `--magnitude-very-high` | 11.62:1 |

All measured pairs meet 4.5:1; risk and magnitude palettes are distinct.

## Changed files

- `web/package.json`, `web/package-lock.json`
- `web/src/main.tsx`
- `web/src/styles/tokens.css`, `web/src/styles/base.css`
- `web/tests/DesignTokens.test.ts`
- `web/tests/Icon.test.tsx`
- `web/src/components/common/Icon.tsx`
- `web/src/components/dashboard/DashboardSidebar.tsx`, `DashboardMapArea.tsx`
- `web/src/components/events/EventDetailPanel.tsx`
- `web/DESIGN_NOTES.md`
- `.superpowers/sdd/2026-10-09-web-redesign/task-01-foundation-brief.md`
- `.superpowers/sdd/2026-10-09-web-redesign/task-01-foundation-report.md`

No API, hook, domain type, backend, mobile, or ML files were changed. Pre-existing sidebar and dashboard layout edits were left untouched. The commit hash is reported in the task completion message because a report cannot include its own commit's hash without changing that hash.
