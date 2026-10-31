# Android QA build — Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task by task.

**Goal:** Produce an identifiable standalone APK for local physical-device testing.

**Architecture:** QA inherits release bundling with an isolated application ID and
QA-only HTTP manifest; verify final APKs and smoke the packaged result in CI.

**Tech Stack:** Android Gradle, React Native 0.75.5, Python unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-31-android-qa-build-design.md`

## Global Constraints

Follow repository standards; no production HTTP relaxation or app/data release.
Use Conventional Commits and the separate `ci/android-qa-build` worktree. Run
script tests/lint, mobile Jest/TypeScript, native CI, structure, and whitespace.

### Task 1: APK contract and Android runtime identity

**Files:** Create `scripts/mobile_qa_artifact.py` and
`scripts/tests/test_mobile_qa_artifact.py`; modify runtime smoke command/tests.

**Interfaces:** CLI flags and record fields are defined in the spec. A manifest
inspector reports package, debuggable flag, and cleartext flag from aapt output.

- [x] Write failing temporary-ZIP and manifest validation cases plus custom
  package/activity smoke regression; run and confirm the intended failures.
- [x] Implement validation and identity parameters; rerun focused and full script
  tests, then Ruff. No device or live network is needed for these tests.
- [x] Commit the verified command and tests.

### Task 2: Native variant and CI

**Files:** Modify Gradle; create QA manifest/resources and `android-qa.yml`.

**Interfaces:** `./gradlew assembleRelease assembleQa` produces the reference
release APK and QA APK; artifact command writes `build-info.json` next to QA APK.

- [x] Add `qa { initWith release; applicationIdSuffix ".qa";
  versionNameSuffix "-qa"; debuggable false; matchingFallbacks = ["release"] }`.
- [x] Add QA-only HTTP manifest and `GeoHazard QA` app-name resource.
- [x] Add workflow checks, both builds, final APK inspection, API34 QA startup
  using custom package and fully qualified activity, then APK/metadata upload.
- [x] Run native CI and inspect manifests, embedded bundle, ABIs, metadata, and
  startup screenshot; fix failures before claiming an installable build.

### Task 3: Documentation, review, and integration

**Files:** README, runtime checklist, spec/plan evidence.

**Interfaces:** Operator downloads one commit-specific artifact and verifies its
APK hash before installing. QA uses its own saved API URL and locations.

- [x] Document artifact download, hash verification, installation, USB API
  forwarding, Metro-free startup, and physical acceptance limits.
- [x] Reconcile current main after readiness integration.
- [ ] Pass final integrated-head CI checks.
- [ ] Obtain independent review, open PR, and wait for all required checks.
- [x] If a phone is connected, verify startup with no Metro and repeat foreground
  acceptance. Otherwise keep this physical gate explicitly pending.
- [ ] Merge only reviewed, passing work; record tested commit and artifact identity.

## Execution evidence (2026-10-31)

Source review identified two policy gaps, both fixed with red/green regressions:
network-security resources can override the cleartext flag, and an absent flag
must not count as an explicit Release denial. The Release-only manifest now
states false; unsupported resources fail verification. Independent recheck found
no remaining source blockers. Local checks passed: 69 script tests plus eight
subtests, 61 mobile tests, strict TypeScript, Ruff, structure, and whitespace.
A real existing debug APK was parsed successfully with Android build tools.
Local mobile checks reused a dependency set with the unchanged lockfile. All six
checks passed on implementation head `8ad89fe8`, including clean native builds,
final APK inspection, and Android/iOS startup. The downloaded QA artifact from
merge checkout `c96b2080fbb6ebff347c5af7d2dea0add38de7d4` was hash-verified and
tested on the connected Infinix phone without Metro. Foreground validation,
matching, offline cache across process restart, recovery, and capture passed;
the missing initial-preview Retake control is tracked in a separate fix branch.
See `docs/android-qa-acceptance-2026-10-31.md` for exact identity and limits.
Readiness PRs #79 and #80 are integrated locally; the final combined head still
requires its own CI checks and review before merge.
