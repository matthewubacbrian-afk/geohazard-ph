# Mobile Advisory Attack-Path Reconciliation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile the six pinned mobile advisory references with their five bounded consumer-call reviews and record the exact unclosed input, execution, and artifact gates for each, without changing any disposition.

**Architecture:** Treat the lockfile, final PR #61 Android/iOS Release reports, advisory path review, and dated consumer-call reviews as separate evidence layers. Verify their counts and claims, then publish a compact gate matrix that says which calls were observed, which inputs remain untrusted or local, which process context is established, and what focused evidence is needed next. Update stale checklist language in the advisory record.

**Tech Stack:** Markdown, npm lockfile, final CI JSON reports, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- Preserve all 34 `undetermined` audit finding dispositions. A package, dependency edge, source-map entry, or missing map entry cannot establish build-only status, device reachability, or exploitability.
- Cite exact dated source reviews and distinguish all six direct advisory references from the 34 inherited-chain findings. State each unverified indirect call and input origin rather than treating a bounded negative observation as exhaustive.
- Keep this as a documentation/evidence slice. Do not change dependencies, app behavior, CI report generation, or scientific/release gates. Do not commit raw audit payloads, source maps, bundles, app binaries, or tarballs.
- Verify structure, whitespace, local documentation checks, independent review, and all five exact-head CI checks. Inspect both final Release reports before merge.

### Task 1: Reconcile advisory gates

**Files:**
- Create: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, the PR #61 Android/iOS `mobile-artifact-report` JSON, `docs/mobile-advisory-exposure-review-2026-10-20.md`, and the five dated `mobile-*-callsites` reviews. Produce one row per direct GHSA reference with installed version, observed affected-operation call or boundary, format/pattern/asset/certificate input origin, established process context, remaining untrusted-input/artifact gate, and a precise next evidence action.

- [x] **Step 1: Verify inventory.** Confirm five directly affected installed packages, six direct advisory references, 34 audit entries per platform (29 with inherited links), package versions, and unchanged report dispositions.
- [x] **Step 2: Reconcile source reviews.** Compare each dated consumer finding to the advisory's operation and input precondition. Distinguish observed call, observed non-call in a bounded consumer, and uninspected indirect consumers.
- [x] **Step 3: Record gate matrix.** State the minimum input-to-operation-to-process evidence needed for a disposition; prioritize the next bounded evidence slice without claiming full reachability or safety.
- [x] **Step 4: Refresh advisory checklist.** Mark source-call inspection as completed only for the bounded direct consumers reviewed; keep indirect paths, runtime/device attribution, and post-migration verification open.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-21-mobile-sprintf-js-callsites.md`
- Modify: this plan

- [x] **Step 1: Mark PR #61 merged and cleaned up, then commit this focused plan before investigation changes.** PR #61 merged at `ed13a9cd` after five exact-head checks and inspection of both final reports; its tested head is on remote main and the worktree and branches were removed.
- [x] **Step 2: Verify documentation and available checks.** `git diff --check`, 140-path structure verification, script tests (26 plus 7 subtests), backend/ML Ruff, local-link checks, and both final PR #61 report inventories passed. CI is the full package/native gate.
- [ ] **Step 3: Commit, push, open one PR, and obtain independent review.** Keep findings factual and scoped.
- [ ] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** Update tracking before the next feature.

## Notes for the executor

This matrix is an evidence handoff for focused build/runtime path tests and the supported framework migration. It cannot itself close an advisory or authorize release. If a direct call is absent from one inspected consumer, record that narrow result and preserve indirect-call uncertainty.
