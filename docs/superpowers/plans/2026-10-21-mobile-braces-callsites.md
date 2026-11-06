# Mobile braces Consumer Calls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace the pinned React Native production-graph consumers of `braces` 3.0.3 to actual pattern calls and input origins relevant to GHSA-vfj7-8cjw-p6xm without changing advisory dispositions.

**Architecture:** Fix versions and paths from the merged lockfile and PR #59 Release reports. Inspect SHA-512-verified published packages in the CLI, Metro file-map, codegen, and Jest chains, labeling supplemental development-only consumers separately, then publish one bounded call-path record that distinguishes an attacker-supplied deep brace pattern from a static or local build pattern.

**Tech Stack:** Markdown, npm lockfile and exact-version package tarballs, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- This is an evidence review. Do not change dependencies, application behavior, Release reports, or any of the 34 `undetermined` dispositions.
- The [advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) affects recursive brace-pattern processing, not every use of a glob library. An installed package or a method name is not proof that a sufficiently deep untrusted pattern reaches the vulnerable walker.
- Cite exact-version source or SHA-512-verified package contents. State any uninspected path, indirect call, attacker-control, or device-inclusion limit.
- Do not commit tarballs, `node_modules`, raw audit JSON, source maps, bundles, APKs, or app directories.
- Verify structure, whitespace, available local checks, independent review, and five exact-head CI checks before merge.

### Task 1: Trace pinned pattern consumers

**Files:**
- Create: `docs/mobile-braces-callsites-2026-10-21.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, the final PR #59 Android/iOS advisory identities, and exact published `braces` 3.0.3, `micromatch` 4.0.8, `fast-glob` 3.3.3, Metro file-map 0.80.12, and observed CLI/codegen/Jest callers. Produce a table of caller file/function, glob or pattern API, pattern origin, relationship to nested-brace processing, and evidence limit.

- [x] **Step 1: Verify versions and advisory.** Reproduce all observed production lockfile paths to `braces` and the affected operation in GHSA-vfj7-8cjw-p6xm.
- [x] **Step 2: Inspect exact-version source.** Verify inspected package tarballs against lockfile SHA-512 values; find `micromatch`/`braces` uses in the published consumers, including indirect `fast-glob` paths.
- [x] **Step 3: Trace pattern inputs.** Distinguish fixed package patterns, local project/configuration values, and any user-supplied values. State when an untrusted deeply nested pattern or execution path cannot be established.
- [x] **Step 4: Publish the bounded review and link it from the advisory record.** Keep the `braces` reference and all 34 finding dispositions `undetermined`.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-20-mobile-node-forge-callsites.md`
- Modify: this plan

- [x] **Step 1: Mark PR #59 merged and cleaned up, then write this focused plan before investigation changes.** PR #59 merged at `61f85055` after five exact-head checks; both final reports were inspected, and its worktree/branches were removed.
- [x] **Step 2: Verify documentation and available checks.** Run `git diff --check`, structure verification, source/lockfile consistency checks, and configured local suites. CI is the full package/native gate.
- [x] **Step 3: Commit, push, open one PR, and obtain independent review.** [PR #60](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/60) contains the corrected review; independent review found and resolved a production-versus-development lockfile labeling issue.
- [x] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** PR #60 merged at `b10296a2`; the final reports were inspected and the tested head is on remote main. The worktree and branches were removed.

## Notes for the executor

`braces` has multiple inherited lockfile paths and no patched release listed by the advisory as of this review date. This slice does not authorize a build-only or exploitable classification, a dependency override, or release signoff. If the published consumers have additional paths, record them instead of claiming exhaustive coverage from the shortest path alone.
