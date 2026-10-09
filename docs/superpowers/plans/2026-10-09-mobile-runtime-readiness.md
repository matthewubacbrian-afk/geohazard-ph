# Mobile Runtime Readiness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify that the implemented GeoHazard PH mobile nearby-alert experience builds and works on Android and iOS simulator or device runtimes, with repeatable checks documented for maintainers.

**Architecture:** Keep the existing React Native 0.75 application and Android debug CI. Add an iOS simulator build to Mobile CI, document a short manual runtime smoke flow that exercises API setup, saved locations, proximity results, and cached offline behavior, and record platform-specific evidence in the project status. Do not add new alert behavior or require store credentials.

**Tech Stack:** React Native 0.75.5, TypeScript, Jest, Gradle, CocoaPods, Xcode, GitHub Actions.

**Related design:** `docs/superpowers/specs/2026-10-09-mobile-native-runtime-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Preserve React Native 0.75.5 and the current app architecture; do not migrate to Expo or upgrade React Native.
- Keep API fields snake_case at the wire boundary and use the existing API mapping.
- Do not add background push, push credentials, production signing, store publishing, user accounts, or device-location permissions.
- Never put a personal API URL, signing key, token, provisioning profile, or generated build output in the repository.
- Run `npm test -- --runInBand` from `mobile/`, `python scripts\verify_structure.py`, and `git diff --check`.
- Android CI already compiles `assembleDebug`; extend that workflow only for an iOS simulator build and preserve its Android/Jest steps.
- A CI simulator build proves compilation, not user-flow or physical-device behavior. Record manual runtime checks only when actually performed.

## Files And Responsibilities

- `.github/workflows/mobile-ci.yml` — add an iOS simulator build on a macOS runner while retaining existing checks.
- `scripts/tests/test_mobile_ci_workflow.py` — assert that the Android build remains configured and the iOS simulator build is present.
- `docs/mobile-runtime-smoke-test.md` — document reproducible Android and iOS setup and manual acceptance steps.
- `docs/project-status.md` — record native scaffold/CI completion and distinguish unverified runtime work from deferred release scope.
- `docs/superpowers/plans/2026-10-09-mobile-runtime-readiness.md` — track implementation and verification evidence.

---

### Task 1: Add iOS simulator compilation to Mobile CI

**Files:**
- Modify: `.github/workflows/mobile-ci.yml`
- Modify: `scripts/tests/test_mobile_ci_workflow.py`
- Reference: `mobile/ios/Podfile`, `mobile/ios/GeoHazardPH.xcodeproj`, `mobile/package-lock.json`

**Interfaces:**
- Consumes: existing npm lockfile, iOS Podfile, and `GeoHazardPH` Xcode scheme.
- Produces: a macOS CI job that installs locked JavaScript dependencies, installs CocoaPods dependencies, and builds the iOS simulator target without signing.

- [x] **Step 1: Add a workflow regression test**

Extend `scripts/tests/test_mobile_ci_workflow.py` to assert that the workflow has a macOS job, installs the mobile npm lockfile, runs `pod install`, and calls `xcodebuild` for the `GeoHazardPH` simulator scheme with signing disabled. Keep the existing assertions for JDK 17, SDK installation, and Android `assembleDebug`.

- [x] **Step 2: Run the focused test and confirm it fails for the missing iOS job**

Run from the repository root:

```powershell
python -m unittest discover -s scripts/tests -p test_mobile_ci_workflow.py
```

Expected: the new iOS-workflow assertion fails because the workflow has no macOS job; existing Android assertions pass.

- [x] **Step 3: Add an iOS job using a supported macOS runner**

Add a separate job with `runs-on: macos-15`. Check out the repository, set up Node 22 with `mobile/package-lock.json` as its cache key, run `npm ci` from `mobile/`, and run `pod install` from `mobile/ios/`.

- [x] **Step 4: Configure the simulator scheme build without signing**

Configure the Mobile CI job to run from `mobile/`:

```bash
xcodebuild \
  -workspace ios/GeoHazardPH.xcworkspace \
  -scheme GeoHazardPH \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Keep signing and export/archive steps out of this job. The job must fail if CocoaPods or the simulator compilation fails.

- [x] **Step 5: Run workflow checks and review both platform jobs**

Run the focused workflow regression test, Mobile Jest, structure verification, and `git diff --check`. Confirm the existing Android setup and `assembleDebug` steps remain present. Hosted CI is required to verify the macOS build; report it as pending until the job runs successfully.

- [x] **Step 6: Commit the CI change**

```bash
git add .github/workflows/mobile-ci.yml scripts/tests/test_mobile_ci_workflow.py
git commit -m "ci: build iOS simulator app"
```

### Task 2: Document the mobile runtime smoke flow

**Files:**
- Create: `docs/mobile-runtime-smoke-test.md`
- Reference: `README.md` mobile setup section, `docs/superpowers/specs/2026-10-09-epic4-mobile-nearby-alerts-design.md`, `docs/error-handling-and-logging.md`

**Interfaces:**
- Consumes: the existing mobile tabs, saved-location form, `/api/v1/events` endpoint, retry behavior, and persistent cache.
- Produces: a concise manual checklist with Android emulator/device and iOS simulator setup differences and expected visible outcomes.

- [x] **Step 1: Document environment prerequisites and API reachability**

List the platform prerequisites from the README and explain that the device must reach an API base URL ending in `/api/v1`. Include Android emulator `10.0.2.2` guidance and physical-device LAN routing; do not insert a private or fixed operator URL.

- [x] **Step 2: Add observable acceptance steps**

The checklist must cover: launch to Nearby; configure the API URL; add and delete a valid saved location; reject invalid coordinates/radius; refresh events and see a match inside the radius; see a clear no-match state outside the radius; stop API access and confirm cached events are labeled offline with retry available; relaunch and confirm saved locations/settings persist. If no fixture or reachable event exists, record that data-dependent checks were blocked rather than passed.

- [x] **Step 3: State what the checks do not prove**

Clarify that foreground alerts are informational proximity matches, not official warnings; simulator smoke does not prove background push, production reliability, or store readiness. Keep a date/platform/result/evidence table blank for the operator or executor to fill after a real run.

- [x] **Step 4: Verify documentation and commit it**

Run `python scripts\verify_structure.py` and `git diff --check` from the repository root.

```bash
git add docs/mobile-runtime-smoke-test.md
git commit -m "docs: add mobile runtime smoke checklist"
```

### Task 3: Execute platform and app-flow verification

**Files:**
- Verify: `.github/workflows/mobile-ci.yml`, `mobile/`, `docs/mobile-runtime-smoke-test.md`
- Update: `docs/mobile-runtime-smoke-test.md` with actual results only.

**Interfaces:**
- Consumes: the Android and iOS CI builds plus the manual checklist from Tasks 1–2.
- Produces: recorded Jest/Android/iOS build outcomes and runtime smoke outcomes with blockers identified.

- [x] **Step 1: Run the mobile unit suite and structure checks**

```powershell
Set-Location mobile
npm test -- --runInBand
Set-Location ..
python scripts\verify_structure.py
git diff --check
```

Expected: Jest passes; the structure verifier and whitespace check pass.

- [x] **Step 2: Observe hosted Android and iOS build jobs**

Confirm both platform build jobs pass on the pull request. A green Jest job alone does not satisfy native compilation acceptance.

- [ ] **Step 3: Run the manual smoke flow on available runtimes**

Use at least one Android emulator/device and one iOS simulator. Follow the checklist with a reachable development or staging API. Record exact platform/runtime, date, API environment (without secrets), completed flows, and blockers. Do not claim physical-device coverage from a simulator run.

- [x] **Step 4: Update project status from observed evidence**

Update `docs/project-status.md` and the smoke checklist only with completed evidence. If a platform runtime is unavailable, preserve it as open with the concrete prerequisite (for example, macOS/Xcode or a reachable test API).

- [x] **Step 5: Run final verification and commit the status record**

Run the Mobile Jest suite, `python scripts\verify_structure.py`, and `git diff --check` after any fixes. Commit the evidence and status update with `docs: record mobile runtime verification`.

## Notes For The Executor

- The existing Android workflow uses JDK 17 and Android SDK 34; do not alter its pinned toolchain as part of this work.
- The current Windows workstation cannot compile iOS locally. The macOS GitHub runner is the compilation authority; a simulator run still requires an available Mac runtime.
- Manual flows depend on an API with events around the selected coordinates. A passing app build does not substitute for those data-dependent checks.
- If smoke testing finds an application defect, stop and write a focused regression test before changing behavior; keep unrelated fixes out of this readiness plan.

## Execution Record (2026-10-09)

- Workflow regression test first failed because the `ios-simulator` job was absent, then passed after the CI edit (4 focused tests; 5 tests in the full script suite).
- `npm ci` restored the lockfile dependencies missing from this workstation's `node_modules`; Mobile Jest then passed all 31 tests in 8 suites.
- `python scripts\verify_structure.py` found all 140 expected paths, and `git diff --check` passed.
- CI job and checklist commits: `c79c765` and `8307112`.
- [PR #20 Mobile CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/37906366103) passed: Android `assembleDebug` completed in the `mobile` job (3m53s) and the new iOS simulator job completed in 14m5s. Backend, ML, and web PR checks also passed.
- Manual runtime smoke is still open. This Windows host has Java 25, no configured Android SDK or emulator, and no macOS/Xcode environment. The checklist requires a reachable API with a representative event and an Android runtime plus an iOS simulator; no runtime flow result is claimed.
