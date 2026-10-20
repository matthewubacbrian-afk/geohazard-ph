# Mobile Advisory Paths Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a reproducible, source-linked review of the six direct mobile advisories' dependency paths and affected-operation preconditions without making unsupported risk conclusions.

**Architecture:** Use the final PR #55 Release reports for IDs and installed versions, npm's lockfile-only production tree for root paths, and the GitHub Advisory Database for operation descriptions. Write a dated review record and synchronize Epic 4 tracking.

**Tech Stack:** Markdown, npm lockfile inspection, GitHub Actions verification.

**Spec:** `docs/superpowers/specs/2026-10-20-mobile-advisory-paths-design.md`

## Global constraints

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, and `docs/testing-standards.md`; use Conventional Commits.
- Preserve all 34 `undetermined` dispositions. Do not treat an absent JavaScript source-map name as proof of absence from native or build outputs.
- Do not commit raw npm audit/tree JSON, source maps, bundles, APKs, `.app` directories, credentials, or large datasets.
- Run structure and whitespace checks, applicable package verification, independent review, and all five exact-head CI checks.

### Task 1: Record the paths and preconditions

**Files:**
- Create: `docs/mobile-advisory-exposure-review-2026-10-20.md`
- Modify: `docs/mobile-artifact-evidence-2026-10-20.md`
- Modify: `docs/mobile-dependency-audit-2026-10-19.md`

**Interfaces:** The review table has package, installed version, GHSA link, shortest observed root path, affected operation/input, and evidence limit. The six IDs are GHSA-vfj7-8cjw-p6xm, GHSA-gh4j-gqv2-49f6, GHSA-5p2g-fcmc-qvqq, GHSA-w3rx-r6r6-pgpr, GHSA-86w9-cpqp-85rv, and GHSA-hp3w-g68c-fv3c.

- [ ] **Step 1: Recheck the final PR #55 Android/iOS JSON reports.** Confirm 34 rows each, installed versions, five directly affected packages, six direct references, and undetermined dispositions.
- [ ] **Step 2: Run `npm ls braces fast-xml-parser image-size node-forge sprintf-js --omit=dev --package-lock-only --all --json` from `mobile/`.** Record the shortest `react-native` root path per affected package; note both `fast-xml-parser` paths.
- [ ] **Step 3: Read the six GitHub Advisory Database pages.** Record the vulnerable operation and required input for each, with direct links and affected ranges.
- [ ] **Step 4: Write the dated review and link it from the artifact and dependency audit records.** State that package names, npm paths, and operation preconditions do not establish app reachability; leave affected API calls and untrusted input unresolved.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-20-mobile-advisory-identities.md`
- Modify: this plan

- [ ] **Step 1: Mark PR #55 merged at `bed6c572` after five checks and both report inspections.** Keep per-advisory API/attack-path review and migration/device gates open.
- [ ] **Step 2: Verify `git diff --check`, `python scripts/verify_structure.py`, report/ID/path consistency, and relevant package suites and linters.** Full CI remains the merge gate if local Docker/npm installation is unavailable.
- [ ] **Step 3: Commit the documentation with `docs: record mobile advisory paths`, push this branch, open one PR, and obtain independent review.**
- [ ] **Step 4: Require five exact-head CI checks, merge, verify the tested head on remote main, and remove the worktree and branches.** Update the next feature's plan/status first before implementing its code.

## Notes for the executor

`npm ls --package-lock-only` describes the lockfile graph. The Release source map and selected native-file inventory remain separate observations; neither can prove a vulnerable operation is invoked from a distributed device app. The next review must inspect actual consumer call sites and untrusted-input paths before changing any disposition.
