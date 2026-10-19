# Mobile release-artifact exposure record — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate reproducible evidence about which npm advisory packages appear in a React Native release JavaScript source map and which native files ship in non-published Android and iOS app artifacts.

**Architecture:** A standard-library Python script reads a source map, npm audit JSON, and an Android APK or iOS `.app` directory, then writes a deterministic small JSON report. CI builds release variants and runs the script on the exact build outputs; no app binary, raw audit JSON, or source map is committed or uploaded. Package observations remain separate from exploitability conclusions.

**Tech Stack:** Python 3.11+, pytest, npm audit, React Native 0.75.5, Gradle, Xcode, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, `docs/git-workflow.md`, and `docs/glossary.md`.
- Do not change app behavior, package versions, platform minimums, signing, or native framework configuration in this slice.
- Keep raw source maps, audit JSON, APKs, `.app` output, and local caches outside Git. The report contains names, hashes, counts, and paths only; never embed bundle code or `sourcesContent`.
- A package path listed in a source map is evidence of bundled JavaScript source, not of an exploitable API. An unlisted package is not proven absent from compiled native code. Set advisory disposition to `undetermined` throughout.
- Run `pytest -v scripts/tests/test_mobile_artifact_inventory.py`, package suites and lint, `python scripts/verify_structure.py`, and `git diff --check`; require all five CI checks before merge.
- If the new release-build step fails, fix it on this branch or abandon the PR. If a merged workflow proves unreliable, revert this PR to restore the previous native CI configuration.

---

### Task 1: Write a failing inventory test

**Files:**
- Create: `scripts/tests/test_mobile_artifact_inventory.py`
- Create: `scripts/mobile_artifact_inventory.py`

**Interfaces:**
- CLI: `python scripts/mobile_artifact_inventory.py --platform android|ios --source-map PATH --artifact PATH --audit-json PATH --output PATH`.
- Output: deterministic JSON with `platform`, `artifact_sha256` (APK bytes or iOS `main.jsbundle` bytes), `source_map_sha256`, `bundle_path`, `native_entries`, `source_packages`, and `advisories`. Each advisory has `package`, `severity`, `source_map_observation` (`listed` or `not_listed`), `matched_source_count`, `dependency_paths`, and `disposition: undetermined`.

- [ ] **Step 1: Write synthetic tests** for a Metro source map, audit entries, an APK zip with a Hermes asset/native file, and an iOS `.app` with `main.jsbundle`/Frameworks.
- [ ] **Step 2: Run the focused test and verify it fails** because the inventory script does not yet exist.
- [ ] **Step 3: Implement source-map, audit, and artifact readers** with clear failures for missing/malformed inputs and no network or external packages.
- [ ] **Step 4: Run the focused test and verify it passes**; inspect the JSON for accidental source content or raw audit payload.
- [ ] **Step 5: Commit** tests and script with a Conventional Commit message.

---

### Task 2: Produce reports in native CI

**Files:**
- Modify: `.github/workflows/mobile-ci.yml`
- Modify: `scripts/tests/test_mobile_ci_workflow.py`
- Modify: `docs/mobile-dependency-audit-2026-10-19.md`, `docs/mobile-rn-migration-assessment-2026-10-20.md`, `PLAN.md`, `docs/project-status.md`, this plan

**Interfaces:**
- Android: `./gradlew assembleRelease` after existing debug build; use `android/app/build/generated/sourcemaps/react/release/index.android.bundle.map` and `android/app/build/outputs/apk/release/app-release.apk`.
- iOS: build an unsigned Release simulator `.app` with `SOURCEMAP_FILE` set outside the repository; locate exactly one app and its `main.jsbundle` from a fixed derived-data path.
- npm audit: run once per native job into a runner-temp JSON file; accept npm's finding exit code but reject invalid/empty JSON in the inventory script.
- Reports: write runner-temp JSON and upload only reports as CI artifacts with a short retention period.

- [ ] **Step 1: Add failing workflow-contract tests** for release builds, source-map inputs, and report upload without raw build products.
- [ ] **Step 2: Run the focused tests and verify the expected failure**.
- [ ] **Step 3: Add Android and iOS release inventory steps** while preserving the existing debug/test gates.
- [ ] **Step 4: Update the audit and status docs** with the exact evidence boundary and commands; do not claim a new audit count before CI reports exist.
- [ ] **Step 5: Run focused tests, package verification, structure and whitespace checks; request independent review**.
- [ ] **Step 6: Commit, push, and open a PR**; require all five green CI checks and inspect generated report artifacts before merge, verify the tested head on remote main, then remove worktree and branches.

## Notes for the executor

This is build-observation tooling, not a security scanner. A Metro source map names JS source modules, while APK/`.app` files show packaged assets and native files. Neither alone proves a vulnerability is exploitable or that all native code is absent. CI runners may resolve different advisory data from the 2026-10-19 snapshot; report that date and count separately. Do not publish or upload debug-signed release binaries.
