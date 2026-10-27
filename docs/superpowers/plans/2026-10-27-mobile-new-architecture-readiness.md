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

- [ ] Confirm installed package versions and native-library Codegen/interop configuration on this branch.
- [ ] Confirm Android `BuildConfig.IS_NEW_ARCHITECTURE_ENABLED` drives host initialization and iOS CI runs `pod install` from the tracked Podfile.
- [ ] Record any compatibility issue with source and exact version; avoid an unrelated dependency refresh.

## Task 2: Enable and document the architecture

**Files:** `mobile/android/gradle.properties`, `mobile/ios/Podfile`, `docs/mobile-rn-migration-assessment-2026-10-20.md`, `docs/project-status.md`, `PLAN.md`.

- [ ] Set Android `newArchEnabled=true` and set `ENV['RCT_NEW_ARCH_ENABLED'] = '1'` before the Podfile loads React Native scripts, so local and CI pod installs select the same architecture.
- [ ] Document how to reproduce the native builds and what remains unverified on devices. Preserve the later Android SDK 24/iOS 15.1 migration decision.
- [ ] Commit and push the bounded change before prolonged verification.

## Task 3: Verify and integrate

- [ ] Run local mobile Jest and TypeScript, web tests/TypeScript/build, backend and ML tests/Ruff, structure, local documentation links, and whitespace sequentially. Report any local environment gaps plainly.
- [ ] Get an independent read-only review of the architecture flags, library compatibility claims, and evidence wording.
- [ ] Open a PR. Require backend, ML, web, Android mobile, and iOS simulator checks on its final head. Confirm Android/iOS Debug and non-published Release builds ran with the New Architecture flags.
- [ ] Compare both Release reports and four compact traces with PR #72, investigate every difference, and preserve all undetermined dispositions unless affected-API evidence supports a separate review.
- [ ] Merge only after the gate passes. Verify the tested commit on remote main; update the plan/status checklist, preserve ignored files, and remove only the clean merged worktree and branch.

## Resume state

Branch `feat/mobile-new-arch-readiness` is an isolated worktree at remote main `e3bf201f` (PR #72 merged). This plan is the first branch change. Next: verify the three pinned native libraries and both platform entrypoints, then set the opt-in flags. No native build or device flow has passed on this branch yet.
