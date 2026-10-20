# Mobile Advisory Identities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Attach exact installed versions and direct advisory references to each non-published mobile Release inventory finding.

**Architecture:** Extend the existing inventory script with a required lockfile input. Match npm audit node paths to lockfile package entries and preserve direct `via` references separately from inherited package links. Keep all dispositions undetermined.

**Tech Stack:** Python standard library, pytest, GitHub Actions, React Native release builds.

**Spec:** `docs/superpowers/specs/2026-10-20-mobile-advisory-identities-design.md`

## Global constraints

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.
- Do not upload or commit raw audit JSON, source maps, bundles, APKs, `.app` output, secrets, or large datasets.
- Use Conventional Commits. Run `python scripts/verify_structure.py`, `git diff --check`, all four package suites, Ruff, web build, mobile TypeScript, and the five CI checks.
- A package-name observation is not an exploitability conclusion.

### Task 1: Add failing evidence tests

**Files:**
- Modify: `scripts/tests/test_mobile_artifact_inventory.py`
- Modify: `scripts/tests/test_mobile_ci_workflow.py`

**Interfaces:** Existing `_inputs` fixture gains a lockfile path; `build_report` gains a fifth path argument. Expected advisory fields are `installed_nodes`, `via_packages`, and `advisory_references`.

- [ ] **Step 1: Add a minimal `packages` lockfile fixture with `node_modules/image-size` version `1.2.1` and `node_modules/metro` version `0.75.5`; include direct `via` source `12345`, HTTPS URL, and range `<=1.2.1`.** Assert direct and inherited rows exactly, including empty arrays for the opposite evidence type.
- [ ] **Step 2: Add cases for a missing audit node in the lockfile, missing version, malformed `via` entry, and invalid advisory URL.** Each must raise `ValueError` mentioning the finding package.
- [ ] **Step 3: Assert both workflow invocations pass `--lockfile mobile/package-lock.json`.**
- [ ] **Step 4: Run `python -m pytest scripts/tests/test_mobile_artifact_inventory.py scripts/tests/test_mobile_ci_workflow.py -q`; verify failure from the missing fifth argument/fields before implementation.**

### Task 2: Implement deterministic evidence enrichment

**Files:**
- Modify: `scripts/mobile_artifact_inventory.py`
- Modify: `.github/workflows/mobile-ci.yml`

**Interfaces:** `build_report(platform, source_map_path, artifact_path, audit_json_path, lockfile_path)`; required CLI `--lockfile`.

- [ ] **Step 1: Read the lockfile as a JSON object and require a `packages` object.** Resolve each audit node exactly, rejecting missing or non-string versions.
- [ ] **Step 2: Parse every `via` entry.** Strings become sorted `via_packages`; direct objects become sorted dictionaries containing `source`, `url`, and `range`. Reject unsupported/malformed entries. Do not copy title, CVSS, or raw audit payload.
- [ ] **Step 3: Add `--lockfile mobile/package-lock.json` to both platform inventory commands.**
- [ ] **Step 4: Rerun the focused tests, full `scripts/tests`, configured Ruff, structure and whitespace checks.**
- [ ] **Step 5: Commit the implementation and tests with `feat: record mobile advisory identities`.**

### Task 3: Verify, review, and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/mobile-artifact-evidence-2026-10-20.md`
- Modify: this plan

- [ ] **Step 1: Record PR #54 as merged and describe the new fields without classifying findings.** Keep shortest root paths and affected-API review in the queue.
- [ ] **Step 2: Run full backend/ML `pytest -v` and Ruff, web `npm test`/`npm run build`, mobile Jest/TypeScript, Python script tests, structure verification, and `git diff --check`.**
- [ ] **Step 3: Get an independent code review, fix actionable findings, commit, push, and open one PR.**
- [ ] **Step 4: Wait for all five exact-head CI checks, download both reports, and verify every finding has version plus direct reference or inherited link; inspect disposition counts.**
- [ ] **Step 5: Merge only on success; confirm tested head on remote main, remove this worktree and branch, and update current tracking for the next feature.**

## Notes for the executor

The `nodes` values are installed locations, not a shortest root dependency path. A chain finding may have no direct advisory object; its `via_packages` link must remain visible. The output is evidence for later manual review, never a risk disposition.
