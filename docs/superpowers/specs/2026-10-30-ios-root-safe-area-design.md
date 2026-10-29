# iOS root safe area — Design

**Date:** 2026-10-30

## Problem

The iPhone 16 simulator startup screenshot from Mobile CI for PR #77 shows the
"Nearby hazards" heading beneath the status bar and Dynamic Island. The root
component in `mobile/src/navigation/RootNavigator.tsx` uses a plain `View`, so
its screen content begins at the physical top of the iOS display. This makes
the heading hard to read and risks the same overlap on the other tabs.

## Goals

- Keep each tab's content below the iOS status area and the tab bar above the
  bottom safe area.
- Preserve the existing Android layout and all tab interactions.
- Verify the layout on fresh iOS and Android simulator startup screenshots.

## Non-goals

- Redesign any screen, navigation, or tab styling.
- Add a new dependency or change the API, saved data, or backend.
- Claim physical iOS device coverage; the available physical device is Android.

## Context And Constraints

`RootNavigator` owns the single root container for all four tabs. Its `root`
style in `mobile/src/styles.ts` supplies flex and background only. The iOS
startup smoke test in `.github/workflows/mobile-ci.yml` uploads a screenshot,
but currently checks process startup rather than layout geometry. Android's
PR #77 screenshot did not show the heading overlap. Follow
`CODING_STANDARDS.md` and `docs/testing-standards.md` for mobile verification.

## Alternatives Considered

- Add `react-native-safe-area-context`: offers fine-grained inset control, but
  introduces a native package and lockfile/pod changes for this root-level fix.
- Add fixed top and bottom padding: small code change, but cannot adapt to
  different status bar, island, and home-indicator dimensions.

## Design

Replace the root `View` in `RootNavigator` with React Native's built-in
`SafeAreaView`, retaining `styles.root`. No child screen, tab selection, or
state flow changes. On iOS, the safe-area container places the existing screen
content and tabs within the available display area. Android keeps the existing
root layout behavior.

There are no new interfaces, environment variables, network calls, storage
changes, error branches, data transformations, or migrations. The component
remains responsible only for app-level layout and tab composition.

## Rollout

Land as one focused mobile PR from `codex/ios-safe-area`. Review the new iOS
simulator screenshot for visible clearance above the Nearby heading and below
the tabs, and compare the Android screenshot with the previous baseline.
Merge after the mobile CI jobs and relevant local checks pass.

## Files

- `mobile/src/navigation/RootNavigator.tsx`: use the safe-area root container.
- `mobile/tests/RootNavigator.test.ts`: regression coverage for the root
  container when the Jest setup supports rendering it meaningfully.
- `docs/mobile-runtime-smoke-test.md`: record iOS screenshot and Android
  comparison evidence after verification.

## Testing Strategy

- Run `npm test -- --runInBand` and `npx tsc --noEmit` from `mobile/`.
- Run `python scripts/verify_structure.py` and `git diff --check` from the root.
- Use Mobile CI's iOS and Android startup screenshots as the layout regression
  evidence; inspect actual images, not just green startup job status.
- If a focused Jest regression cannot assert visible safe-area behavior without
  mirroring the component implementation, rely on the simulator images and
  explain that limit in the PR rather than adding a brittle test.

## Acceptance Criteria

- The iOS Nearby heading is fully below the status area in the new startup
  screenshot, and the bottom tab bar remains above the home indicator.
- The Android startup screenshot shows no new clipping or unexpected inset.
- Mobile Jest and strict TypeScript checks pass.
- Mobile CI iOS and Android jobs pass on the final PR head.
- The runtime smoke-test document records the screenshot evidence and limits.

## Out Of Scope (backlog)

- Physical iOS device verification remains open until an iPhone is available.
- Broader screen-by-screen accessibility and responsive-layout review remains
  separate from this focused startup defect.
