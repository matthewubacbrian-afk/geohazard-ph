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
- [ ] Commit and push the bounded change before prolonged verification.

## Task 3: Verify and integrate

- [ ] Run local mobile Jest and TypeScript, web tests/TypeScript/build, backend and ML tests/Ruff, structure, local documentation links, and whitespace sequentially. Report any local environment gaps plainly.
- [ ] Get an independent read-only review of the architecture flags, library compatibility claims, and evidence wording.
- [ ] Open a PR. Require backend, ML, web, Android mobile, and iOS simulator checks on its final head. Confirm Android/iOS Debug and non-published Release builds ran with the New Architecture flags.
- [ ] Compare both Release reports and four compact traces with PR #72, investigate every difference, and preserve all undetermined dispositions unless affected-API evidence supports a separate review.
- [ ] Merge only after the gate passes. Verify the tested commit on remote main; update the plan/status checklist, preserve ignored files, and remove only the clean merged worktree and branch.

## Resume state

Branch `feat/mobile-new-arch-readiness` is an isolated worktree at remote main `e3bf201f` (PR #72 merged). The plan commit `ebf5d11b` is pushed. The three pinned native packages declare Codegen metadata; both platform opt-in flags and tracking notes are changed. Local mobile Jest passed 61 tests and TypeScript completed with exit 0. Native builds and device flows have not run on this branch. Next: commit and push the opt-in/configuration change, finish local suites sequentially, then open a PR for exact-head CI.
