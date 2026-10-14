# ARM64 Fiona Release Build — Design

**Date:** 2026-10-14

## Problem

The first manual staging release for merged commit `c5cdd792e4ffe3f71f8f226e39434a010dd94196` passed its verification job but failed while building the ARM64 API image. Pip selected `fiona-1.10.1.tar.gz` on ARM64, and the production image lacked `gdal-config`. The AMD64 dependency installation used a wheel and succeeded. The publish job therefore produced neither a complete multi-architecture release nor a deployment bundle.

## Goals

- Install the system GDAL development files and compiler tools before `pip install .` in the production API image.
- Preserve Fiona's static-layer import capability on both architectures.
- Complete the manual release workflow on `main`, including AMD64/ARM64 manifest checks and the deployment bundle upload.

## Non-goals

- No changes to API behavior, source ingestion, risk-profile labels, or model artifacts.
- No staging host deployment; the user has no OCI VM or DNS, and the current risk-profile export is on quality hold.

## Context And Constraints

`backend/pyproject.toml` requires Fiona. `backend/ingestion/sources/static_layers.py` imports it for vector data. The production image starts from `python:3.12-slim` and currently installs Python dependencies without system build tools. Fiona's source build needs GDAL configuration and compiled extensions. Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.

## Alternatives Considered

1. **Install GDAL development files and compiler tools in the production API image (chosen):** keeps the current dependency and works for either wheel or source installation. The image grows because GDAL runtime libraries remain available to Fiona.
2. **Require a prebuilt Fiona wheel on ARM64:** the failed release selected a source archive, so this would keep the current build blocked without an established wheel source.
3. **Remove Fiona from the API image:** would disable the existing static-layer import path and change application behavior.

## Design

Add one `apt-get` layer to `backend/Dockerfile.prod` before the Python package install. Install `build-essential` and `libgdal-dev` with `--no-install-recommends`; remove apt lists afterward. Debian's `libgdal-dev` supplies `gdal-config`, headers, and a dependency on the runtime library. Retain those libraries in the final single-stage image so Fiona can load at runtime. No new environment variable, interface, migration, error handling, or data transformation is required.

## Rollout

Commit on a dedicated fix branch, open a PR, require the normal CI checks, merge to `main`, then dispatch the manual staging release workflow. Confirm both image manifests and the uploaded bundle. The held `risk_profiles.json` is not included or transferred.

## Files

- `backend/Dockerfile.prod` — install GDAL development files and compiler tools before pip.
- `docs/project-status.md` — record the release result after verification, without claiming a live deployment.
- This spec and `docs/superpowers/plans/2026-10-14-arm64-fiona-release.md` — record the approved build repair.

## Testing Strategy

The failed publish job in [release run 38513589320](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/38513589320) is the observed red integration check. Run backend package verification and the repository structure check locally where available; run PR CI. The decisive green check is a new manual release whose publish job completes, confirms `linux/amd64` and `linux/arm64` for both images, and uploads its deployment bundle.

## Acceptance Criteria

- [ ] The production Dockerfile installs `build-essential` and `libgdal-dev` before pip.
- [ ] The PR's required CI checks pass.
- [ ] A `main` release run passes verify and publish, verifies both architectures, and uploads `staging-release-<sha>`.
- [ ] The status register distinguishes published release assets from an unverified live deployment and keeps the risk-profile quality hold.

## Out Of Scope (backlog)

- A smaller multi-stage GDAL image is deferred until release size or build time is measured.
- OCI provisioning, DNS, and a validated risk-profile export remain separate work.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-arm64-fiona-release.md`.
- Terminology: `docs/glossary.md`.
