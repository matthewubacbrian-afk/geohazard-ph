# Kaggle credential integration — Implementation Plan

> **For agentic workers:** Use the subagent-driven-development or executing-plans skill task by task. Steps use checkboxes for tracking.

**Goal:** Integrate the existing Kaggle `.env` credential loader into current main with consistent operator documentation and no change to the held profile artifact.

**Architecture:** Merge the reviewed feature branch from PR #32 into this new isolated branch, resolve current-main conflicts, correct the runbook contradiction, and verify the resulting ML and repository behavior before a replacement PR. Leave PR #32's worktree untouched.

**Tech Stack:** Python 3.11+, pytest, Ruff, Markdown, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-14-kaggle-dotenv-credentials-design.md` (arrives with the PR #32 branch).

## Global Constraints

- Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Preserve non-empty shell-variable precedence, `~/.kaggle/kaggle.json` fallback, and safe credential errors. Do not print, commit, or transmit credential values.
- Do not download datasets, retrain models, export risk profiles, or clear the current Epic 5 quality hold.
- Use Conventional Commits. Run ML `pytest -v` and Ruff, remaining package checks, structure verification, `git diff --check`, and all five PR CI checks.

---

### Task 1: Integrate the existing loader

**Files:**
- Merge: `fix/kaggle-dotenv-loader` code, tests, spec, and setup documents from PR #32.
- Resolve if needed: `README.md`, `docs/data-sources.md`, `ml/src/ml/ingest_kaggle.py`, and `ml/tests/test_ingest_kaggle.py` against current main.

**Interfaces:**
- Consumes: `download_datasets` in `ml/src/ml/ingest_kaggle.py` and the existing repository-root `.env` format.
- Produces: the PR #32 `_load_dotenv_credentials(env_path: Path | None = None) -> None` behavior without changing training/export contracts.

- [x] **Step 1:** inspected PR #32's diff and history; no secrets entered the tracked diff.
- [x] **Step 2:** merged the feature branch without editing its other worktree; the README auto-merged with current main.
- [x] **Step 3:** focused credential tests passed 12/12, full ML tests 72/72, and ML Ruff passed. Independent review found two older tests depended on the developer's real `.env`; both now use a temporary root.
- [x] **Step 4:** committed the integration and compatibility fix in `4ebba4d9 feat: integrate kaggle dotenv credentials`.

### Task 2: Correct operator guidance and deliver

**Files:**
- Modify: `docs/runbook.md` — state repository-root `.env` support and shell precedence while retaining the quality hold and offline instructions.
- Modify: `PLAN.md`, `docs/project-status.md`, this plan, and the imported spec/plan acceptance checklists to match verified state.

**Interfaces:**
- Consumes: integrated loader behavior and current staging quality hold.
- Produces: one consistent credential setup path across README, data-source notes, and runbook.

- [x] **Step 1:** corrected the contradictory runbook paragraph to match the loader's shell, root `.env`, and Kaggle config precedence.
- [ ] **Step 2:** run all package verification, structure and whitespace checks; obtain independent review.
- [ ] **Step 3:** commit docs, push, and open a replacement PR with actual evidence; close PR #32 only after the replacement has merged.
- [ ] **Step 4:** require five green CI checks, merge, verify exact head in remote main, and remove this worktree/branch.

## Notes for the executor

- PR #32 is open at `62fb24a5` and its existing worktree belongs to another feature stream. This branch starts at main `a31197b0` and will merge that history without rewriting or force-pushing PR #32.
- The current `docs/runbook.md` says the trainer does not load `.env`; that sentence will be false after integration.
- No OCI host, PHIVOLCS permission, domain-reviewed risk-profile policy, or device evidence was newly supplied. Preserve all external holds.
