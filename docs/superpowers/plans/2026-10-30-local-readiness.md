# Local Readiness — Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to execute this approved documentation slice. Track completed steps below.

**Goal:** Reconcile local setup and readiness statements with recorded implementation and CI evidence.

**Architecture:** Update documentation from current source, merged PR checks, and dated runtime evidence. Preserve historical observations and separate unrun acceptance checks from completed work.

**Tech Stack:** Markdown, Git, GitHub CLI, Python structure verifier.

**Spec:** `docs/superpowers/specs/2026-10-30-local-readiness-design.md`

## Global Constraints

- Follow project standards and git workflow; work on `docs/local-readiness`.
- Conventional Commits; no secrets, generated artifacts, or application changes.
- Keep Oracle staging deferred at the user's request and preserve all data-quality holds.
- Verify structure and whitespace; package suites apply only if package code changes.

### Task 1: Verify evidence

**Files:** Read `README.md`, `PLAN.md`, `docs/project-status.md`, and `docs/mobile-runtime-smoke-test.md`.

**Interfaces:** Consume current source paths, PR #77/#78 evidence, and main CI results; produce dated, attributable status statements.

- [x] Inspect branch and confirm the primary checkout's edit is excluded.
- [x] Read current main CI and PR #77 checks with GitHub CLI.
- [x] Compare Windows setup's created environment with subsequent commands.

### Task 2: Reconcile documentation

**Files:** Modify `README.md`, `PLAN.md`, `docs/project-status.md`, and `docs/mobile-runtime-smoke-test.md`.

**Interfaces:** No application interface changes; keep existing endpoint names and evidence rows.

- [x] Replace the three Windows `../.venv` executable paths with `.venv` paths after entering `backend`.
- [x] Describe mobile's foreground nearby alerts and offline cache scope.
- [x] Replace pending PHIVOLCS CI claims with PR #77's five successful checks.
- [x] Record PR #78's bounded simulator layout evidence and main CI checkpoint.
- [x] Record staging deferral and order the remaining local checks by prerequisites.

### Task 3: Verify and submit

**Files:** Review all changed documentation and this plan.

**Interfaces:** Produce a focused PR against `main`, including actual verification and remaining runtime gates.

- [x] Run `python scripts/verify_structure.py` (expect 140 scaffold paths).
- [x] Run `git diff --check` (expect exit 0) and review the complete diff.
- [x] Confirm no application files or primary checkout edits changed.
- [x] Commit with `docs: reconcile local readiness and project status`.
- [ ] Push `docs/local-readiness`, open a PR, and inspect required checks before merge consideration.

## Notes for the executor

No new tests are needed for prose corrections. Validate executable paths against setup layout; a successful structure check does not establish a running API. Resume API/ingestion checks when Docker works and device flows when hardware is connected. Do not record these missing prerequisites as product test failures.
