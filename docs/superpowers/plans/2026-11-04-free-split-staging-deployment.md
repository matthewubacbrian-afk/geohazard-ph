# Free Split Staging Deployment — Implementation Plan

> **For agentic workers:** Use `docs/superpowers/templates/plan-template.md` when executing this plan. This plan preserves the original rollout checklist. The 2026-11-05 checkpoint below and docs/free-split-deployment.md supersede earlier provisioning assumptions; unchecked acceptance checks remain open.

**Goal:** Stage the current GeoHazard PH web and API using the lowest-cost practical split-provider architecture, with a verified PostGIS database, working Redis-backed realtime updates, scheduled ingestion, and an explicit free-tier operating envelope.

**Architecture:** Serve the Vite web application from Render Static Sites; run the FastAPI API as one Render Free Web Service in Singapore; store relational and spatial data in Supabase Postgres with PostGIS enabled; use Upstash Redis over its native TCP protocol only if connection, Pub/Sub, regional availability, and measured free quota checks pass; run the existing one-cycle ingestion scheduler in short-lived GitHub Actions jobs. Keep migrations as a release operation, distinct from recurring ingestion. The React Native app remains distributed separately and points to the staged API URL.

**Tech Stack:** React 18, Vite, React Native/Expo, FastAPI, SQLAlchemy/psycopg, Postgres/PostGIS, Redis Pub/Sub, Docker, GitHub Actions, Render, Supabase, Upstash.

## Verified Checkpoint: 2026-11-05

The active deployment uses Render Static Site + Render Free API, Supabase PostGIS,
and Upstash Redis. Oracle is not the selected deployment path.

See [the current deployment and operations record](../../free-split-deployment.md)
for public links, the corrected data flow, configuration ownership, release and
migration procedures, ingestion evidence, cost settings, and remaining checks.
The earlier context and checklist below are historical rollout evidence, not a
claim that the still-unchecked checks have been completed.

- PHIVOLCS fix: [PR #83](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/83).
- Published worker image SHA: `5c33057841dd9ae1a2df91926b626b94a78bed0a`.
- [Release run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41995260585)
  and [one-cycle ingestion run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41999595044)
  succeeded. The API returned 299 PHIVOLCS and 40 USGS events after ingestion.
- [PR #84](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/84)
  changed the schedule to every six hours. `STAGING_INGEST_ENABLED=true` was verified.
- Render Hobby: no card, $0 reported/projected. Supabase Free: no payment method,
  dashboard spend cap enabled. Upstash Free Tier: $0 reported. These are dated
  operator-reported account observations, not continuing usage guarantees.
- End-to-end browser WebSocket delivery/reconnect, mobile staging, automated
  migrations, backup/restore, and the first scheduled trigger still require
  recorded acceptance evidence. Manual ingestion success does not prove them.
- Regional profiles remain held; approval record and exact export version/hash
  are still outstanding. Ingestion does not release risk labels.

## Current Project Context

- The project status was re-read on 2026-11-04; its epic evidence and caveats are recorded in `docs/project-status.md`. Epics 1 and 2 are implemented; Epic 3 has a locally verified 155-feature GEM snapshot with partial coverage and unresolved PHIVOLCS reuse permission; Epic 4 has foreground alerts and offline cache but background push and store publishing remain open; Epic 5's risk-profile export is held pending domain review; Epic 6's NASA overlay is informational and InSAR remains research-only; Epic 7 is a scene-analysis demonstrator whose model is absent from the default API image and whose deployed Linux/ARM64 resource fit is unverified.
- Partial staging hosting is now verified: the Render static site `geohazard-ph-staging-web` deployed successfully from `main` at source SHA `38853d4` on 2026-11-04. Its public URL is `https://geohazard-ph-staging-web.onrender.com`. API/realtime integration and browser route/map checks remain open. The earlier OCI A1.Flex creation attempt failed because the Singapore availability domain was out of capacity; no VM or DNS is recorded.
- `compose.staging.yml` assumes a colocated PostGIS 16 database and Redis 7, runs Alembic before API startup, and keeps a persistent ingestion worker polling every 300 seconds. This split plan replaces those assumptions with managed Postgres/Redis and an ephemeral scheduler, so it requires real service-compatibility checks before implementation.
- The API reads `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, and `RISK_PROFILE_EXPORT_PATH`. The web build reads `VITE_API_BASE_URL` and can derive its WebSocket URL from it. The backend Docker image currently starts Uvicorn on port 8000; Render's start command must bind to its assigned `$PORT` (or an explicitly configured supported port).
- `backend/ingestion/scheduler.py` already supports a one-cycle run via `INGEST_MAX_CYCLES=1`. It ingests USGS and PHIVOLCS independently and publishes committed event changes to Redis. A successful process exit alone may not prove both sources succeeded; ingestion logs and resulting API data must be inspected.
- The API realtime endpoint subscribes to Redis Pub/Sub. The ingestion job and API are separate processes, so a per-process in-memory broker is not equivalent unless architecture and product scope are deliberately changed.
- Fresh migrations do not populate the static GEM snapshot. Any static-layer import needs a separately documented, checksum-verified, permission-cleared data procedure. Volcano-zone data must stay absent unless reuse permission is obtained. The held Epic 5 profile export must stay empty. The scene-analysis endpoint may return its documented typed 503 without the model package and weights.

## Summary And Recommendation

Use this architecture as a **free-first staging/demo target**, conditional on the provider gates below. It avoids waiting on OCI A1 capacity and assigns each component to a service suited to its runtime. It is not an always-on or production-SLA deployment. The web static site has no API cold start, but the free API can sleep, the free database may pause on inactivity, scheduled jobs can be delayed, and quotas/provider policies can change.

Do not create all provider resources before verifying the database migration and Redis Pub/Sub paths. First prove that Supabase can host the project's PostGIS schema and that Upstash's free TCP endpoint supports the exact `redis-py` publisher/subscriber behavior. If either gate fails or its free limits do not fit measured usage, pause and choose a documented fallback instead of silently losing geospatial or realtime behavior.

## Deployment Flow

```text
USGS + PHIVOLCS -> GitHub Actions one-cycle ingestion
                          |                    |
                          v                    v
                  Supabase PostGIS      Upstash Redis Pub/Sub
                          ^                    |
                          |                    v
                          +------ Render FastAPI
                                       ^
                                       | HTTPS REST + WSS
                                Browser / mobile
```

The browser is served by Render Static Sites. Database writes and Redis
publications are performed by the worker; Supabase and Upstash do not connect
directly. Browser ingestion-generated WSS delivery remains an acceptance check.

The arrows show responsibilities, not a guarantee that the providers' free regions are colocated. Select Singapore for Render and Supabase where available; verify the actual Upstash free-tier region and measure latency. Static sites are served through a global CDN.

## Provider Split: Pros And Cons

| Component | Proposed provider | Pros | Cons / limits to plan around |
| --- | --- | --- | --- |
| Web frontend | Render Static Site (free) | Static Vite build, CDN delivery, automatic Git deploy, no compute process to keep warm. | Needs API URL baked into the build; web and API have separate origins, so CORS and WebSocket URLs must be exact. Build minutes and outbound bandwidth have workspace limits. |
| FastAPI | Render Free Web Service (Singapore) | Supports Python/Docker and WebSockets; avoids OCI A1 capacity provisioning; simple Git-based releases. | Sleeps after 15 minutes without qualifying inbound traffic and can take about a minute to wake; local filesystem is ephemeral; free instance can restart; one instance and monthly shared free hours/bandwidth limits. A sleeping API can make mobile/web checks feel unavailable during wake-up. |
| Postgres/PostGIS | Supabase Free (Singapore, if offered) | Managed Postgres and PostGIS; supports regular Postgres client connections and spatial queries; no VM administration. | 500 MB database allowance; projects may pause after low database activity over a week; free plan has no automatic backups; shared resources and external DB connectivity add latency and operational coupling. Validate the project's exact migrations and connection mode first. |
| Redis | Upstash Free, native TCP | Avoids managing Redis; compatible Redis TCP protocol and TLS can work with the existing Redis client and Pub/Sub model. | 250 MB dashboard storage allowance, 10 GB monthly bandwidth, 500,000 commands/month on current published pricing; free-tier region selection may not match Singapore. Event fan-out and reconnects count toward usage. Prove Pub/Sub behavior and count realistic commands before relying on it. Do not substitute the REST client without a separate realtime compatibility test. |
| Ingestion scheduler | GitHub Actions scheduled workflow | Reuses the existing one-cycle scheduler and public-source adapters; ephemeral runner avoids paying for an always-on worker. Standard GitHub-hosted runners are free for public repositories. | Scheduled runs can be delayed or dropped during high load; failures need useful job summaries; private repos have monthly included runner-minute limits, so frequent schedules may exceed them. Secrets are needed for DB/Redis; scheduled jobs must not expose them in logs. |

### Cost Position

Target monthly provider spend is **$0 only while every service remains on its free plan and usage stays inside the current included quotas**. This is not a price guarantee and does not cover optional domains, upgraded resources, overages, taxes, or future plan changes. Never enable automatic paid upgrades for this staging setup. Review each provider's billing and usage page after provisioning and periodically afterward. Add a payment method only if the provider requires one; set the strictest available spend controls and alerts first.

The selected cadence is every six hours: about 120 scheduled cycles per 30-day
month. At the observed 339-event batch size, roughly 40,680 publish commands are
expected, before subscriber traffic, retries, and feed growth. This is a forecast,
not measured monthly usage. Keep monitoring the 500,000-command free ceiling.


## Alternatives Considered

1. **OCI Always Free VM with current Compose stack.** Keeps PostGIS, Redis, API, worker, web, and reverse proxy under one Compose file and avoids cross-provider connections. Rejected as the first path because A1 capacity in Singapore is currently blocking VM creation; VM operations, patching, backups, DNS, and free-resource quota tracking remain operator responsibilities.
2. **All components on Render Free.** Simplifies account management. Rejected because Render's free Postgres expires after 30 days, and free Key Value is in-memory and loses data on restarts; neither is an appropriate persistent PostGIS + realtime foundation for this project.
3. **Vercel frontend plus Render API and Supabase/Upstash.** Could host the same static Vite bundle. Not selected because the current Render static path is simpler and adds no serverless API/runtime constraints; reconsider if the team already prefers Vercel or needs its frontend-specific workflows.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/glossary.md`, `docs/git-workflow.md`, and applicable testing/error-handling contracts before implementation.
- Keep one API service instance on the free tier. Do not claim high availability, always-on behavior, durable Redis state, production readiness, hazard prediction, or official warning status.
- Never expose credentials in chat, screenshots, workflow logs, source files, or committed `.env` files. Put provider values into the corresponding provider's secret store/GitHub Actions secrets; use least-privilege tokens and rotate any credential accidentally exposed.
- Use HTTPS/WSS for public service traffic and TLS for external DB/Redis connections. Keep CORS origins exact. Do not publish database or Redis ports to the internet.
- Pin releases to immutable commit-SHA images where using GHCR; use the existing release workflow, but do not treat image publication/CI as a live deployment check.
- Keep risk-profile export held and do not seed unapproved PHIVOLCS vector data. Clearly disclose Epic 7 scene-review limits and its missing model runtime.
- Treat provider quotas and free-tier behavior as time-sensitive. Recheck official pricing, limits, feature support, and region options during setup.
- Make no code, workflow, infrastructure, or provider changes until the relevant rollout task is selected and the operator has reviewed the exact change.

## Rollout Plan

### Task 1: Confirm the code and target assumptions

**Files:** Read only: `docs/project-status.md`, `docs/runbook.md`, `compose.staging.yml`, `.github/workflows/deploy-staging.yml`, `backend/app/config.py`, `backend/app/core/db.py`, `backend/app/services/realtime.py`, `backend/ingestion/scheduler.py`, `web/src/api/client.ts`, `web/src/api/realtime.ts`.

- [x] Confirm the deployment branch contains the desired current code and that there are no unrelated user edits to carry into release work.
- [x] Confirm web build path, API startup command, `/health`, `/api/v1/events`, `/api/v1/risk-profile/clusters`, and `/ws/events` behavior at the selected release SHA.
- [x] Confirm whether repository visibility and GitHub Actions allowance make the intended schedule free; estimate observed runtime before picking cadence.
- [x] Confirm static-layer import policy and whether the 155-feature GEM snapshot will be intentionally seeded into staging; do not assume migrations perform this import.

**Task 1 preflight record (2026-11-04):** `origin/main` and the selected code baseline both resolve to `38853d48289df95502906615c4af15a78b78452b` (PR #82, 2026-10-31); the repository is public, and the isolated deployment-plan worktree contains no unrelated application-code edits. The existing release workflow is manual (`workflow_dispatch`) and verifies/publishes multi-architecture images; it does not yet run scheduled ingestion. Standard GitHub-hosted runners are free for this public repository, but no hosted one-cycle ingestion runtime exists to measure yet. Use a **30-minute provisional cadence** for the first staging schedule, then check actual duration, source freshness, retries, and Redis command/bandwidth usage before making it more frequent. A 30-minute cadence is 1,440 runs per 30-day month; this is only the run count, not an Actions schedule guarantee.

The web build is `npm ci && npm run build` from `web/`; `VITE_API_BASE_URL` supplies the API URL and the web derives `/ws/events` as WSS from HTTPS. The production API image currently starts Uvicorn on fixed port 8000, so the Render start command must use `$PORT`. Source inspection confirms `/health`, `/api/v1/events`, `/api/v1/risk-profile/clusters`, and `/ws/events` are implemented; actual hosted HTTP/WebSocket checks remain later rollout gates. The mobile API URL can be entered in the app and must end in `/api/v1`.

**Staging content default:** include earthquake records from the available live feeds and, if the staging database fits, seed only the verified pinned GEM reference snapshot: 155 accepted features, source commit `56816508ad92fd6846dad1163b1c8c01376a2cd1`, SHA-256 `37babb516edfac22b5ae91744495d8546b3ae4676b4d4f68cc77da8222df20e1`, with the runbook's `CC-BY-SA-4.0` attribution metadata. The raw source is not bundled, so the operator must follow the checksum-verified import procedure after database compatibility is proven. Do not seed PHIVOLCS fault/volcano geometries while reuse permission is unresolved. Keep risk profiles empty and do not package the scene-analysis model; the scene-analysis endpoint remains a demonstrator and may return its typed unavailable response.

**Gate:** A release SHA, scope of staged endpoints/data, and provisional update cadence are written down. Epic 5 remains held; Epic 7 remains demonstrator-only. No provider resources or application workflows have been created yet.

### Task 2: Prove managed PostGIS compatibility

**Files:** No app changes unless an evidenced incompatibility requires a separately reviewed implementation change. Provisioning work is operator-owned.

- [x] Create a Supabase Free project in Singapore if available; otherwise record region and expected latency before proceeding. **Observed checkpoint (2026-11-04):** the healthy Free project `geohazard-ph-staging` is provisioned in Southeast Asia (Singapore, `ap-southeast-1`). A separate empty Mumbai (`ap-south-1`) project also remains and should be retired only after the Singapore project is confirmed as the intended one.
- [x] Enable PostGIS in Supabase's recommended `extensions` schema, then inspect the project's existing Alembic migrations for extension/schema assumptions. **Observed checkpoint (2026-11-04):** PostGIS 3.3.7 is enabled in `extensions`. Migrations `0001` and `0003` use unqualified PostGIS type/function names, and `0001` runs `CREATE EXTENSION IF NOT EXISTS postgis` without a schema clause. Before migration, verify the `postgres` role's actual `search_path` and the installed extension schema using read-only SQL; do not change the project's migration or database configuration until that result is known.
- [x] Connect using the exact SQLAlchemy/psycopg URL shape the API and migration will use. Do not paste a real URL/password into chat. **Observed checkpoint (2026-11-04):** the operator used the shared **Session pooler** (port **5432**) and SQLAlchemy's `postgresql+psycopg` driver; the URL and password were entered locally and are not recorded here. The SQL Editor preflight reports `current_user=postgres`, `search_path="$user", public, extensions`, and PostGIS schema `extensions`.
- [x] Apply all migrations to an empty project using the intended connection mode. **Observed checkpoint (2026-11-04):** the operator reports Alembic successfully ran revisions `0001`, `0002`, and `0003` against the Singapore project.
- [x] Verify geometry/geography types, SRID 4326 values, and GiST index creation. **Observed checkpoint (2026-11-04):** SQL Editor returned Alembic revision `0003`; `hazard_events.location` is `Point` geography SRID 4326; `fault_lines.geometry` and `volcano_zones.geometry` are geometry SRID 4326; all three expected GiST indexes exist.
- [x] Confirm Postgres row counts and database-size usage. **Observed checkpoint (2026-11-04):** SQL Editor reports an 18 MB database and 0 rows in `hazard_events`, `fault_lines`, and `volcano_zones`, as expected for a fresh staging schema.
- [x] Verify application database reads and PostGIS-backed API queries locally. **Observed checkpoint (2026-11-04):** local Uvicorn returned HTTP 200 for `/health`, `/api/v1/events`, and `/api/v1/faults`; the database-backed event/fault reads returned empty arrays as expected. The public API is read-only for these resources; verify the ingestion write path during Task 7's one-cycle scheduler check instead of inventing a test write endpoint.
- [ ] Record the selected connection string mode (direct or session pooler), required TLS options, connection cap, free database size, pause behavior, and backup/restore procedure.

**Gate:** All migrations and database-backed API queries work without weakening their semantics; storage and connection use fit the free limits. The scheduled ingestion write/realtime evidence is verified later in Task 7. Otherwise stop and design a compatible database option.

### Task 3: Prove Redis TCP and Pub/Sub compatibility

**Files:** No app changes unless an evidenced incompatibility requires a separately reviewed implementation change. Provisioning work is operator-owned.

- [x] Create one Upstash Free Redis database only after reviewing region and current pricing; prefer a nearby region if available. **Observed checkpoint (2026-11-04):** operator created `geohazard-ph-staging` on Upstash Free in Singapore (`ap-southeast-1`). Dashboard showed 500K commands/month, 10 GB monthly bandwidth, 250 MB storage, and $0 monthly at creation. After local smoke checks, Usage showed 11 commands, 2 KB bandwidth, 0 B stored, and $0.00 cost; this is a local-test baseline, not representative application load.
- [x] Put the TLS TCP URL in a temporary local secret store for the smoke test; verify the current `redis-py` publisher pipeline and async subscriber connect, subscribe, receive an `EventChange`, reconnect after interruption, and close cleanly. **Observed checkpoint (2026-11-04):** a local Python `redis-py` TCP/TLS PING returned `True`; a sync publisher and async subscriber exchanged `pubsub-smoke-ok` on a randomly named temporary channel. URL was entered through a hidden PowerShell prompt and removed from the process environment afterward. This proves basic TCP and Pub/Sub delivery only; actual application `EventChange` payload, reconnect behavior, and hosted-provider connectivity remain unverified.
- [ ] Confirm billing is Free and measure realistic commands/bandwidth from a representative ingestion batch and a browser WebSocket subscriber.
- [ ] Calculate monthly budget using measured command counts, expected event volume, API subscriber count, and chosen scheduler cadence; include retries and headroom.

**Gate:** Persistent TCP and Pub/Sub work from Render and a GitHub-hosted runner, region/latency is acceptable, and forecast usage fits the free ceiling with headroom. If not, pause for an explicit fallback decision (lower cadence, temporarily disable realtime with clear product approval, or a separately evaluated broker).

### Task 4: Deploy the Render static web site

**Files:** Provider configuration only unless a code issue is found: web build settings and `VITE_API_BASE_URL`.

- [x] Connect `matthewubacbrian-afk/geohazard-ph` on `main`.
- [x] Set root directory `web`; build with `npm ci && npm run build`; publish `dist`.
- [ ] Set `VITE_API_BASE_URL` to the final API origin plus `/api/v1` before building. Confirm the generated WebSocket URL is `wss://<api-host>/ws/events` or set a matching explicit `VITE_WS_URL` at build time if needed.
- [x] Initial static deploy succeeded on 2026-11-04 from source SHA `38853d4` (Render reports `Deploy succeeded | Live`; build duration 32.3 seconds).
- [x] Record the public URL: `https://geohazard-ph-staging-web.onrender.com`.
- [ ] Check static assets, client-side routes, map rendering, and browser-console errors before connecting the live API.

**Observed build note:** Vite emitted a non-fatal warning that the minified JavaScript bundle is about 2.48 MB, above its 500 kB advisory threshold. Record for later performance review; it did not prevent the static deploy.

**Gate:** Static site loads over HTTPS and browser routes resolve; actual API calls may remain unavailable until Task 5 is complete. Deploy status and URL are confirmed, but this gate remains open until browser checks are recorded.

### Task 5: Deploy the FastAPI API service

**Files:** Render service settings and secrets. Expected settings: API Docker context/Dockerfile (`backend`, `Dockerfile.prod`), start command bound to `$PORT`, `DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT=staging`, exact `CORS_ORIGINS`, and held/empty `RISK_PROFILE_EXPORT_PATH` behavior.

- [ ] Create a Render Free Web Service in Singapore from the approved release SHA, using the backend production Dockerfile.
- [ ] Override the current fixed-port command with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (or an equivalent supported Render port configuration); verify Render's assigned port is actually honored.
- [ ] Set the managed DB and Redis URLs using Render's secret environment settings. Set `CORS_ORIGINS` to a JSON array containing only the final static-site origin (and a custom domain only if it is configured).
- [ ] Keep `RISK_PROFILE_EXPORT_PATH` pointed to a path that yields an empty list in the release image. Do not add a risk-profile file or model weights to the image.
- [ ] Configure a health check on `/health`, deploy, and inspect logs for startup, database connectivity, and Redis connection without printing secret values.
- [ ] Verify `/health`, `/api/v1/events`, `/api/v1/faults`, `/api/v1/volcanoes`, and `/api/v1/risk-profile/clusters` (expected empty list) over HTTPS.

**Gate:** API health and required read endpoints pass, credentials are not visible in logs, CORS is exact, and free usage/spend controls are checked.

### Task 6: Connect realtime and web/mobile clients

**Files:** Render CORS setting; Render static build environment; mobile staging API setting. Change code only if an observed cross-origin/WebSocket incompatibility fails a documented test.

- [ ] Load the web site and verify a read request reaches the API with no CORS errors.
- [ ] Open `/ws/events` over WSS from the browser and verify it connects, receives a deliberately generated valid `EventChange`, and reconnects after API sleep/restart.
- [ ] Set the mobile app's staging base URL to the Render API origin ending in `/api/v1`; verify foreground event loading and offline-cache behavior on a physical device or emulator.
- [ ] Confirm clients handle API cold starts, retry/loading states, WebSocket disconnection, and an empty held risk-profile list without suggesting official alerts or predictions.

**Gate:** Browser and mobile smoke evidence is recorded; cold start and intermittent free-tier service behavior are acceptable for staging.

### Task 7: Add safe migration and scheduled-ingestion workflows

**Files:** New or modified `.github/workflows` workflow(s), deployment documentation, and possibly a small one-shot operational script. Read `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and workflow conventions before editing.

- [ ] Create a release-only/manual migration job using the approved image SHA and DB secret. Run `alembic upgrade head` once per release before the API depends on new schema; never run migrations on every scheduled ingestion cycle.
- [ ] Create a scheduled ingestion job with `INGEST_MAX_CYCLES=1`, the same immutable API image SHA, `DATABASE_URL`, and `REDIS_URL`. Use non-hour-boundary UTC times to reduce schedule queue delays; choose cadence only after quota budgeting.
- [ ] Ensure secrets are masked, absent from command echo/output, scoped to the staging environment, and unavailable to untrusted fork PRs. Restrict workflow permissions to read packages and required contents/actions scopes.
- [ ] Make the job summary distinguish USGS success/failure from PHIVOLCS success/failure and include counts without sensitive payloads. The current scheduler may log per-source failures and still exit successfully; add a reliable job-level failure signal before treating green status as healthy ingestion.
- [ ] Prevent overlapping runs or document idempotent overlap behavior. Verify retries do not duplicate events and that Pub/Sub command consumption remains within budget.
- [ ] Ensure GHCR package visibility/authentication works for the runner; use least-privilege `GITHUB_TOKEN` package access when private.
- [ ] Verify an action run performs one cycle, updates expected rows, and causes a browser subscriber to receive an event. Test source outage and Redis outage reporting without logging credentials.

**Gate:** Release migration is repeatable and safe for the staging DB; scheduled jobs are observable, non-overlapping, bounded by free quotas, and produce verified source/realtime evidence.

### Task 8: Final staging acceptance and operating routine

**Files:** `docs/runbook.md`, `docs/project-status.md`, and this plan; record only evidence actually observed.

- [ ] Run a checklist covering browser, mobile, API health, PostGIS spatial query, source feed freshness, one realtime event, risk-profile held state, and scene-analysis typed-unavailable behavior.
- [ ] Verify provider dashboards show free plan, resource usage, bandwidth/commands/database size, usage alerts, no accidental paid resource, and no duplicate staging service.
- [ ] Document owner actions for checking Supabase pause notices, retrying failed scheduled jobs, refreshing any changed secrets, importing only cleared static data, exporting/restoring the small staging DB, and retiring services.
- [ ] Update `docs/project-status.md` with the staging URL/service types only if provisioned, plus exact live checks and date. Do not mark the application production-ready based on a free-tier smoke deployment.
- [ ] Keep the OCI runbook as an alternative path and record why this staging target was selected.

**Acceptance:** A user can load the web site, fetch the supported staging API, see at least one verified USGS/PHIVOLCS record if its source is available, receive a realtime `EventChange`, and use the mobile staging URL; migrations, storage, scheduled worker, quotas, and failure modes are documented; no held Epic 5 export or unapproved hazard data is exposed; no unplanned charge is visible.

## Operator Inputs Needed Later

Do not send credentials in chat. During the provider setup steps, the operator will create accounts/projects and enter secrets directly into provider dashboards or GitHub Actions environment secrets.

- A GitHub environment such as `staging` and its approved deployment branch.
- Supabase project and a database connection string using an approved connection mode.
- Upstash Redis TLS TCP connection URL (not REST token/URL) if Task 3 passes.
- Final Render static-site and API URLs; optional custom domain only if one is available and desired.
- Exact `CORS_ORIGINS` value derived from the chosen public web origin.
- A decision on optional GEM staging import after source/license and data-size checks.

Never provide SSH private keys, OCI API keys, database passwords, Redis credentials, GitHub tokens, card numbers, or account passwords to Codex. This proposed split path does not require OCI credentials or an OCI VM. A database backup/restore destination is also needed if staging data must be recoverable; Supabase Free does not include automatic backups.

## Official Provider References

These plan assumptions were checked against provider documentation on 2026-11-04; revisit them during setup because free limits and features can change.

- [Render free services and limitations](https://render.com/docs/free) — static hosting, 15-minute free-service idle sleep, ephemeral filesystem, free Postgres expiry, free Key Value limits, and included-usage behavior.
- [Render regions](https://render.com/docs/regions) — Singapore is a service/datastore region; static sites use a global CDN.
- [Supabase PostGIS guide](https://supabase.com/docs/guides/database/extensions/postgis) — enabling PostGIS and using the dedicated `extensions` schema.
- [Supabase free pricing](https://supabase.com/pricing) and [free project pausing](https://supabase.com/docs/guides/platform/free-project-pausing) — 500 MB DB size, inactivity pause behavior, and absence of free automatic backups.
- [Upstash Redis pricing](https://upstash.com/pricing/redis) — current Free tier data, bandwidth, and command quotas.
- [Upstash protocol compatibility](https://upstash.com/docs/redis/overall/compatibility) and [REST API caveats](https://upstash.com/docs/redis/features/restapi) — native TCP vs HTTP/REST behavior.
- [GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage), [workflow schedule syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), and [schedule delays](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) — public/private runner costs, minimum interval, and queue delays.

## Notes For The Next Session

- Work one provider step at a time. Use the current operations record for active service state; gather evidence for any remaining acceptance checks without repeating completed provisioning steps.
- This plan is a design and execution roadmap, not permission to provision providers, publish a release, import datasets, or change the current OCI account.
- Do not add account credentials to this Markdown file. Replace assumptions with confirmed values only after the operator completes the relevant step.
