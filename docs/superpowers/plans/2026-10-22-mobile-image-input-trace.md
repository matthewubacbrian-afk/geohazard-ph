# Mobile Image Input Trace — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record whether the exact Android and iOS Release packager processes call `image-size`, and identify the supplied input shape without storing raw asset bytes.

**Architecture:** Preload a small CommonJS observer only during each existing Release command. It records `image-size` module loads and calls in temporary JSONL files, then a separate summarizer correlates their process IDs with the executed Metro build function in V8 coverage. Upload only a compact report; leave the audited Release-report and five-package process-summary formats unchanged.

**Tech Stack:** Node 22, React Native 0.75.5/Metro 0.80.12, GitHub Actions, Python 3, pytest, Node's built-in test runner.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`; use Conventional Commits.
- Keep all 34 advisory dispositions `undetermined`. A zero-call observation describes only these scoped builds; it cannot establish safety, device absence, or all future/generated input paths.
- Keep raw bytes, raw coverage, JSONL, binaries, and caches outside Git. Do not persist absolute host paths or input content in uploaded artifacts.
- Require a Metro build sentinel and correlate observer process IDs with that build before reporting an absence of calls. Fail the summary on malformed or out-of-scope records.
- Preserve the five exact-head CI jobs and compare both Release reports and existing process summaries with PR #65 before merging.

### Task 1: Observe bounded `image-size` inputs

**Files:**
- Create: `scripts/mobile_image_input_observer.cjs`
- Test: `scripts/tests/test_mobile_image_input_observer.cjs`

**Interfaces:** A preload hook reads an output directory from `GEOHAZARD_IMAGE_INPUT_TRACE_DIR`, intercepts only the pinned CommonJS `image-size` export, and writes one JSONL module-load or call record with PID. Call records distinguish path, `Uint8Array`, and invalid arguments. They include a byte count and SHA-256 of observed bytes (for paths, the parser's at-most-512-KiB read window), a bounded signature class, and a coarse origin class; they never include raw bytes or absolute paths. The wrapped function retains the original return, throw, callback, and exported properties.

- [x] **Step 1: Write focused tests** for path/buffer inputs, supported-suffix files with JXL/HEIF/ICNS prefixes, exported properties, thrown errors, and recording failure; run to see expected failures.
- [x] **Step 2: Implement the preload observer** with fail-closed record writes and deterministic event fields; rerun the focused tests.
- [x] **Step 3: Commit** the tested observer with `feat: observe mobile image parser inputs`.

### Task 2: Correlate calls with the exact Release packager

**Files:**
- Create: `scripts/mobile_image_input_summary.py`
- Test: `scripts/tests/test_mobile_image_input_summary.py`
- Modify: `.github/workflows/mobile-ci.yml`
- Test: `scripts/tests/test_mobile_ci_workflow.py`

**Interfaces:** The summarizer consumes the temporary JSONL directory, existing V8 coverage directory, and `mobile/node_modules` root. It accepts only validated records from PIDs whose coverage executed `metro/src/Server.js` `build`, reports observed module loads and calls by input kind/origin/signature, and emits a compact JSON artifact per platform. It fails if the Metro sentinel or observer activation is missing. The workflow sets `NODE_OPTIONS` and the observer directory only for Android/iOS Release commands and uploads the compact report after the existing process summary.

- [ ] **Step 1: Write failing tests** for PID correlation, zero calls with activation, malformed JSON, missing Metro execution, and out-of-install coverage paths.
- [ ] **Step 2: Implement the summarizer** and make its focused tests pass.
- [ ] **Step 3: Write a failing workflow test** for scoped preload/report wiring; add the Android and iOS steps and make it pass.
- [ ] **Step 4: Commit** the tested summarizer and workflow with `feat: report release image parser inputs`.

### Task 3: Review evidence and integrate

**Files:**
- Create: `docs/mobile-image-input-trace-2026-10-22.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `PLAN.md`, `docs/project-status.md`, and this plan

**Interfaces:** Report only observed exact-head calls, input classes, and unresolved generated/external asset and device gates. Link both compact summaries and both unchanged-format Release reports. Keep all 34 dispositions undetermined.

- [ ] **Step 1: Run** script tests, backend and ML tests/Ruff, mobile Jest/TypeScript, single-worker web tests/build, structure, root-aware links, and whitespace; state any local Docker integration gap.
- [ ] **Step 2: Obtain independent review** of observer behavior and evidence wording, correct findings, then commit and push the evidence.
- [ ] **Step 3: Require all five exact-head CI checks**, inspect both new summaries, compare the Android/iOS Release reports and existing process summaries with PR #65, and merge only if the gate passes.
- [ ] **Step 4: Verify main**, preserve ignored files, archive the clean worktree, remove merged branches, and correct post-merge tracking if necessary.

## Notes for the executor

- Current tracked mobile entry/source has no image import, custom Metro asset rule, or asset-generation step; recheck these claims against the branch and exact CI commands.
- A path observation is a snapshot just before the parser's own read. Report that limit rather than claiming an atomic view of its bytes.
- Physical-device behavior, future external/generated assets, the New Architecture, supported framework migration, and Epic 5 approval remain separate gates.
