# Task 06 — Risk and volcano panels report

## Changes
- Integrated the existing `RegionLookup` into `RiskProfilesPanel` with controlled local search state. Lookup rows and cards use the same case-insensitive filtered set; an empty query restores all profiles and no matches show clear feedback.
- Kept risk profile values, drivers, model/dataset information, and the descriptive-statistics disclaimer. Added text labels and distinct shape treatments for risk levels using semantic risk tokens.
- Restyled risk cards/lookup and the volcano bulletin panel with the dashboard surface, typography, borders, focus treatment, and compact data hierarchy.
- Extended volcano coverage for retrieved timestamps and the missing alert level (`null`), alongside existing level-zero, source, stale, loading, retry, and empty assertions.
- No API client, hook, type, backend, or request behavior changed.

## TDD and verification
- RED: `npm test -- --run tests/RiskProfilesPanel.test.tsx` failed because the active panel did not expose the labeled region search input.
- GREEN: `npm test -- --run tests/RiskProfilesPanel.test.tsx tests/RiskProfile.test.tsx tests/VolcanoPanel.test.tsx` passed (3 files, 8 tests).
- `npm run build` passed. Vite emitted the existing large JavaScript chunk advisory.
- `git diff --check` passed.
- Spec review follow-up: added a visible-label regression assertion, confirmed RED while visible copy differed from the accessible name, and aligned the visible label to “Filter regions”. Focused suite/build/diff-check were rerun before amending the task commit.
- Quality cleanup follow-up: risk query/profile/label normalization now uses locale-stable `toLowerCase()`. A Turkish-locale regression test first failed for `ISLAND` / `HIGH`, then passed for both the filtered card and lookup row after the fix.

## Files
- Risk panel, card, and lookup TSX/CSS Modules.
- Volcano panel CSS Module.
- `RiskProfilesPanel.test.tsx` and added volcano assertions in `VolcanoPanel.test.tsx`.
- This brief and report.

## Visual review / limits
Did not start the app: the approved task sequence reserves running services for Task 7’s final desktop/mobile verification. No screenshot review in this task.
