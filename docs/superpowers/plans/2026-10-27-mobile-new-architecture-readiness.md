# Mobile New Architecture readiness — Implementation Plan

> **For agentic workers:** Execute the checked steps in order in this isolated worktree. Use the existing migration assessment as the design and keep the later framework migration separate.

**Goal:** Opt the pinned React Native 0.75.5 app into the New Architecture on Android and iOS, and record build evidence without claiming device-flow or advisory safety.

**Architecture:** Preserve the existing React Native, React, Metro, native-library, Android SDK, and iOS deployment versions. Change only the Android architecture property and the iOS Pod install environment, then let the existing CI compile Debug and non-published Release apps on both platforms. If a pinned library fails, fix only the evidenced incompatibility in this branch or leave the PR unmerged. Physical-device cache, camera, and SVG checks remain a separate gate.

**Tech Stack:** React Native 0.75.5, Android Gradle, CocoaPods, Jest, TypeScript, GitHub Actions.

**Design basis:** [Migration assessment](../../mobile-rn-migration-assessment-2026-10-20.md), [Epic 4 runtime checklist](../../mobile-runtime-smoke-test.md), and [project plan](../../../PLAN.md).

## Global constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Keep all nine current audit rows `undetermined`; the direct `node-forge` row remains high. New native files or a green simulator build do not prove runtime reachability or safety.
- Do not change minimum Android/iOS versions, React Native, dependencies, lockfile, generated build files, or app behavior unless a specific build failure requires a narrow fix.
- Do not claim saved-location persistence, image capture, or SVG rendering passed without a recorded device run.
- Run local backend, ML, web, and mobile suites and lint/type/build checks sequentially; use CI for Docker-backed integration and clean Android/iOS native builds. Require all five exact-head checks and compare both Release reports and four compact traces with PR #72. An architecture change may legitimately alter native inventory and artifact hashes; inspect and document each difference rather than waiving it.

## Task 1: Confirm the pinned baseline

**Files:** `mobile/package.json`, `mobile/package-lock.json`, `mobile/android/gradle.properties`, `mobile/ios/Podfile`, `mobile/android/app/src/main/java/com/geohazardph/mobile/MainApplication.kt`, `.github/workflows/mobile-ci.yml`.

- [x] Confirm pinned Async Storage 1.24.0, Image Picker 8.2.1, and SVG 15.12.1 each declare Codegen metadata. Their package declarations are evidence of integration hooks, not proven device compatibility.
- [x] Confirm Android `BuildConfig.IS_NEW_ARCHITECTURE_ENABLED` drives host initialization and iOS CI runs `pod install` from the tracked Podfile.
- [x] No incompatibility was established by source inspection; native CI and device flows remain the deciding evidence. No dependency refresh was made.

## Task 2: Enable and document the architecture

**Files:** `mobile/android/gradle.properties`, `mobile/ios/Podfile`, `docs/mobile-rn-migration-assessment-2026-10-20.md`, `docs/project-status.md`, `PLAN.md`.

- [x] Set Android `newArchEnabled=true` and set `ENV['RCT_NEW_ARCH_ENABLED'] = '1'` before the Podfile loads React Native scripts, so local and CI pod installs select the same architecture.
- [x] Document native build expectations and unverified real-device flows in the migration assessment and smoke checklist. Preserve the later Android SDK 24/iOS 15.1 migration decision.
- [x] Commit and push the bounded change as `8e440d7f` before prolonged verification; the separate PR #72 plan closeout was pushed as `b3c84561`.

## Task 3: Verify and integrate

- [x] Run local mobile Jest (61) and TypeScript; web tests (175), TypeScript, and production build; backend unit tests (128) and Ruff; ML tests (72) and Ruff; scripts tests (54 plus 7 subtests) and CI-scoped Ruff; structure (140 paths), 113 local document links, and whitespace sequentially. Local Docker-backed backend integration and native iOS/Android builds require CI. An initial web test run failed when Vite denied a worker loaded through an external `node_modules` junction; copying the same preserved dependencies into this ignored worktree path resolved it, and the full rerun passed. Broad, non-CI `ruff check scripts` has six pre-existing findings in untouched files; the workflow's two selected staging script files pass Ruff.
- [x] Get an independent read-only review of the architecture flags, library compatibility claims, and evidence wording. It found no critical, important, or minor issue; it confirmed CI will select the flags, while native build and device results remain unverified.
- [x] Open [PR #73](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/73) after the local gate and independent review.
- [ ] Require backend, ML, web, Android mobile, and iOS simulator checks on its final head. Confirm Android/iOS Debug and non-published Release builds ran with the New Architecture flags.
- [ ] Compare both Release reports and four compact traces with PR #72, investigate every difference, and preserve all undetermined dispositions unless affected-API evidence supports a separate review.
- [ ] Merge only after the gate passes. Verify the tested commit on remote main; update the plan/status checklist, preserve ignored files, and remove only the clean merged worktree and branch.

## Resume state

Branch `feat/mobile-new-arch-readiness` is an isolated worktree at remote main `e3bf201f` (PR #72 merged). [PR #73](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/73) is open; `fc090a1a` is the last pushed head before this checkpoint update. Android/iOS opt-in flags and tracking notes are changed; all local checks listed above passed after correcting the Vite dependency path. Independent review found no issue. Native builds and device flows have not yet passed on this branch. Next: commit/push this checkpoint, require all five CI checks on the new exact head, inspect both Release reports and four compact traces against PR #72, then merge only if the full gate passes.
