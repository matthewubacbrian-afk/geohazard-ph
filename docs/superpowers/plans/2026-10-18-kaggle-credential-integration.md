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
- [x] **Step 2:** local ML suite, Ruff, structure and whitespace checks passed; independent review's test-isolation finding was fixed; PR CI passed for backend, ML, web, mobile/Android, and iOS.
- [x] **Step 3:** committed docs in `57548fbf`, pushed, and opened PR #43 with verification evidence. GitHub marked PR #32 merged automatically when its history landed through PR #43.
- [x] **Step 4:** all five checks passed; PR #43 merged at `5877a0c8`, exact head `57548fbf` was verified in remote main, and both merged worktrees/branches were removed.

## Notes for the executor

- PR #32 at `62fb24a5` was incorporated into PR #43's merge history. Its branch and worktree were removed only after merge and clean-state verification.
- The runbook's old claim that the trainer does not load `.env` was corrected in the integration merge.
- No OCI host, PHIVOLCS permission, domain-reviewed risk-profile policy, or device evidence was newly supplied. Preserve all external holds.
