# Oracle Always Free Deployment And Project Status — Design

**Date:** 2026-10-09

## Problem

GeoHazard PH has a portable Linux staging bundle but no Oracle Cloud Infrastructure (OCI) deployment guide. The current GitHub Actions release publishes single-architecture images by default, while the likely Always Free target, VM.Standard.A1.Flex, is ARM. The required risk-profile export is also an operator-provided host file whose preparation is not explained in the release procedure. Project phase information is split across the README, two development-framework documents, and historical plans, so completed work is difficult to distinguish from future work.

## Goals

- Publish immutable API and web images for both `linux/amd64` and `linux/arm64`.
- Document a tested-by-commands, operator-run Oracle Always Free A1 setup and deployment path, including DNS, ingress, SSH, Docker Compose, GHCR, risk-profile data, health checks, backups, rollback, and cleanup.
- Establish one current project status page that identifies completed code, operational data prerequisites, and deferred scope, and make the older roadmap documents point to it.
- Preserve the existing portable staging workflow and avoid requiring OCI credentials in GitHub or the repository.
- Run the repository's required verification for changed files and report any checks that require unavailable external services or account access.

## Non-goals

- Creating or changing an OCI tenancy, VM, network, DNS record, billing state, or credential.
- Automatic provisioning or remote deployment from GitHub Actions.
- Mobile background push, APNs/FCM delivery, device registration, or native device build pipelines; Epic 4's foreground nearby-alert slice is treated as complete.
- New UI work, new hazard features, or changes to API behavior.
- Claiming all Philippines static hazard source data is imported or complete. Reviewed source vectors and permissions remain an operator/data stewardship prerequisite.
- Claiming always-free availability is guaranteed. Oracle documents regional capacity constraints and eligibility limits.

## Context And Constraints

- `CODING_STANDARDS.md`, `AGENTS.md`, and `docs/git-workflow.md` govern changes, verification, and branch handling.
- `docs/runbook.md` already describes the portable bundle and `scripts/deploy_staging.sh`; `compose.staging.yml` mounts `RISK_PROFILE_EXPORT_FILE` into the API container.
- `.github/workflows/deploy-staging.yml` currently builds API and web images without an explicit platform matrix.
- Epic 4 is merged in PR #16 and has a completed plan at `docs/superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md`. Its spec excludes backend push delivery.
- Epic 3 APIs/import code and Epic 5 historical seismic risk-profile pipeline exist. National static source coverage is still a separately reviewed data import. Landslide/InSAR remains stretch work.
- OCI Always Free A1 compute is limited to 2 OCPUs and 12 GB RAM per tenancy in the home region, with capacity not guaranteed. See Oracle's [Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).
- Only the operator has access to their OCI tenancy, SSH private key, DNS provider, and any needed GHCR read credentials. Documentation must not ask them to commit secrets.

## Alternatives Considered

1. **Documented manual provisioning plus immutable multi-architecture images (chosen).** Fits the current manual release artifact, avoids storing cloud credentials, and gives the operator transparent setup and rollback steps. The tradeoff is that the operator performs the OCI console and SSH actions.
2. **GitHub Actions remote deployment using OCI API keys and SSH secrets.** Reduces manual steps but requires tenancy configuration, privileged secrets, ongoing identity/network maintenance, and a target VM; none are available in this project context.
3. **Run only on an AMD micro instance.** Avoids ARM image work but does not match the expected capacity needed by PostGIS, Redis, API, web, Caddy, and worker together. It would also avoid rather than resolve the architecture gap.

## Design

### Architecture and data flow

1. The manual `Prepare Staging Release` workflow runs its existing package checks.
2. On `main`, Buildx publishes immutable API and web tags for `linux/amd64` and `linux/arm64` under the selected commit SHA.
3. The operator creates an Always Free eligible ARM VM in the tenancy home region, configures its network and DNS, installs Docker Compose, and downloads/extracts the workflow bundle.
4. The operator prepares `.env.staging` and the required risk-profile JSON on the VM, authenticates to GHCR if the packages are private, then invokes the existing deploy script with the release SHA and HTTPS URL.
5. Compose pulls the host-compatible image variant, runs database migrations and services, and the script checks health, events, and risk-profile endpoints.

### Components

- `.github/workflows/deploy-staging.yml`: add explicit Buildx platform targets for both image builds; retain commit-SHA tags and the portable artifact.
- `docs/runbook.md`: add Oracle Console and host setup steps, minimal ingress/egress requirements, arm64 image/release steps, risk-profile export placement, deploy/verify commands, storage/backups, rollback, cleanup, and limits/capacity guidance.
- `docs/project-status.md`: create the canonical epic and operational-readiness register with evidence links and specific deferred work.
- `README.md`, `geohazard-development-framework.md`, and `docs/geohazard-development-framework.md`: link current status to the register and remove contradictory present-tense status claims where needed.

### Configuration and secrets

- No new application setting is required. Continue to use `.env.staging.example` and the existing variables.
- Keep `.env.staging`, the risk export, SSH keys, OCI credentials, and any GHCR token on the operator's machine/VM only.
- The runbook must explain where the risk-profile JSON comes from, that it is a descriptive statistical profile rather than a prediction, and that the configured host path must exist before Compose starts.

### Errors and operational risks

- Document OCI "out of host capacity" as a regional availability issue with Oracle's recommended wait/availability-domain steps; do not suggest upgrading to paid as the only response.
- Document GHCR authentication failure, DNS/port/TLS readiness, missing risk export, exhausted disk, and failed health checks with specific diagnostics.
- Restrict SSH ingress to the operator's source IP where practical; expose only 80/443 publicly for the site. Keep database and Redis ports private.
- Explain that the free allowance is bounded and depends on the tenancy's region and resource allocation; the guide does not promise zero cost if the operator selects paid resources or exceeds quotas.
- Back up Postgres data and Caddy state before release changes; use the previous image SHA for rollback and restore a database backup when schema/data changes require it.

## Rollout

This lands as one reviewable feature branch. Update the workflow first, then the runbook, then the canonical project-status register and links. No infrastructure is provisioned by this change. The operator can follow the guide after the branch is merged and a multi-architecture release bundle is produced from `main`.

## Files

- Modify `.github/workflows/deploy-staging.yml` — publish ARM64 and AMD64 manifests.
- Modify `docs/runbook.md` — document Oracle setup and lifecycle.
- Create `docs/project-status.md` — provide the canonical epic/readiness tracker.
- Modify `README.md` — point project-status readers at the tracker.
- Modify `geohazard-development-framework.md` — mark as historical framework and link to current tracker.
- Modify `docs/geohazard-development-framework.md` — link to current tracker and clarify phase scope.
- Create `docs/superpowers/plans/2026-10-09-oracle-deployment-and-project-status.md` — implementation tasks after spec review.

## Testing Strategy

- Workflow: inspect the YAML diff and use the repository's workflow verification available locally; the staging workflow itself verifies project packages and Compose configuration.
- Project docs and structure: `python scripts\verify_structure.py` and `git diff --check` from the repository root.
- Release configuration: `docker compose --env-file .env.staging.example -f compose.staging.yml config --quiet` (already used by the workflow; the example file's risk path is not mounted by config validation).
- Full package checks listed by `CODING_STANDARDS.md`: backend pytest with PostGIS/Redis, ML pytest, web tests/build, and mobile Jest. Do not claim OCI runtime validation without an operator tenancy and deployed VM.

## Acceptance Criteria

- [ ] Both published application image tags contain `linux/amd64` and `linux/arm64` variants.
- [ ] The OCI instructions can be followed without committing secrets or granting a GitHub workflow OCI access.
- [ ] The instructions explicitly require an Always Free-eligible A1 shape in the home region, explain the tenancy resource ceiling/capacity caveat, and give SSH/network/DNS steps.
- [ ] The instructions explain how to supply a valid risk-profile export, deploy an immutable SHA, check all three endpoints, back up/restore data, roll back, and remove the VM safely.
- [ ] `docs/project-status.md` distinguishes completed Epic 4 foreground behavior from deferred background push, completed Epic 3 code from incomplete source data coverage, and completed seismic ML from deferred landslide/InSAR stretch scope.
- [ ] The README and both development-framework documents direct readers to the canonical project status.
- [ ] Required package and structure checks have recorded results; checks unavailable in this environment are clearly reported.

## Out Of Scope (backlog)

- Background mobile push delivery, provider/device registration, and native release builds.
- Reviewed PHIVOLCS static-layer digitization/import and national completeness audit.
- Landslide/InSAR ingestion and user-facing products.
- Fully automated OCI provisioning/deploy workflow; revisit if the operator later wants it and supplies a tenancy design and secret-management approach.
- Periodic scheduled model retraining or a live-event risk model; existing risk profiles use historical Kaggle data.

---

## Spec self-review

- No placeholders or open-ended acceptance statements remain.
- Scope separates already-complete feature work from deployment and operational data prerequisites.
- Each goal maps to one or more acceptance criteria; external OCI access is explicitly excluded from agent verification.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-09-oracle-deployment-and-project-status.md`.
- Terminology: `docs/glossary.md`.
