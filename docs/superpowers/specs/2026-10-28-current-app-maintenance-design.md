# Current App Maintenance and Runtime Verification Design

**Date:** 2026-10-28
**Decision:** Keep React Native 0.75.5 and the current Android SDK 23/iOS 13.4 minimums while proving the existing app and resolving observed failures. The user approved this direction on 2026-10-28. This document defines verification and maintenance; it does not approve a framework, dependency, or OS-floor upgrade.

## Current evidence and limit

The latest remote-main commit at design time is `771d529a`. Backend, ML, and web CI passed on that commit. The Android mobile job passed tests, TypeScript, Debug and non-published Release builds; the iOS job was still running when checked. Earlier PR #73 passed both platform builds with the New Architecture flags enabled on the current framework. These builds do not establish that the app launches, that saved data persists, or that camera and SVG flows work on devices. The device result tables in `docs/mobile-runtime-smoke-test.md` remain empty. The current nine mobile audit rows are undetermined, including a high direct `node-forge` row. A live OCI staging host and DNS have not been recorded; Epic 5 profile export is held by the domain-review record.

## Strategy and order

1. **Preserve a reproducible baseline.** Require the five existing exact-head CI checks for changes, including mobile tests, TypeScript, Android/iOS Debug and non-published Release builds. Compare Android and iOS Release reports and compact traces whenever mobile source, native settings, lockfile, or build workflow changes. Keep audit dispositions evidence based. Repair a failed baseline before introducing framework changes.
2. **Add a bounded automated launch gate.** In a separate implementation slice, boot an Android emulator and iOS simulator in CI, install the current Debug app, launch it, and fail if installation, launch, or a bounded post-launch liveness check fails. Record each platform separately. A runner missing the required simulator must fail clearly; it must not become a skipped or green result. Use the built app and existing CI dependencies rather than adding an app testing framework for this first gate. This gate checks startup only.
3. **Run the existing device-flow checklist.** On Android and iOS, record exact app commit, OS, device or simulator, reachable API environment, completed steps, failures, and evidence in `docs/mobile-runtime-smoke-test.md`. Cover saved-location validation and persistence, URL-scoped offline cache, refresh recovery, camera permission/capture, and SVG overlay. A simulator result does not replace a physical-camera or physical-device result. Missing devices or API data are recorded as blocked, not passed.
4. **Verify staging independently.** With an OCI host, DNS, and configuration, deploy the held-export mode and record health, event-feed, and web smoke results. The branch-only staging workflow and published artifact are insufficient evidence of a live deployment. Profile export stays held until the Epic 5 domain-review decision and validation gates are complete.
5. **Maintain without silent upgrades.** Review main CI on every change and recheck open advisories and dependency inputs at least monthly, recording the date and affected paths. Treat a newly actionable security issue or failing build as a maintenance defect. Evaluate a supported React Native migration only after the current-app runtime and staging gates are recorded, with a separate explicit OS-support decision and new post-migration evidence. This is a checkpoint, not a promise that the old framework can be retained indefinitely.

## Acceptance and failure handling

The automated gate must produce a clear pass or failure for each platform on the exact commit. It must not report user-flow coverage or advisory clearance. A startup crash, timeout, absent simulator, or missing app bundle is a failure with log evidence. The manual checklist passes only when each required step has a recorded observation; unavailable hardware, empty feeds, or unreachable staging remain open gates. Any observed app defect gets a focused regression test where feasible and a separate fix before the app is described as functioning. Release readiness requires both platform device-flow evidence and live staging evidence, with the Epic 5 export still held unless separately approved.

## Scope of first implementation slice

Add and verify startup smoke checks for the existing app in the mobile CI workflow, and update the tracked plan and runtime checklist with their precise coverage and results. Do not change React Native, package versions, minimum OS support, app behavior, or the held export. Device-flow execution and live staging are later evidence slices because their prerequisites are not present in this workspace.
