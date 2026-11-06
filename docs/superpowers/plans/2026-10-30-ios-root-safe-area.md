# iOS root safe area — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Place all mobile tabs inside the iOS safe area without changing Android layout.

**Architecture:** Change the one root container in `RootNavigator`. Keep screen components and styles untouched. Use the existing Mobile CI simulator screenshot artifacts to verify actual geometry on both platforms.

**Tech Stack:** React Native 0.75, TypeScript, Jest, GitHub Actions iOS/Android simulators.

**Spec:** `docs/superpowers/specs/2026-10-30-ios-root-safe-area-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Work only in the isolated `codex/ios-safe-area` branch and commit with Conventional Commits.
- Preserve Android layout, all four tabs, and existing navigation state behavior.
- Do not add packages, lockfile changes, native config changes, or generated artifacts.
- Run mobile Jest and TypeScript checks, structure verification, and `git diff --check`.
- The existing PR #77 iPhone 16 startup screenshot is the failing visual baseline. Jest's Node environment has no native layout measurement. The approved spec permits screenshot comparison instead of an implementation-mirroring unit test.

---

### Task 1: Move the app root into the safe area

**Files:**
- Modify: `mobile/src/navigation/RootNavigator.tsx`

**Interfaces:**
- Consumes: React Native `SafeAreaView` and existing `styles.root`.
- Produces: the same `RootNavigator()` export, children, state, and tab interactions.

- [ ] **Step 1: Confirm the red visual baseline.** Inspect the saved iOS PR #77 screenshot at `C:/Users/matth/AppData/Local/Temp/ghph-pr77-startup-ios/startup.png`; the Nearby heading overlaps the status area. Record that Mobile CI currently asserts startup liveness only.
- [ ] **Step 2: Change the root container.** Import `SafeAreaView` from `react-native`, replace only the outer `<View style={styles.root}>` with `<SafeAreaView style={styles.root}>`, and replace its matching closing `</View>` with `</SafeAreaView>`. Keep nested tabs `<View>` and all children intact.
- [ ] **Step 3: Verify the mobile package.** From `mobile/`, run `npm test -- --runInBand` and `npx tsc --noEmit`; expect zero failed tests and TypeScript exit 0. From the repository root, run `python scripts/verify_structure.py` and `git diff --check`; expect exit 0.
- [ ] **Step 4: Commit the focused code change.** Run `git status --short`, stage only `mobile/src/navigation/RootNavigator.tsx`, and commit `fix: respect ios safe area in mobile root`.

---

### Task 2: Verify simulator layouts and record evidence

**Files:**
- Modify: `docs/mobile-runtime-smoke-test.md`

**Interfaces:**
- Consumes: Mobile CI startup screenshot artifacts from the final PR head.
- Produces: a dated runtime evidence row distinguishing iOS simulator and Android emulator observations from physical-device checks.

- [ ] **Step 1: Push the branch and open a focused PR.** Include Summary, Testing, and Notes, including the iOS physical-device limitation.
- [ ] **Step 2: Wait for Mobile CI.** Check both iOS simulator and Android jobs on the final commit; failures require diagnosis and a new commit before proceeding.
- [ ] **Step 3: Inspect both startup images.** Download the `mobile-startup-ios` and `mobile-startup-android` artifacts. Verify the iOS Nearby heading lies below the status area and the tabs above the home indicator; verify Android has no new clipping or unexpected inset. A green startup job alone does not satisfy this step.
- [ ] **Step 4: Record the observed result.** Add a dated row or paragraph in `docs/mobile-runtime-smoke-test.md` with the app commit, simulator versions, CI run link, actual layout observations, and the unchanged physical iOS limitation. Do not mark unrun mobile flows as passed.
- [ ] **Step 5: Verify and commit documentation.** Run `git diff --check`, `python scripts/verify_structure.py`, and `git status --short`; stage only the smoke-test document and commit `docs: record ios safe area simulator check`. Push and confirm CI passes on the final PR head, inspect its screenshots again if the code changed, then merge only after all acceptance criteria are met.

## Notes for the executor

- Task 2 depends on Task 1 because CI screenshots require the new app build.
- CI runs on hosted macOS and Ubuntu; local Windows cannot run the iOS simulator.
- The attached Android phone may provide an additional check, but it cannot substitute for iOS screenshot evidence.
- Preserve the main checkout's user-owned `web/index.html` edit and do not pull or switch its branch.
