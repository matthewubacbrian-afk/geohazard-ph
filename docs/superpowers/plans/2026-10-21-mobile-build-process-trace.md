# Mobile Release Build Process Trace — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record which directly affected Node package files and named functions execute during the existing non-published Android/iOS Release builds, without changing advisory dispositions.

**Architecture:** Enable Node's built-in V8 coverage only for each native Release command, summarize the generated per-process JSON with a small Python script, and upload separate compact artifacts. Keep existing release-inventory generation and schema unchanged.

**Tech Stack:** GitHub Actions, Node 22 V8 coverage, Python 3, pytest, React Native 0.75.5.

**Spec:** `docs/superpowers/specs/2026-10-21-mobile-build-process-trace-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`,
  and `docs/git-workflow.md`; use Conventional Commits.
- Keep all 34 audit dispositions `undetermined`. A missing V8 entry or
  function name does not establish safety, build-only status, or device absence.
- Do not commit raw coverage, app build artifacts, caches, or secrets.
- Preserve the five exact-head CI jobs and compare both final Release reports
  with PR #63 before merge.

### Task 1: Implement the bounded coverage summarizer

**Files:**
- Create: `scripts/mobile_process_coverage.py`
- Test: `scripts/tests/test_mobile_process_coverage.py`

**Interfaces:** `build_report(platform, coverage_dir, node_modules_root)`
returns `platform`, `coverage_file_count`, and `packages` keyed by the five
direct names. Each package has `loaded_files` and `executed_functions`, where
each function has `path`, `name`, and `start_offset`. Paths are relative to
the requested `node_modules` root.

- [ ] **Step 1: Write tests for import-only and called-function coverage.**
      A module-wrapper entry counts as loaded; a nonempty named function with
      positive entry count is listed; zero-count functions are omitted.
- [ ] **Step 2: Run focused pytest and see the missing-module failure.**
- [ ] **Step 3: Implement parsing, path validation, deterministic sorting,
      and the four-argument CLI.**
- [ ] **Step 4: Run focused pytest; add malformed/no-file and nested-path
      cases, observe failures first, then pass them.**
- [ ] **Step 5: Commit the tested summarizer and tests.**

### Task 2: Capture the exact CI Release process

**Files:**
- Modify: `.github/workflows/mobile-ci.yml`
- Test: `scripts/tests/test_mobile_ci_workflow.py`

**Interfaces:** Android/iOS build steps set platform-specific
`NODE_V8_COVERAGE` under `$RUNNER_TEMP`. A following step runs the
summarizer with `mobile/node_modules` and uploads
`mobile-process-trace-android`/`mobile-process-trace-ios` JSON.

- [ ] **Step 1: Add a workflow test for both scoped Release environments and
      report uploads; run it and observe failure.**
- [ ] **Step 2: Modify only the Release steps and add report/upload steps.**
- [ ] **Step 3: Run workflow and script tests; commit the workflow change.**

### Task 3: Review actual CI evidence and integrate

**Files:**
- Create: `docs/mobile-build-process-trace-2026-10-21.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `PLAN.md`, `docs/project-status.md`, and this plan

**Interfaces:** Consume both exact-head coverage artifacts and both final
Release reports; state positive observations, absences within this run, and
unresolved attack-path/device gates.

- [ ] **Step 1: Verify local package suites, TypeScript, Ruff, structure,
      links, and `git diff --check`; obtain independent wording/code review.**
- [ ] **Step 2: Push one PR, require all five exact-head checks, inspect both
      process reports, and compare Android/iOS Release JSON to PR #63.**
- [ ] **Step 3: Commit the dated evidence and tracking updates, rerun the
      exact-head gate, then merge only if still green.**
- [ ] **Step 4: Verify the tested head on remote main; archive only a clean,
      ignored-file-free worktree and remove merged branches.**

## Notes for the executor

V8 coverage reports JavaScript function-entry counts in Node processes that
receive the environment variable. It does not capture arguments, a process's
trust boundary, native calls, or device execution. An anonymous top-level
function shows module evaluation, not use of the affected parser. Keep those
claims separate in both JSON interpretation and prose.
