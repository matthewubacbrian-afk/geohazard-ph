# Current App Launch Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed Android and iOS simulator startup check for the existing non-published Release apps, without changing app behavior, dependencies, or OS support.

**Architecture:** Keep native Release builds and report generation in the existing Mobile CI jobs. Provision an Android emulator and select a GitHub runner iPhone simulator after those builds. A small Python command installs, launches, and checks the app process after a bounded delay; it emits a clear failure and captures diagnostic logs/screenshots. Unit tests mock platform commands and verify selection, success, timeout, and crash cases. The existing manual device-flow checklist remains the separate functional acceptance gate.

**Tech Stack:** GitHub Actions, Android SDK/adb, Xcode simctl, Python 3 unittest, React Native 0.75.5.

**Design:** `docs/superpowers/specs/2026-10-28-current-app-maintenance-design.md`

---

## Files and responsibilities

- Create `scripts/mobile_runtime_smoke.py`: platform command wrapper, simulator selection, install/launch/liveness check, bounded errors and diagnostics.
- Create `scripts/tests/test_mobile_runtime_smoke.py`: deterministic mocked success and failure tests for both platforms; no device needed locally.
- Modify `.github/workflows/mobile-ci.yml`: provision a pinned Android API 34 emulator, boot available iPhone simulator, run smoke command after existing Release report steps, upload bounded diagnostics on failure. Do not modify audited report JSON or raw trace retention.
- Modify `docs/mobile-runtime-smoke-test.md`: record the automated startup gate's scope and keep the manual result table unfilled until actual flow evidence exists.
- Modify `PLAN.md` and `docs/project-status.md`: show maintenance-first order, current evidence, and remaining device/staging gates. Do not label advisories or flows cleared.

## Task 1: Runtime smoke command

- [x] Write unit tests first for Android install/launch/process alive, Android process exit, iOS simulator selection, iOS install/launch/process alive, missing simulator, command failure, and timeout. Mock all subprocess calls and waits. Assert failures are nonzero with a useful platform-specific message.
- [x] Run `python -m unittest scripts.tests.test_mobile_runtime_smoke -v`; confirm the new tests fail before implementation.
- [x] Implement the smallest `scripts/mobile_runtime_smoke.py` command. Require `--platform`, `--artifact`, and diagnostic output directory. Validate the artifact exists; use bounded subprocess timeouts. Use `com.geohazardph.mobile`; check process survival after a short wait. Never report a flow or security pass.
- [x] Run the focused tests again and confirm pass. Run `ruff check scripts/mobile_runtime_smoke.py scripts/tests/test_mobile_runtime_smoke.py` if Ruff is installed in the project environment; otherwise use the repository's documented lint command.
- [x] Commit the command and tests; push the branch.

## Task 2: CI wiring

- [x] Add Android emulator package/API 34 image installation and bounded boot after the current Release inventory step. Verify KVM, create a named AVD, start headless, and fail on boot timeout. Run the smoke command against `mobile/android/app/build/outputs/apk/release/app-release.apk`.
- [x] After the iOS Release inventory step, select an available iPhone simulator with `simctl`, boot it, and run the smoke command against `$RUNNER_TEMP/mobile-ios-derived/Build/Products/Release-iphonesimulator/GeoHazardPH.app`. Fail if no usable simulator exists. Record diagnostic output only; do not publish app or raw coverage.
- [x] Check workflow syntax and `git diff --check`; run unit tests again. Commit and push.

## Task 3: Tracking, verification, and integration

- [x] Update the manual runtime checklist, root plan, and project status with exact startup-only coverage and remaining device, staging, and Epic 5 holds. Keep all nine current audit rows undetermined unless a fresh audit and evidence show otherwise. Commit and push.
- [x] Run focused Python tests, backend and ML tests/lint, web tests/build, mobile Jest/TypeScript, structure check, and whitespace check sequentially where local resources permit. Record missing local tools honestly; CI is the exact-head authority for native builds and backend integration when Docker is unavailable.
- [ ] Open a PR and attach it to the task. Review the diff independently before merge. Wait for all five exact-head checks; inspect startup logs and compare both Release reports plus four compact traces against the prior audited baseline. Expected audit count is nine, all undetermined; only Android APK hash may differ, unless a dated audit-feed change is independently explained.
- [ ] Merge only if all checks pass and artifact differences are explained. Verify the tested commit is on `origin/main`. Update tracking after merge in the next substantive slice if a separate status-only PR would add no value. Remove the feature worktree only when merged, clean, and free of ignored/untracked content; preserve any ignored files first. Keep the unrelated primary `web/index.html` edit untouched.

## Resume state

Branch: `docs/mobile-maintenance-strategy` based on remote-main `771d529a`.
Pushed code and docs through `f6cdcb33`; this follow-up fixes the independent
review's AVD path, deprecated GPU mode, and missing crash logs. Local checks:
128 backend unit tests, 72 ML tests, 175 web tests/build, 61 mobile tests and
TypeScript, 57 mobile evidence tests, package Ruff, workflow YAML parsing,
structure (140 paths), 102 local links, and whitespace passed. Backend
integration and native simulator launch require exact-head CI. Main baseline
run `40618628164` finished green on Android and iOS. No PR yet. Next: push
this fix, open PR, inspect all five checks and startup screenshots, compare
Release reports/traces, then merge only on a verified exact head. Device flows
and live staging remain unverified; the old framework and OS floors remain.
