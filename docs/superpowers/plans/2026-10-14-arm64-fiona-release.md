# ARM64 Fiona Release Build — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a verified AMD64/ARM64 staging release after repairing the Fiona source build in the ARM64 production API image.

**Architecture:** Install Debian GDAL development files and compiler tools in the single-stage production API image before Python dependencies. Keep application code and the held model export unchanged.

**Tech Stack:** Docker, Debian package manager, Python/Fiona, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-14-arm64-fiona-release-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Commit with Conventional Commits; do not commit model artifacts, raw data, or credentials.
- Run backend package verification, `python scripts/verify_structure.py`, and `git diff --check` before completion claims. CI has provisioned PostGIS and Redis for its integration suite.
- Keep the current regional profile export off staging under the recorded quality hold.

### Task 1: Repair ARM64 dependency installation

**Files:**
- Modify: `backend/Dockerfile.prod`

**Interfaces:**
- Consumes: `python:3.12-slim`, Debian package repositories, and the existing `backend/pyproject.toml` dependency set.
- Produces: the same API image and command, with system GDAL build and runtime libraries available to Fiona.

- [ ] **Step 1: Confirm red integration evidence.** Inspect release run `38513589320`: AMD64 pip installs Fiona's wheel; ARM64 pip selects `fiona-1.10.1.tar.gz` and fails because `gdal-config` is absent.
- [ ] **Step 2: Add the minimal Dockerfile layer** before `RUN pip install --no-cache-dir .`:

  ```dockerfile
  RUN apt-get update \
      && apt-get install -y --no-install-recommends build-essential libgdal-dev \
      && rm -rf /var/lib/apt/lists/*
  ```

- [ ] **Step 3: Run local checks.** From the repository root run `python scripts/verify_structure.py` and `git diff --check`. Run backend tests with the project's provisioned services if available; PR CI supplies PostGIS and Redis otherwise.
- [ ] **Step 4: Commit** as `fix: install gdal build dependencies for arm64`.

### Task 2: Verify and publish the release

**Files:**
- Modify: `docs/project-status.md` after the release result is known.

**Interfaces:**
- Consumes: merged `main` commit and the manual `.github/workflows/deploy-staging.yml` workflow.
- Produces: a release run with two published multi-architecture images and a `staging-release-<sha>` bundle; no host deployment.

- [ ] **Step 1: Open the fix PR** with Summary / Testing / Notes, noting no API, schema, or environment breaking change.
- [ ] **Step 2: Require green CI, then merge** using a standard merge commit.
- [ ] **Step 3: Dispatch the manual release** on `main` and inspect verify, publish, architecture-check, and artifact-upload results.
- [ ] **Step 4: Update `docs/project-status.md`** with the observed result, release SHA, and remaining OCI/model hold, then verify and commit the documentation.

## Notes for the executor

The failed release run is the red integration test for this Docker configuration change. The green integration test is a fresh successful publish run. Do not report images as published before inspecting that run; no OCI VM or DNS exists, so live health and risk-profile endpoint checks cannot be claimed.
