# Oracle Always Free Deployment And Project Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish ARM-capable staging images, give the operator a complete Oracle Always Free deployment runbook, and reconcile project tracking against shipped work.

**Architecture:** Keep the existing manual GHCR release bundle and immutable commit-SHA tags. Build multi-architecture manifests, document operator-owned OCI provisioning and lifecycle, then point project overview documents to one canonical status register.

**Tech Stack:** GitHub Actions, Docker Buildx, Docker Compose, Bash, Markdown, Python 3.11+, pytest, npm, Jest.

**Spec:** `docs/superpowers/specs/2026-10-09-oracle-deployment-and-project-status-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/git-workflow.md`, and the approved spec.
- Work on `codex/oracle-deployment-roadmap`; do not change `main` directly.
- Use Conventional Commits. Do not commit OCI keys, `.env.staging`, SSH material, model artifacts, or datasets.
- Keep OCI resource creation and DNS/SSH credential handling operator-owned; GitHub Actions must not receive OCI secrets.
- Preserve the existing portable deployment workflow and commit-SHA image tags.
- Keep database and Redis ports private; only the reverse proxy's HTTP/HTTPS ports are public.
- Use `docs/glossary.md` canonical names for domain terms.
- Verify every changed package. From the repository root run `python scripts\verify_structure.py` and `git diff --check`.
- Backend test command is `(cd backend && pytest -v)` and requires the configured PostGIS test database and Redis. ML: `(cd ml && pytest -v)`. Web: `(cd web && npm test && npm run build)`. Mobile: `(cd mobile && npm test -- --runInBand)`.

## Files And Responsibilities

- `.github/workflows/deploy-staging.yml` — publish and verify AMD64/ARM64 image manifests.
- `docs/runbook.md` — explain OCI provisioning, release, checks, backup, rollback, and cleanup.
- `docs/project-status.md` — be the single current epic and operational-readiness tracker.
- `README.md` — link readers to current project status.
- `geohazard-development-framework.md` — mark the root framework as historical and link to current status.
- `docs/geohazard-development-framework.md` — align epic descriptions with current status.
- `docs/superpowers/plans/2026-10-09-oracle-deployment-and-project-status.md` — track completion steps.

---

### Task 1: Publish and verify multi-architecture images

**Files:**
- Modify: `.github/workflows/deploy-staging.yml`

**Interfaces:**
- The existing API and web tags remain `${IMAGE_PREFIX}-api:${GITHUB_SHA}` and `${IMAGE_PREFIX}-web:${GITHUB_SHA}`.
- Both image builds publish `linux/amd64` and `linux/arm64` variants under a single manifest tag.

- [x] **Step 1: Add explicit target platforms to both Buildx builds**

Add `platforms: linux/amd64,linux/arm64` to each existing `docker/build-push-action@v7` step. Keep existing contexts, Dockerfiles, tags, login, and web build arg unchanged.

- [x] **Step 2: Add a published-manifest verification step**

After both image build steps and before uploading the bundle, add a step that inspects each immutable tag and fails unless both architectures exist:

```yaml
      - name: Verify published image architectures
        env:
          IMAGE_PREFIX: ${{ steps.image.outputs.prefix }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          for image in api web; do
            docker buildx imagetools inspect "$IMAGE_PREFIX-$image:$IMAGE_TAG" --raw \
              | jq -e '[.manifests[].platform | .os + "/" + .architecture] \
                | index("linux/amd64") != null and index("linux/arm64") != null' \
              > /dev/null
          done
```

- [x] **Step 3: Validate workflow and deployment configuration**

Run from the repository root:

```powershell
docker compose --env-file .env.staging.example -f compose.staging.yml config --quiet
python scripts\verify_structure.py
git diff --check
```

Expected: all commands exit successfully. The release workflow's manifest check is the integration verification after publishing; no claim of OCI-host deployment is made.

- [x] **Step 4: Commit the workflow change**

```powershell
git add .github/workflows/deploy-staging.yml
git commit -m "ci: publish staging images for ARM64"
```

### Task 2: Document Oracle Always Free provisioning and deployment

**Files:**
- Modify: `docs/runbook.md`
- Reference: `.env.staging.example`, `compose.staging.yml`, `scripts/deploy_staging.sh`, `docs/data-sources.md`, `docs/superpowers/specs/2026-10-09-oracle-deployment-and-project-status-design.md`

**Interfaces:**
- Continue using `.env.staging`, `IMAGE_PREFIX`, `IMAGE_TAG`, `SITE_DOMAIN`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `CORS_ORIGINS`, `RISK_PROFILE_EXPORT_FILE`, and `INGEST_POLL_INTERVAL_SECONDS`.
- Release command stays `bash scripts/deploy_staging.sh <40-character-release-sha> https://<site-domain>`.

- [x] **Step 1: Add an OCI Always Free prerequisites section**

Document account/home-region selection and that the operator must select an Always Free eligible `VM.Standard.A1.Flex` ARM instance. State Oracle's current tenancy totals (2 OCPUs, 12 GB RAM, 200 GB block storage in the home region), that shape capacity may be unavailable, and that paid resources/overages can incur charges. Link Oracle's official Always Free resource page and launch-instance tutorial. Make clear this repository does not create OCI resources or guarantee availability.

- [x] **Step 2: Document secure network, SSH, DNS, and host setup**

Give ordered Console steps: create/use a VCN with a public subnet and internet gateway/route; assign a public IP; permit inbound TCP 22 only from the operator's source IP and inbound TCP 80/443 from clients; do not open 5432 or 6379; allow outbound DNS/HTTPS for GHCR and source feeds; add matching host firewall rules; create the DNS A record; wait for DNS resolution. Describe keeping the private SSH key private. Link to Oracle security-list guidance and Docker's official Ubuntu engine installation instructions. The operator verifies `uname -m` reports `aarch64`, Docker works, and `docker compose version` is available before continuing.

- [x] **Step 3: Document release bundle, image access, and risk-profile preparation**

Explain how to run **Prepare Staging Release** on `main`, download the artifact associated with the release SHA, and extract it on the VM. Explain that packages may be private; if so, log in to GHCR interactively using a token with only `read:packages`, and never place the token in the repository or shell command text. Before starting the stack, copy the trained `ml/model_artifacts/v1/risk_profiles.json` export to the host path configured by `RISK_PROFILE_EXPORT_FILE` (for example `./deploy-data/risk_profiles.json`), ensure the file exists and is readable, then create `.env.staging` from the example and replace all sample values. State that this historical statistical profile is descriptive, not a prediction, and that an untrained fixture is for local smoke testing only.

- [x] **Step 4: Document deployment verification, backups, rollback, and cleanup**

Include commands to inspect the release SHA and architecture manifest; run the deploy script; verify `/health`, `/api/v1/events`, and `/api/v1/risk-profile/clusters`; inspect Compose service health and logs; and diagnose GHCR auth, DNS/ports/TLS, missing export, disk, and health-check failures. Include timestamped Postgres dump and restore commands and a safe method to back up the named Caddy data volume before upgrades. Explain previous-SHA rollback, when database restore is needed, retaining volumes on ordinary shutdown (`compose down` without `-v`), and clean removal of the VM, attached boot/block volumes, public IP, and DNS after saving required backups.

- [x] **Step 5: Review instructions against actual repository interfaces**

Check every variable and command against `.env.staging.example`, `compose.staging.yml`, `scripts/deploy_staging.sh`, and the output structure in `ml/src/ml/train.py`. Remove commands that refer to unavailable files, ports, or service names. Run:

```powershell
docker compose --env-file .env.staging.example -f compose.staging.yml config --quiet
git diff --check
```

Expected: Compose configuration and whitespace validation succeed.

- [x] **Step 6: Commit the runbook change**

```powershell
git add docs/runbook.md
git commit -m "docs: add Oracle Always Free deployment guide"
```

### Task 3: Reconcile project status and roadmap links

**Files:**
- Create: `docs/project-status.md`
- Modify: `README.md`
- Modify: `geohazard-development-framework.md`
- Modify: `docs/geohazard-development-framework.md`

**Interfaces:**
- `docs/project-status.md` is the authoritative current status page.
- Historical design and implementation plans remain historical records; their old unchecked boxes are not treated as current backlog without evidence.

- [x] **Step 1: Create the current project status register**

Record these evidence-based statuses and link relevant implementation plans, specs, runbook sections, and code where helpful:

| Epic/workstream | Status | Evidence and remaining work |
|---|---|---|
| Epic 1 earthquake API and web map | Implemented | Existing live feed, API, and dashboard; historical completion evidence remains in merged code/history. |
| Epic 2 PHIVOLCS/realtime/deduplication | Implemented | Existing ingestion, bulletin and realtime contracts; retain source/network caveats in runbook. |
| Epic 3 static hazard layers | Code implemented; source coverage operational | Import/API/map path exists; reviewed source assets, licensing, and completeness require operator review/import. |
| Epic 4 mobile nearby alerts/offline cache | Foreground slice implemented | Link the 2026-10-09 plan; background push and native release pipelines are explicitly deferred. |
| Epic 5 regional seismic risk profiles | Historical-data pipeline implemented | Training and profile API/UI exist; periodic retraining and live/canonical-event modeling are deferred. |
| Epic 6 landslide/InSAR stretch scope | Deferred | No claim of user-facing product readiness. |
| Oracle Always Free deployment | Guide/image support in progress, then operator action | Link this runbook section; OCI account provisioning and deployed-host validation are operator tasks. |

Add a short project conventions section explaining this register supersedes the conflicting phase summaries and old unchecked plan checkboxes. Distinguish implementation status from data import and actual deployment status.

- [x] **Step 2: Link overview documents to the canonical register**

Add a concise status link in the README near the project overview. At the start of `geohazard-development-framework.md`, label its schedule as the original planning framework and direct readers to `docs/project-status.md`. Update `docs/geohazard-development-framework.md` to point to the register and align Epic 5/6 labels with the current scope without deleting the historical intent.

- [x] **Step 3: Verify status statements against committed evidence**

Use `git log`, code paths, README content, the Epic 4 plan/spec, and the Epic 3 runbook section. Avoid treating unchecked historical plans as pending work. Confirm no status statement implies mobile background push or national static-layer completeness.

Run:

```powershell
python scripts\verify_structure.py
git diff --check
```

Expected: structure and whitespace checks succeed.

- [x] **Step 4: Commit status and roadmap updates**

```powershell
git add docs/project-status.md README.md geohazard-development-framework.md docs/geohazard-development-framework.md
git commit -m "docs: reconcile project epic status"
```

### Task 4: Run package verification and review the complete branch

**Files:**
- Verify: all files changed by Tasks 1–3 and package suites named below.

- [ ] **Step 1: Run ML and mobile tests**

```powershell
Set-Location ml
pytest -v
Set-Location ..
Set-Location mobile
npm test -- --runInBand
Set-Location ..
```

Expected: both suites pass. Report dependency or environment failures separately; do not mark the corresponding acceptance criterion as verified.

- [ ] **Step 2: Run web tests and production build**

```powershell
Set-Location web
npm test
npm run build
Set-Location ..
```

Expected: web tests and build pass.

- [ ] **Step 3: Run backend tests and integration prerequisites**

With Docker PostGIS and Redis available and the project test database created, run:

```powershell
Set-Location backend
pytest -v
Set-Location ..
```

Expected: backend unit and integration suites pass. If Docker or the migrated test database is unavailable, report the exact blocker and do not claim the backend suite passed.

- [ ] **Step 4: Run final structure, Compose, and diff checks**

```powershell
python scripts\verify_structure.py
docker compose --env-file .env.staging.example -f compose.staging.yml config --quiet
git diff --check
git status --short
```

Expected: structure/configuration/diff checks pass and status contains only intended committed files.

- [ ] **Step 5: Complete final independent review**

Review the full branch diff against `main`. Confirm multi-architecture build steps include a manifest check, all docs match actual env vars/commands, no secrets or generated artifacts are present, and all deferred scope is tracked. Record exact verification outcomes for the handoff.

## Notes for the executor

- Execute tasks in order because documentation relies on the final workflow and release interfaces.
- Use one implementation agent for one task at a time, then a spec-compliance review, followed by a code-quality review. Fix and re-review all findings before proceeding.
- The operator's OCI account, DNS provider, private SSH key, source Kaggle credentials, and any private GHCR package access are not available to agents. Never request or commit those secrets.
- The only external integration not verifiable in CI is a real Oracle VM deployment. The repository can verify image manifests after publishing and the runbook can provide the commands the operator will use.
