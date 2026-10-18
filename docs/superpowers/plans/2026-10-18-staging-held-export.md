# Staging held-export mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permit a staging release while the regional risk-profile export remains on quality hold, without publishing fixture or held data.

**Architecture:** Keep `RISK_PROFILE_EXPORT_PATH` pointed at `/data/risk_profiles.json` in the API, where the production image has no bundled fixture. The base Compose file has no profile bind mount, so the existing list endpoint returns `[]`. A separate Compose override adds a read-only bind mount only after a reviewed export exists; the deploy script requires an explicit `--with-profile` flag to use it and checks that the API returns a non-empty list. The default deployment checks for the empty list.

**Tech Stack:** Docker Compose, Bash, Python standard library, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/git-workflow.md`, `docs/testing-standards.md`, and the glossary.
- Do not transfer or serve the current held export. A passing config check does not clear the Epic 5 domain review.
- Keep the production backend image free of `backend/tests/fixtures`; do not change the API contract.
- Use Conventional Commits. Run Compose validation, the staging verifier, backend and ML `pytest -v`, web and mobile tests/builds/checks, Ruff, `python scripts/verify_structure.py`, and `git diff --check` before PR.

### Task 1: Make both Compose modes explicit

**Files:**
- Modify: `compose.staging.yml`, `.env.staging.example`
- Create: `compose.staging.profile.yml`, `scripts/verify_staging_config.py`
- Modify: `.github/workflows/backend-ci.yml`, `.github/workflows/deploy-staging.yml`

**Interfaces:**
- Base: `docker compose --env-file .env.staging.example -f compose.staging.yml config --format json` has no API profile volume and keeps `RISK_PROFILE_EXPORT_PATH=/data/risk_profiles.json`.
- Reviewed mode: add `-f compose.staging.profile.yml`; it requires `RISK_PROFILE_EXPORT_FILE`, mounts that host file read-only at `/data/risk_profiles.json`, and disables implicit host-path creation.
- `python scripts/verify_staging_config.py` validates both rendered models and fails on a missing or accidental base mount.

- [x] **Step 1: Write the failing verification script** that renders each mode to JSON and asserts the exact API environment and volume properties.
- [x] **Step 2: Run `python scripts/verify_staging_config.py` and verify failure against the current mandatory mount.**
- [x] **Step 3: Remove the base profile mount, add the opt-in override, and make the example export path commented and review-gated.**
- [x] **Step 4: Rerun the verifier and `docker compose ... config --quiet` for both modes.**
- [x] **Step 5: Include the override in the release bundle and run the verifier in the staging workflow. Commit with a focused Conventional Commit.**

### Task 2: Deploy and verify the selected mode

**Files:**
- Modify: `scripts/deploy_staging.sh`
- Create: `scripts/tests/test_deploy_staging.py`

**Interfaces:**
- `bash scripts/deploy_staging.sh <sha> <https-url>` deploys without an export and requires the profile endpoint's JSON to equal `[]`.
- `bash scripts/deploy_staging.sh <sha> <https-url> --with-profile` adds the override and requires a non-empty JSON list.
- Invalid flags and response shapes fail the deployment check; tests use stub `docker` and `curl`, with no live host or image pulls.

- [x] **Step 1: Write script tests for default mode, opt-in mode, invalid flag, and mismatched profile response.**
- [x] **Step 2: Run `python -m unittest discover -s scripts/tests -p 'test_deploy_staging.py' -v` and confirm expected failures.**
- [x] **Step 3: Implement mode selection and JSON response checks in the deploy script.**
- [x] **Step 4: Rerun the focused tests and shell syntax validation; commit the script and tests.**

### Task 3: Align operator guidance and project tracking

**Files:**
- Modify: `docs/runbook.md`, `docs/project-status.md`, `PLAN.md`
- Modify: `docs/superpowers/plans/2026-10-18-staging-held-export.md`
- Test: `backend/tests/unit/test_risk_profile_service.py`, `backend/tests/integration/test_risk_profile_api.py`

**Interfaces:** The runbook starts with the held-export deployment. It permits the override only after a recorded domain approval and a validated, versioned replacement export. Backup, rollback, and verification commands specify which Compose files to use for each mode.

- [x] **Step 1: Correct the runbook's contradictory required-transfer steps and preserve the already-corrected Kaggle credential statement.**
- [x] **Step 2: Mark the staging code slice done in `PLAN.md` and `docs/project-status.md` while retaining the host/DNS/live-verification and Epic 5 quality holds.**
- [ ] **Step 3: Run focused staging tests, all package suites and linters/builds, structure verification, whitespace check, and review the diff.**
- [ ] **Step 4: Commit the documentation/status changes, push, open a PR, confirm all required CI checks pass, then merge and remove this worktree and branch.**

## Notes for the executor

- `backend/Dockerfile.prod` copies `app`, `ingestion`, and `db`, but not `backend/tests`; the default fixture path cannot resolve in that image. `load_profiles` returns an empty list when its configured path is absent.
- The current held export must not be used to exercise reviewed mode. Compose rendering and stubbed deploy tests provide coverage without publishing data.
- The repository has other worktrees owned by earlier work. Remove only this feature's worktree after verifying its exact head is an ancestor of remote `main`.
