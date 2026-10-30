# Android QA build — Design

**Date:** 2026-10-31

## Problem

Mobile CI builds apps but retains reports rather than installable APKs. The latest
phone checks combined an older native binary with current JavaScript, and Metro
setup delayed testing. Testers need one identifiable APK built from one commit.

## Goals

- Build an independently installable `com.geohazardph.mobile.qa` APK with its own
  `GeoHazard QA` label, embedded JavaScript, and developer support disabled.
- Allow local HTTP API access in this QA variant only.
- Retain the APK and a record of its commit, lockfile hash, APK hash, application
  ID, and bundled native architectures for seven days in GitHub Actions.
- Reject missing bundles, wrong packages, debuggable QA apps, or cleartext-enabled
  production APKs; exercise standalone QA startup in an emulator.

## Non-goals

Store signing/publication, framework migration, scientific validation, model
provisioning, new product UI, and Oracle staging.

## Context And Constraints

The user approved this slice on October 31 after the proposed readiness sequence.
Use `ci/android-qa-build` in its own worktree. Follow CODING_STANDARDS.md, glossary,
testing standards, error-handling rules, and git workflow. Preserve existing
debug/release builds and Release evidence reports. The connected phone previously
reported armeabi-v7a; include that ABI alongside the existing configured ABIs.

## Alternatives Considered

1. Upload debug APK only: simpler, but still requires Metro. Rejected.
2. Relax HTTP in release: simpler configuration, but changes production behavior.
   Rejected.
3. Separate release-like QA build: chosen; package isolation preserves existing app
   data and bundling removes the runtime server dependency.

## Design

### Architecture and components

Add a `qa` Android build type initialized from release, signed with the existing
development key, `debuggable false`, `.qa` application ID suffix, `-qa` version
suffix, and release dependency fallback. Keep QA out of React Native's debuggable
variants so its bundle task runs. Add QA-only manifest and label resources.

A dedicated Android QA workflow builds Release and QA from one checkout, runs
mobile and script checks, verifies the final artifacts, and runs the shared
startup checker against QA in an API 34 emulator without Metro. Retain the APK,
build record, and startup diagnostics. Trigger manually and on relevant PR/main
changes; do not change existing audited Release upload paths.

### Interfaces

`scripts/mobile_qa_artifact.py` accepts `--apk`, `--release-apk`, `--lockfile`,
`--commit`, `--aapt`, and `--output`. Its record contains `commit`, `application_id`,
`apk_sha256`, `lockfile_sha256`, and `native_abis`. Validate the APK ZIP bundle and
native ABI entries and use Android build tools to inspect the merged manifests.

Extend the Android runtime checker with optional `--android-package` and
`--android-activity`, defaulting to the current application and fully qualified
MainActivity. Keep iOS behavior unchanged. Record the actual package in results.

### Configuration, failures, and data

No new API configuration or hardcoded server URL. The existing Saved locations
form sets the API address. Manifest checks fail closed with a concise diagnostic;
no failed artifact is published. Build metadata contains no credentials or local
developer paths. Application ID separation gives QA independent saved data.

## Rollout

Review and integrate readiness PRs #79/#80 after passing checks, then rebase or
merge current main into this feature branch before final integration. A phone may
be used only when connected; record missing hardware instead of claiming a pass.

## Files

- `mobile/android/app/build.gradle` — QA build type.
- `mobile/android/app/src/qa/AndroidManifest.xml` — development HTTP scope.
- `mobile/android/app/src/qa/res/values/strings.xml` — distinct label.
- `scripts/mobile_qa_artifact.py` and its script tests — final artifact contract.
- `scripts/mobile_runtime_smoke.py` and its tests — configurable Android identity.
- `.github/workflows/android-qa.yml` — QA build, artifact verification, smoke, retention.
- `README.md`, `docs/mobile-runtime-smoke-test.md` — download/install and acceptance.
- This spec and its implementation plan — execution and verification evidence.

## Testing Strategy

Unit tests use temporary APK ZIPs and fake Android manifest inspection results.
Cover absent bundle, absent phone ABI, wrong identity, debuggable QA, unsafe
release manifest, malformed inspection output, and success hashes. Extend smoke
tests to assert the QA package/activity is used for install/launch/liveness and
result metadata. Run script tests/lint, mobile tests and TypeScript, structure,
whitespace, native CI builds, and emulator startup. Verify APK checksum before
physical installation; test startup with Metro absent and local API over USB.

## Acceptance Criteria

- [ ] QA APK bundles JavaScript, has the separate ID/label, and launches without Metro.
- [ ] QA allows local HTTP; the inspected release manifest does not enable cleartext.
- [ ] Metadata hashes match the uploaded APK and checked-out lockfile/commit.
- [ ] All configured ABIs, including armeabi-v7a, are present.
- [ ] Unit, package, native build, and startup checks pass before merge.
- [ ] Any physical-device checks identify the exact downloaded commit and APK hash.

## Out Of Scope (backlog)

Automated foreground flow tests and camera/model acceptance follow this build slice.

## Spec self-review

Goals map to the acceptance checklist and script/native checks. QA identity and
HTTP settings are scoped to the new variant. Existing scientific and deployment
gates remain independent of successful builds.

## Related documents

- Plan: `docs/superpowers/plans/2026-10-31-android-qa-build.md`.
- Naming: `docs/glossary.md`; Git: `docs/git-workflow.md`.
- Android variants: https://developer.android.com/build/build-variants
