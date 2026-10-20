# Mobile fast-xml-parser Consumer Calls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace the pinned CLI-platform consumers of `fast-xml-parser` 4.5.7 to actual parser or builder calls and identify the origin of inputs relevant to GHSA-gh4j-gqv2-49f6, without overstating runtime reachability or changing advisory dispositions.

**Architecture:** Start from the merged PR #56 lockfile and Release evidence. Inspect the exact installed Android and iOS CLI-platform package versions, then document cited call sites and input provenance. Keep the other five advisory references in the later attack-path queue.

**Tech Stack:** Markdown, tracked npm lockfile, exact-version npm package source, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- This is a bounded documentation review. Do not alter dependencies, app behavior, release reports, or the 34 `undetermined` dispositions.
- Distinguish a lockfile edge from a call site, a call site from untrusted input, and build-host execution from distributed-device execution. Do not infer absence from source-map package names alone.
- Cite immutable exact-version source or verified package contents for every call-site claim. Record unresolved branches explicitly.
- Do not commit package tarballs, `node_modules`, raw audit JSON, source maps, bundles, APKs, or app directories.
- Verify structure, whitespace, applicable local checks, independent review, and all five exact-head CI checks before merge.

### Task 1: Trace the pinned consumers

**Files:**
- Create: `docs/mobile-fast-xml-parser-callsites-2026-10-20.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, the final PR #56 Android/iOS report identities, and exact package source for `@react-native-community/cli-platform-android` and `cli-platform-apple` at 14.1.0. Produce a table with consumer version, source file/function, `fast-xml-parser` API called, input origin, advisory operation match, and evidence limit.

- [x] **Step 1: Verify the pinned packages and direct advisory identity.** Both 14.1.0 CLI tarballs matched the lockfile SHA-512 integrity values; the tracked lockfile and PR #56 reports identify `fast-xml-parser` 4.5.7 and GHSA-gh4j-gqv2-49f6.
- [x] **Step 2: Inspect exact-version consumer source.** A recursive search of the published JavaScript found three direct import/use files, with `XMLParser`/`XMLValidator` and no direct `XMLBuilder` call in the two pinned CLI packages.
- [x] **Step 3: Trace input to each relevant call.** The cited functions read local manifest, workspace, or scheme files. Input control and other consumers remain unverified.
- [x] **Step 4: Publish the bounded review and link it from the existing advisory record.** All 34 findings remain `undetermined` and the other five direct references remain queued.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-20-mobile-advisory-paths.md`
- Modify: this plan

- [x] **Step 1: Mark PR #56 merged and cleaned up, then write this focused plan before investigation changes.** PR #56 merged at `29fa1a2e` after five checks; both final Release reports were inspected, and its worktree/branches were removed.
- [x] **Step 2: Verify the documentation and relevant package checks.** `git diff --check`, structure verification (140 paths), exact tarball integrity checks, the scripts suite (26 tests plus seven subtests), and backend/ML Ruff checks passed. CI remains the full package/native gate.
- [x] **Step 3: Commit, push, open one PR, and obtain independent review.** [PR #57](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/57) is open. Independent Astra review verified the exact-version source claims; its one stale-table finding was corrected before the PR opened.
- [ ] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** The next feature updates tracking before implementation.

## Notes for the executor

The advisory concerns `XMLBuilder` comment or CDATA delimiter handling, not every XML parse. A consumer's `XMLParser` call is useful path evidence but does not itself establish that operation is invoked. This slice does not authorize a build-only or exploitable classification, a dependency override, or release signoff.
