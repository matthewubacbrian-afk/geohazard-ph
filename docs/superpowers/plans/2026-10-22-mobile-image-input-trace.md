# Mobile Image Input Trace — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record whether Node processes in the exact Android and iOS Release builds call `image-size`, and identify the supplied input shape without storing raw asset bytes.

**Architecture:** Preload a small CommonJS observer only during each existing Release command. It records `image-size` module loads and calls in temporary JSONL files, then a separate summarizer correlates process and worker-thread IDs with V8 coverage and requires an executed Metro build function. Upload only a compact report; leave the audited Release-report and five-package process-summary formats unchanged.

**Tech Stack:** Node 22, React Native 0.75.5/Metro 0.80.12, GitHub Actions, Python 3, pytest, Node's built-in test runner.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`; use Conventional Commits.
- Preserve the 34-row PR #65 audit as a dated baseline. GitHub subsequently withdrew the `braces` and `sprintf-js` advisories, so PR #66's live audit returns 12 rows. Keep every current row `undetermined`; do not treat a withdrawal or zero-call observation as proof of safety, device absence, or all future/generated input paths.
- Keep raw bytes, raw coverage, JSONL, binaries, and caches outside Git. Do not persist absolute host paths or input content in uploaded artifacts.
- Require a Metro build sentinel and matching V8 coverage and observer activation for every scoped Node thread before reporting an absence of calls. Fail the summary on malformed or out-of-scope records.
- Preserve the five exact-head CI jobs and compare both Release reports and existing process summaries with PR #65 before merging. The user approved a documented audit-only baseline change after the two advisory withdrawals; require all other fields to match except the Android APK hash.

### Task 1: Observe bounded `image-size` inputs

**Files:**
- Create: `scripts/mobile_image_input_observer.cjs`
- Test: `scripts/tests/test_mobile_image_input_observer.cjs`

**Interfaces:** A preload hook reads an output directory from `GEOHAZARD_IMAGE_INPUT_TRACE_DIR`, intercepts the pinned CommonJS `image-size` export through its package name or resolved path, and writes JSONL module-load and call records with process and worker-thread IDs. Call records distinguish path, `Uint8Array`, and invalid arguments. They include a byte count and SHA-256 of observed bytes (for paths, the parser's at-most-512-KiB read window), a bounded signature class, and a coarse origin class; they never include raw bytes or absolute paths. The wrapped function retains the original return, throw, callback, and exported properties.

- [x] **Step 1: Write focused tests** for path/buffer inputs, supported-suffix files with JXL/HEIF/ICNS prefixes, exported properties, thrown errors, and recording failure; run to see expected failures.
- [x] **Step 2: Implement the preload observer** with fail-closed record writes and deterministic event fields; rerun the focused tests.
- [x] **Step 3: Commit** the tested observer with `feat: observe mobile image parser inputs`.

### Task 2: Correlate calls with the exact Release packager

**Files:**
- Create: `scripts/mobile_image_input_summary.py`
- Test: `scripts/tests/test_mobile_image_input_summary.py`
- Modify: `.github/workflows/mobile-ci.yml`
- Test: `scripts/tests/test_mobile_ci_workflow.py`

**Interfaces:** The summarizer consumes the temporary JSONL directory, existing V8 coverage directory, and `mobile/node_modules` root. It accepts validated records from covered Release Node process/thread pairs, distinguishes Metro build threads from other Release threads, and compares observed parser calls with V8's parser execution count. It reports validated module loads and calls by input kind/origin/signature in a compact JSON artifact per platform. It fails if the Metro sentinel, coverage match, observer activation, or parser execution match is missing. The workflow sets `NODE_OPTIONS` and the observer directory only for Android/iOS Release commands and uploads the compact report after the existing process summary.

- [x] **Step 1: Write failing tests** for process/thread correlation, zero calls with activation, malformed JSON, missing Metro execution, and out-of-install coverage paths.
- [x] **Step 2: Implement the summarizer** and make its focused tests pass.
- [x] **Step 3: Write a failing workflow test** for scoped preload/report wiring; add the Android and iOS steps and make it pass.
- [x] **Step 4: Commit** the tested summarizer and workflow with `feat: report release image parser inputs` (`140d2d60`).

### Task 3: Review evidence and integrate

**Files:**
- Create: `docs/mobile-image-input-trace-2026-10-24.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `PLAN.md`, `docs/project-status.md`, and this plan

**Interfaces:** Report only observed exact-head calls, input classes, and unresolved generated/external asset and device gates. Link both compact summaries and both unchanged-format Release reports. Preserve the historical 34-row evidence, explain the current 12-row live audit, and keep every current disposition undetermined.

- [x] **Step 1: Run** script tests, backend unit and ML tests/Ruff, mobile Jest/TypeScript, single-worker web tests/build, structure, root-aware links, and whitespace. Backend integration could not run locally without Docker; exact-head backend CI passed at `140d2d60`.
- [x] **Step 2: Obtain independent review** of observer behavior and evidence wording, correct findings, then commit and push the evidence. The reviewer found and verified fixes for a resolved-path observer bypass and stale present-tense advisory wording.
- [x] **Step 3: Require all five exact-head CI checks**, inspect both new summaries, compare the Android/iOS Release reports and existing process summaries with PR #65, and merge only if the gate passes. The final checks passed on `a80ecd85`; [PR #66](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/66) merged at `c398d31c`.
- [x] **Step 4: Verify main**, preserve ignored files, remove the clean worktree and merged branches, and correct post-merge tracking. The tested head is an ancestor of `origin/main`; 25 ignored cache/build directories were moved to a named preservation folder before worktree removal. This tracking correction is delivered in a separate docs-only PR.

## Notes for the executor

- Current tracked mobile entry/source has no image import, custom Metro asset rule, or asset-generation step; recheck these claims against the branch and exact CI commands.
- A path observation is a snapshot just before the parser's own read. Report that limit rather than claiming an atomic view of its bytes.
- Physical-device behavior, future external/generated assets, the New Architecture, supported framework migration, and Epic 5 approval remain separate gates.
