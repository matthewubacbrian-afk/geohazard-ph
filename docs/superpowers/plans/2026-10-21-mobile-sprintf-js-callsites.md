# Mobile sprintf-js Consumer Calls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace the pinned mobile production dependency paths to `sprintf-js` 1.0.3 and actual formatting calls and input origins relevant to GHSA-hp3w-g68c-fv3c, without changing advisory dispositions.

**Architecture:** Reconcile the lockfile's multiple `cosmiconfig`, `js-yaml`, and `argparse` versions before attributing calls. Verify exact published tarballs against SHA-512 integrity values, inspect the affected `sprintf-js` operation and its direct/indirect consumers, then publish a bounded source review that separates an installed package from a reachable attacker-controlled format string.

**Tech Stack:** Markdown, npm lockfile and exact-version package tarballs, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- This is an evidence review. Do not change dependencies, app behavior, Release reports, or any of the 34 `undetermined` dispositions.
- A lockfile edge, package name in a source map, or configuration-file path alone does not establish use of the vulnerable formatting operation or attacker control of its format string.
- Cite the exact affected version and verified published source. Preserve distinctions between production and development-only dependency paths and between top-level and nested package versions.
- Do not commit tarballs, `node_modules`, raw audit JSON, source maps, bundles, APKs, or app directories.
- Verify structure, whitespace, available local checks, independent review, and five exact-head CI checks before merge; inspect final Android and iOS Release reports.

### Task 1: Trace pinned formatter consumers

**Files:**
- Create: `docs/mobile-sprintf-js-callsites-2026-10-21.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, the final PR #60 Android/iOS advisory identities, the GHSA-hp3w-g68c-fv3c affected operation, and SHA-512-verified published `sprintf-js` 1.0.3, `argparse` 1.0.10, `js-yaml` 3.15.2, Metro's nested `cosmiconfig` 5.2.1, and any other direct pinned consumers found. Produce a table of exact caller, formatting API, format-string origin, affected-operation relationship, and evidence limit.

- [x] **Step 1: Verify versions and advisory.** Enumerate all production lockfile paths to `sprintf-js`; distinguish nested newer parser/configuration copies.
- [x] **Step 2: Inspect exact-version source.** Verify published tarball integrity, inspect `sprintf-js` affected operation and every direct published caller found in the pinned path.
- [x] **Step 3: Trace inputs.** Follow format strings through the observed CLI/configuration calls; distinguish fixed strings, local configuration or file contents, and potentially untrusted input. State unverified indirect paths or runtime contexts.
- [x] **Step 4: Publish the bounded review and link the advisory record.** Keep the `sprintf-js` reference and all 34 finding dispositions `undetermined` unless a separately reviewed full attack path supports a change.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-21-mobile-braces-callsites.md`
- Modify: this plan

- [x] **Step 1: Mark PR #60 merged and cleaned up, then commit this focused plan before investigation changes.** PR #60 merged at `b10296a2` after five exact-head checks and inspection of both final reports; its tested head is on remote main and the worktree and branches were removed.
- [x] **Step 2: Verify documentation and available checks.** `git diff --check`, 140-path structure verification, SHA-512 package integrity, production lockfile graph, the pinned precision probe, script tests (26 plus 7 subtests), and backend/ML Ruff passed. CI is the full package/native gate.
- [ ] **Step 3: Commit, push, open one PR, and obtain independent review.** Record only exact-version-supported claims.
- [ ] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** The next feature updates tracking before implementation.

## Notes for the executor

The top-level `cosmiconfig` 9.0.2 uses a nested `js-yaml` 4.3.2 and `argparse` 2.0.1. Metro's nested `cosmiconfig` 5.2.1 and the top-level `js-yaml` 3.15.2 / `argparse` 1.0.10 require separate call-path inspection. Do not generalize across these versions or classify a finding from the shortest dependency path alone.
