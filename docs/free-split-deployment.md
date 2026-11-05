# Free Split Staging Deployment

Last verified checkpoint: 2026-11-05 (Asia/Manila). This is the current operations
record. The [rollout plan](superpowers/plans/2026-11-04-free-split-staging-deployment.md)
retains historical setup checks. Oracle is not the active deployment path.

## Service Links

| Service | Link or role |
| --- | --- |
| Web | [Staging dashboard](https://geohazard-ph-staging-web.onrender.com/) |
| API health | [Health check](https://geohazard-ph-staging-api.onrender.com/health) |
| Earthquakes | [All events](https://geohazard-ph-staging-api.onrender.com/api/v1/events), [PHIVOLCS](https://geohazard-ph-staging-api.onrender.com/api/v1/events?source=phivolcs), [USGS](https://geohazard-ph-staging-api.onrender.com/api/v1/events?source=usgs) |
| Reference layers | [Faults](https://geohazard-ph-staging-api.onrender.com/api/v1/faults), [volcano bulletins](https://geohazard-ph-staging-api.onrender.com/api/v1/volcanoes) |
| Regional profiles | [Clusters](https://geohazard-ph-staging-api.onrender.com/api/v1/risk-profile/clusters); empty while the export is held |
| WebSocket | `wss://geohazard-ph-staging-api.onrender.com/ws/events` |
| Operations | [Render](https://dashboard.render.com/), [Supabase](https://supabase.com/dashboard), [Upstash](https://console.upstash.com/) |
| Source and automation | [Repository](https://github.com/matthewubacbrian-afk/geohazard-ph), [ingestion workflow](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/workflows/ingest-staging.yml), [release workflow](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/workflows/deploy-staging.yml) |

Use the staging projects in the authenticated dashboards. Database connection
strings and Redis credentials are secrets and are deliberately absent here.

## Data Flow

```text
USGS + PHIVOLCS earthquake feeds
  -> GitHub Actions: one bounded ingestion cycle
       -> Supabase Postgres/PostGIS: upsert events and resolve canonical events
       -> Upstash Redis TCP/TLS: publish committed EventChange messages

Browser on Render Static Site -> HTTPS REST -> Render FastAPI -> Supabase
Browser                       <- WSS relay <- Render FastAPI <- Upstash Pub/Sub
Mobile app                    -> same API (staging acceptance still pending)
```

Supabase and Upstash do not communicate directly. The worker writes to the
database and publishes after commit. The API reads the database and relays Redis
messages. The browser also refreshes REST events every 30 seconds; that does not
fetch new source data. Redis delivery is best effort and has no durable replay.

GEM fault features are a separate static import. Volcano bulletins are a separate
PHIVOLCS adapter, not earthquake ingestion. Regional profiles are a separately
reviewed offline export; source ingestion does not train or publish those labels.

## Configuration Ownership

| Location | Setting | Purpose |
| --- | --- | --- |
| Render API secrets | `DATABASE_URL`, `REDIS_URL` | Supabase SQLAlchemy/psycopg connection and Upstash TLS TCP connection |
| Render API environment | `ENVIRONMENT=staging`, `CORS_ORIGINS` | Staging mode; exact web origin as a JSON array |
| Render static build | `VITE_API_BASE_URL` | `https://geohazard-ph-staging-api.onrender.com/api/v1` |
| Render static build | Optional `VITE_WS_URL` | Normally derived from the API base; if set, use the WSS address above |
| GitHub `staging` environment secrets | `STAGING_DATABASE_URL`, `STAGING_REDIS_URL` | Same staging connections, scoped to workflow execution |
| GitHub `staging` environment variable | `STAGING_RELEASE_SHA` | Published immutable worker-image commit SHA |
| GitHub repository variable | `STAGING_INGEST_ENABLED` | `true` enables scheduled ingestion; `false` skips scheduled jobs |

Current worker SHA: `5c33057841dd9ae1a2df91926b626b94a78bed0a`.
Current enable variable: `true`, verified through GitHub on 2026-11-05.
Web build settings above describe the required contract; live environment values
and browser CORS/WSS acceptance still need a recorded end-to-end check.

## Release And Ingestion Procedure

1. Merge reviewed code into `main`. Deploy the static web and API through their
   existing Render services. Record each Render deploy's source SHA and outcome;
   publishing GHCR images alone does not redeploy those services.
2. If a release changes schema, pause ingestion and run `alembic upgrade head`
   from `backend/` using the reviewed release and staging database secret in a
   secure operator environment. Record the revision before and after. There is
   currently no dedicated automated split-deployment migration workflow. Do not
   put credentials into command text or logs; do not run migrations every cycle.
3. Run **Prepare Staging Release** on the desired commit. Wait for publication
   and image-architecture verification to succeed.
4. Set `STAGING_RELEASE_SHA` only to that published full commit SHA. This selects
   `ghcr.io/matthewubacbrian-afk/geohazard-ph-api:<sha>` for the worker.
5. Run **Ingest Staging Events** manually, inspect per-source fetched/processed
   counts, then verify the source-specific API links above and event timestamps.
   Manual dispatch runs even when the enable variable is `false`.
6. Check provider usage and re-enable scheduled ingestion when the release and
   free quota budget are verified. See [the ingestion runbook](runbook.md#free-split-staging-ingestion).

The configured cron is `17 */6 * * *` in UTC: 02:17, 08:17, 14:17, and 20:17
in Asia/Manila. GitHub can delay or skip scheduled triggers. The first automatic
trigger has not yet been recorded as successful in this checkpoint.
Each run has a 15-minute timeout, concurrency group `staging-ingest`, one cycle
(`INGEST_MAX_CYCLES=1`), and strict source failure reporting
(`INGEST_FAIL_ON_SOURCE_ERROR=true`). A failed source still allows the other
source to be attempted, then the job exits unsuccessfully.

## Verified Evidence

- [PHIVOLCS fix PR #83](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/83)
  restored verified TLS using the standard CA bundle plus the checked-in
  GlobalSign intermediate and handled the compressed response. TLS remains on.
- [Release run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41995260585)
  passed publication and architecture verification for the worker SHA above.
- [Manual ingestion run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41999595044)
  succeeded: 40 USGS and 299 PHIVOLCS fetched/processed. The public API then
  returned 339 events, including 299 PHIVOLCS events. Latest observed PHIVOLCS
  occurrence: 2026-11-05 16:01 Asia/Manila (08:01 UTC). Counts change over time.
- [Cadence PR #84](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/84)
  changed the schedule from 30 minutes to six hours at the operator's choice.
- Earlier live checks found 155 GEM fault features, five volcano bulletins,
  and zero risk-profile clusters. These are dated observations, not fixed totals.

## Free Plan Controls And Usage

Operator-reported dashboard figures on 2026-11-05:

| Provider | Plan and controls | Observed usage |
| --- | --- | --- |
| Render | Hobby, no card, $0 month-to-date and projected | 3.85/750 free hours, 8 MB/5 GB bandwidth, 4/500 pipeline minutes |
| Supabase | Free, no payment method; dashboard reports spend cap enabled | No invoice; database size and egress totals still need recording |
| Upstash | Free Tier, $0 cost | 87/500,000 commands, 86 KB/10 GB bandwidth, 0 B/250 MB storage before the ingestion run |
| GitHub | Public repository, standard hosted runner | Standard runner time is free; GHCR image storage/bandwidth is currently free |

At 339 events per cycle, 120 cycles per 30-day month imply about 40,680 Redis
publish commands. The current code republishes every fetched event, including
unchanged records. This estimate excludes reconnects, subscribers, retries,
manual runs, and feed growth. It is not measured monthly usage.

Review usage weekly during staging and after feed-volume changes. Keep paid
upgrades and add-ons off. Render can suspend services/builds without a payment
method when included usage is exhausted. Supabase Free can restrict service at
quota limits. Upstash applies plan limits by default; its documentation says
adding a payment method converts free resources to pay-as-you-go. The operator
could not locate Auto Upgrade, so no claim of inspecting that toggle is made.
Free plans can sleep, pause, throttle, or become unavailable; this is staging.

Official references, reviewed 2026-11-05:
[Render Free](https://render.com/docs/free),
[Render bandwidth](https://render.com/docs/outbound-bandwidth),
[Supabase cost controls](https://supabase.com/docs/guides/platform/cost-control),
[Upstash upgrades](https://upstash.com/docs/redis/howto/upgrade-database),
[Upstash pricing](https://upstash.com/pricing/redis),
[GitHub runner billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[GHCR billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages).

## Recovery And Remaining Acceptance

- To stop recurring work, set repository variable `STAGING_INGEST_ENABLED=false`.
  This does not cancel an already running job. Inspect failures and API results
  before manually retrying; manual dispatch bypasses that switch.
- For a worker regression, pause the schedule, select a previously verified
  published `STAGING_RELEASE_SHA`, and test manually. Image rollback does not
  reverse database migrations; schema recovery requires a reviewed backup plan.
- Change connection secrets in both Render and GitHub when rotating credentials.
  Redeploy/restart affected services, test one ingestion cycle, then re-enable.
- Check Supabase pause notices and restore through its dashboard if necessary.
  Do not add artificial keep-alive traffic or upgrade a plan to hide free-tier limits.
- Separate paid services, duplicate staging instances, domains, model hosting,
  and paid monitoring are not required by this deployment.

Still open: measured post-ingestion Redis usage and Supabase size/egress;
first scheduled-trigger evidence; browser CORS, ingestion-generated WSS delivery
and reconnect after API sleep; physical/emulated mobile staging checks;
repeatable split-deployment migrations; a securely stored database backup and
tested restore procedure; deployed scene-analysis availability/resource checks.
The colocated Compose backup procedure in the runbook is not a tested Supabase
backup procedure.

Regional shading remains blocked by the [profile quality hold](risk-profile-quality-review-2026-10-14.md)
and [domain review record](epic5-domain-review-decision-record.md). A later approval
record identifying the exact reviewed export version/hash has not been supplied.
Do not load the held export just to make the map shaded.
