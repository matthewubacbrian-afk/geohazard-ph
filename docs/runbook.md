# Runbook

## Ingestion Failure

1. Check which source failed and whether the source is reachable.
2. Inspect the saved raw payload or HTML snapshot.
3. Confirm whether the parser failed because the source shape changed.
4. Disable only the affected source if bad data could reach users.
5. Add or update a fixture before changing parser logic.

## Ingestion & Worker

Start the polling worker locally from `backend/`:

```bash
python -m ingestion.scheduler
```

By default the scheduler waits at least 60 seconds after each cycle (configured via `INGEST_POLL_INTERVAL_SECONDS` in environment/settings). Each cycle runs USGS and PHIVOLCS ingests independently; if one source fails, the other continues and the error is logged with structured fields (`source` and exception). `SIGTERM`/`SIGINT` interrupts the wait immediately; an active cycle finishes before shutdown.

For a local one-shot run, set `INGEST_MAX_CYCLES=1` in the command's environment. Positive values bound the number of cycles; unset means continuous polling. Leave this variable unset for the Docker worker, whose production `restart: unless-stopped` policy would otherwise repeatedly restart bounded runs.

Apply database migrations from `backend/`:

```bash
alembic upgrade head
```

To target a specific database (for example the integration test database), pass the URL on the command line:

```bash
alembic -x db_url=postgresql+psycopg://geohazard:geohazard@localhost:5432/geohazard_test upgrade head
```

When a source feed is unreachable:

1. Confirm the ingest logs `ingest source failed` with `extra={"source": "usgs"|"phivolcs"}` and check the underlying exception in the logs.
2. Verify the source status, URL, and credentials (USGS requires no API key; verify network egress).
3. Respect the one-minute minimum poll cadence (default 60s, configurable via `INGEST_POLL_INTERVAL_SECONDS`); do not hammer the feed.
4. Confirm the bounding box (`PH_BBOX`) and filters are still valid if an ingest runs but returns zero events.
5. For USGS-specific failures, `USGSFetchError` may be raised by the adapter; inspect logs for details.

### API — regional event summary

`GET /api/v1/events/summary` returns aggregate statistics (event_count, avg_magnitude, max_magnitude, latest_occurred_at) for events within a bounding box. The bounding box defaults to the Philippines (PH_BBOX) and may be overridden with west/south/east/north query params; an optional region_name labels the response. The web dashboard card uses this endpoint.

## Data Accuracy Concern

1. Treat coordinate, magnitude, alert-level, and deduplication issues as high priority.
2. Preserve raw payloads for reprocessing.
3. Verify against the source site or API before publishing corrections.

## Local Scaffold Check

Run from the repository root:

```bash
python scripts/verify_structure.py
```

## Canonical Event Reconciliation

The matcher now rebuilds groups from current source rows during nonempty ingestion.
Before rolling this change into a database that already contains events, take a
database backup and inspect the proposed changes during a maintenance window:

```bash
cd backend
python -m ingestion.reconcile
python -m ingestion.reconcile --apply
```

The first command rolls back its changes and logs inspected and changed row counts.
The second commits them. Check `/api/v1/events` and `/api/v1/events/summary`
afterward. Browsers reconcile through their periodic REST refresh; the maintenance
command does not publish WebSocket messages. Rows without a stable source
`external_id` use a content key and need source-level review if revised.

## Portable Staging Release

The manual **Prepare Staging Release** workflow runs backend and web checks,
publishes API and web images to GHCR under the commit SHA, and uploads a deployment
bundle. It does not connect to a host. The bundle contains `compose.staging.yml`,
the Caddyfile, the deploy script, and `.env.staging.example`.

### Oracle Cloud Infrastructure Always Free A1

This repository and its release workflow do not create OCI resources or provision
a VM; the operator performs the instance and network setup in the OCI Console.

Oracle Always Free compute is provisioned only in the tenancy's home region. The
published Always Free A1 allowance is a total of 2 OCPUs and 12 GB memory across
A1 instances, plus 200 GB total block volume allowance. Capacity is not guaranteed:
A1 shapes may be unavailable in a home region. Choosing paid capacity or exceeding
free quotas can incur charges. Review [Always Free resources and limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
and Oracle's [launch an instance tutorial](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/launchinginstance.htm)
before provisioning.

1. In the OCI Console, select the tenancy's **home region** and open **Compute → Instances → Create instance**.
2. Name the instance, select **Ubuntu 24.04** as the image, and choose the **VM.Standard.A1.Flex** shape. Configure no more than the available A1 free allowance (2 OCPUs and 12 GB memory total); confirm the console identifies the selected image and shape as Always Free eligible before creating it.
3. Select or create a VCN and a **public subnet** with a route to an internet gateway. Assign a public IPv4 address. Add your SSH public key during instance creation. Keep the private key private; never upload it to the repository or deployment bundle.
4. Inspect every security list attached to the subnet and every network security
   group attached to the instance; their ingress rules apply cumulatively. Remove
   any broad inbound TCP 22 rule whose source is `0.0.0.0/0` or `::/0`, then add
   an inbound TCP 22 rule limited to your current operator IP in CIDR form. Allow
   TCP 80 and 443 from clients (`0.0.0.0/0`, and `::/0` only if IPv6 is
   configured). Do not open TCP 5432 or 6379. Permit outbound DNS and HTTPS/network
   access so the host can reach GHCR, DNS resolvers, and configured event-source
   feeds. See [OCI security list rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm).
5. Create a DNS A record for the deployment hostname pointing to the instance's public IPv4 address. Wait until the name resolves to that address before deployment; Caddy needs working DNS and publicly reachable ports 80/443 to obtain TLS certificates.
6. Connect from Windows PowerShell using the private key you created or selected:

   ```powershell
   ssh -i "$env:USERPROFILE\.ssh\oci_geohazard" ubuntu@<public-ip>
   ```

   Replace the key path and address with your own values. On the VM, verify the architecture with `uname -m`; it must print `aarch64`.
7. Install Docker Engine and the Compose plugin by following Docker's [official Ubuntu installation instructions](https://docs.docker.com/engine/install/ubuntu/). Verify both commands:

   ```bash
   docker --version
   docker compose version
   ```

   Configure the Ubuntu host firewall while keeping SSH reachable. Replace
   `<operator-cidr>` with your current public IP as a single-host CIDR (for
   example `203.0.113.10/32`); do not create a public SSH rule. OCI security-list
   or network-security-group rules are a separate firewall and must also allow
   the intended traffic. Inspect current rules and remove every broad SSH rule
   before adding the restricted one:

   ```bash
   sudo ufw status numbered
   ```

   If the status lists a broad TCP 22 rule, substitute its displayed number and
   run this command; repeat the status check because rule numbers change after
   each deletion. Skip this command if no broad SSH rule exists:

   ```bash
   sudo ufw delete "replace-with-rule-number"
   ```

   Then add SSH access only for the operator's current public IP as a single-host
   CIDR, replacing the placeholder with the actual address:

   ```bash
   sudo ufw allow from "replace-with-operator-cidr" to any port 22 proto tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   sudo ufw status
   ```

   Confirm the SSH rule is present before enabling UFW, and keep an active SSH
   session open while checking that a new SSH connection still works. If your
   public IP changes, update both the UFW rule and the OCI ingress rule before
   reconnecting.

For other Linux hosts, retain the existing requirements: Docker Compose v2, a DNS
name pointing to the host, inbound ports 80 and 443, and outbound access to GHCR
and the event sources.

### Prepare and deploy a release

1. On the repository's `main` branch, run the manual **Prepare Staging Release**
   workflow. Record the 40-character commit SHA and download the artifact named
   `staging-release-<sha>` from that same workflow run. The artifact contains
   `compose.staging.yml`, `infra/caddy/Caddyfile`, `scripts/deploy_staging.sh`,
   and `.env.staging.example`; extract all files together into one directory on
   the VM, preserving the `infra/caddy` and `scripts` paths.
2. If the GHCR packages are private, authenticate with a GitHub token that has only
   `read:packages` access. Do not put the token in a command argument, shell
   history, or committed file. Enter it at the prompt:

   ```bash
   read -r -p 'GitHub username: ' ghcr_user
   read -r -s -p 'GHCR token: ' ghcr_token; printf '\n'
   printf '%s' "$ghcr_token" | docker login ghcr.io -u "$ghcr_user" --password-stdin
   unset ghcr_token
   ```

   Restrict access to Docker's credential configuration. Docker may store
   credentials in `~/.docker/config.json` when no credential helper is configured;
   prefer a credential helper where available, and otherwise protect the directory
   and file. Log out of GHCR after deployment if desired with
   `docker logout ghcr.io`.

   ```bash
   chmod 700 ~/.docker
   if [ -f ~/.docker/config.json ]; then chmod 600 ~/.docker/config.json; fi
   ```
3. Confirm the published API and web image manifests include both ARM64 and
   AMD64. Use the actual image prefix and SHA from the workflow:

   ```bash
   docker buildx imagetools inspect ghcr.io/owner/geohazard-ph-api:<sha>
   docker buildx imagetools inspect ghcr.io/owner/geohazard-ph-web:<sha>
   ```

   Replace `owner` and `<sha>` with the workflow's image prefix and release SHA;
   each manifest must list `linux/arm64` and `linux/amd64`.
4. Generate the production ML output from the repository root on your Windows
   development machine. Normal training requires `KAGGLE_USERNAME` and
   `KAGGLE_KEY` environment variables or credentials in
   `%USERPROFILE%\.kaggle\kaggle.json`. The trainer does not load credentials from
   the repository `.env`; do not rely on that file for Kaggle authentication.
   The `-Offline` option skips Kaggle downloads and is appropriate only when the
   needed local CSV inputs already exist under `ml/data/raw/`:

   ```powershell
   .\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1
   # Only when local training inputs exist:
   .\scripts\train_risk_profile_models.ps1 -ArtifactVersion v1 -Offline
   ```

   The output is `ml/model_artifacts/v1/risk_profiles.json`. Keep each trained
   export immutable and versioned with its release SHA on the VM. Transfer it from
   PowerShell to a release-specific filename; replace `RELEASESHA` below with the
   same 40-character SHA used for the images:

   ```powershell
   ssh -i "$env:USERPROFILE\.ssh\oci_geohazard" ubuntu@<public-ip> "mkdir -p -m 700 /home/ubuntu/geohazard-release/deploy-data"
   scp -i "$env:USERPROFILE\.ssh\oci_geohazard" .\ml\model_artifacts\v1\risk_profiles.json "ubuntu@<public-ip>:/home/ubuntu/geohazard-release/deploy-data/risk_profiles_RELEASESHA.json"
   ```

   The extracted bundle directory must be `/home/ubuntu/geohazard-release` in
   this example. Connect to the VM and, in its terminal, change into that directory
   before validating the export:

   ```bash
   cd /home/ubuntu/geohazard-release
   ```

   Keep this directory as the working directory for the remaining `.env.staging`,
   Compose, backup, deployment, and recovery commands. Validate that the JSON is
   a non-empty list of objects whose fields match `RiskProfile` in
   `backend/app/schemas/risk_profile.py`. This standard-library check needs no
   Pydantic installation on the VM:

   ```bash
   python3 - <<'PY'
   import json
   import math
   from pathlib import Path

   path = Path("./deploy-data/risk_profiles_RELEASESHA.json")
   assert path.is_file() and path.stat().st_size > 0, "risk profile export is missing or empty"
   data = json.loads(path.read_text(encoding="utf-8"))
   assert isinstance(data, list) and data, "expected a non-empty JSON list"

   def valid_profile(item):
       return (
           isinstance(item, dict)
           and isinstance(item.get("region_name"), str)
           and bool(item["region_name"].strip())
           and isinstance(item.get("cluster"), int)
           and not isinstance(item["cluster"], bool)
           and isinstance(item.get("label"), str)
           and isinstance(item.get("confidence"), (int, float))
           and not isinstance(item["confidence"], bool)
           and math.isfinite(item["confidence"])
           and isinstance(item.get("feature_importances"), dict)
           and all(
               isinstance(key, str)
               and isinstance(value, (int, float))
               and not isinstance(value, bool)
               and math.isfinite(value)
               for key, value in item["feature_importances"].items()
           )
           and isinstance(item.get("model_version"), str)
           and isinstance(item.get("generated_at"), str)
           and isinstance(item.get("dataset_snapshot"), str)
       )

   assert all(valid_profile(item) for item in data), "one or more profiles do not match RiskProfile fields"
   print(f"Validated {len(data)} risk profiles")
   PY
   chmod 600 ./deploy-data/risk_profiles_RELEASESHA.json
   test -s ./deploy-data/risk_profiles_RELEASESHA.json && test -r ./deploy-data/risk_profiles_RELEASESHA.json
   ```

   These are historical descriptive statistical profiles, not predictions. The
   fixture at `backend/tests/fixtures/risk_profiles.json` is for local tests and is
   not the production export.
5. Copy `.env.staging.example` to `.env.staging` in that same directory. Replace
   all placeholders: set `IMAGE_PREFIX` to the workflow's GHCR prefix, `IMAGE_TAG`
   to the exact commit SHA, `SITE_DOMAIN` to the DNS hostname, a strong
   `POSTGRES_PASSWORD`, a matching URL-encoded password in `DATABASE_URL`, and
   `CORS_ORIGINS` to a JSON array containing `https://<site-domain>`. Set
   `RISK_PROFILE_EXPORT_FILE` to the host export path (for example
   `./deploy-data/risk_profiles_RELEASESHA.json`) and set
   `INGEST_POLL_INTERVAL_SECONDS` as desired. Compose resolves a relative host
   path from the directory containing `compose.staging.yml`. Restrict permissions
   on deployment secrets and exports:

   ```bash
   chmod 600 .env.staging
   chmod 700 ./deploy-data
   chmod 600 ./deploy-data/risk_profiles_RELEASESHA.json
   ```

   Keep `.env.staging`, database backups, and model exports private and out of
   version control. The web bundle uses same-origin `/api/v1` and derives `wss://`
   from its public HTTPS origin. For rollback, update `.env.staging` so
   `IMAGE_TAG` and `RISK_PROFILE_EXPORT_FILE` point to the matching prior release
   SHA together, and pass that same SHA to the deploy script. The script argument
   sets the effective `IMAGE_TAG`. Keep each versioned export until no release or
   rollback needs it.
6. Ensure the deployment URL, `SITE_DOMAIN`, Caddy's site hostname, and DNS name
   all match. From the extracted bundle directory, deploy with the exact interface:

   ```bash
   bash scripts/deploy_staging.sh <40-character-release-sha> https://<site-domain>
   ```

   The script validates Compose, pulls immutable images, starts services, waits
   for health, and checks the health, events, and risk-profile endpoints. Confirm
   the release afterward:

   ```bash
   curl --fail https://SITE_DOMAIN/health
   curl --fail https://SITE_DOMAIN/api/v1/events
   curl --fail https://SITE_DOMAIN/api/v1/risk-profile/clusters
   docker compose --env-file .env.staging -f compose.staging.yml ps
   docker compose --env-file .env.staging -f compose.staging.yml logs --tail=100 api worker web proxy postgres redis migrate
   ```

   Replace `SITE_DOMAIN` in the curl URLs with the actual hostname. For GHCR
   authentication errors, log in as above and retry
   `docker compose --env-file .env.staging -f compose.staging.yml pull`. For DNS,
   TLS, or connection failures, confirm the A record, public IP, OCI ingress rules,
   and host firewall allow ports 80/443. For a missing model export, inspect
   `docker compose --env-file .env.staging -f compose.staging.yml config` and run
   `test -s ./deploy-data/risk_profiles_RELEASESHA.json` after replacing
   `RELEASESHA` with the active release SHA. For disk pressure, inspect `df -h`
   and `docker system df`. For unhealthy services, use the `ps` and `logs`
   commands above and resolve the first failing dependency before retrying.

### Backup, restore, rollback, and cleanup

Before each update, create database and Caddy data backups from the extracted
bundle directory. The date-based names below use UTC. Each temporary file is
validated before being renamed to its final name, so a failed dump or archive does
not appear as a complete backup. The Caddy archive includes both `/data` (durable
ACME certificates and related state) and `/config`; treat it as secret material
because it contains TLS private keys, and protect its storage accordingly:

```bash
(
  set -euo pipefail
  umask 077
  mkdir -p -m 700 backups
  chmod 700 backups
  backup_date="$(date -u +%Y%m%dT%H%M%SZ)"
  if [[ -e "backups/geohazard-${backup_date}.dump" || -e "backups/caddy-state-${backup_date}.tar.gz" ]]; then
    echo "Backup names already exist; wait and retry." >&2
    exit 1
  fi
  pg_dump_tmp="$(mktemp "backups/.geohazard-${backup_date}.dump.XXXXXX")"
  caddy_tmp="$(mktemp "backups/.caddy-state-${backup_date}.tar.gz.XXXXXX")"
  trap 'rm -f -- "$pg_dump_tmp" "$caddy_tmp"' EXIT
  docker compose --env-file .env.staging -f compose.staging.yml exec -T postgres pg_dump -U geohazard -d geohazard -Fc > "$pg_dump_tmp"
  docker compose --env-file .env.staging -f compose.staging.yml exec -T proxy tar -C / -czf - data config > "$caddy_tmp"
  docker compose --env-file .env.staging -f compose.staging.yml exec -T postgres pg_restore --list < "$pg_dump_tmp" > /dev/null
  tar -tzf "$caddy_tmp" > /dev/null
  chmod 600 "$pg_dump_tmp" "$caddy_tmp"
  mv -- "$pg_dump_tmp" "backups/geohazard-${backup_date}.dump"
  mv -- "$caddy_tmp" "backups/caddy-state-${backup_date}.tar.gz"
)
```

Restore a database dump only when intentionally replacing the current database.
This overwrites current database contents. First capture a fresh backup using the
commands above, stop API and worker services, then drop and recreate the database
and restore the chosen custom-format dump:

```bash
docker compose --env-file .env.staging -f compose.staging.yml stop api worker
docker compose --env-file .env.staging -f compose.staging.yml exec -T postgres dropdb -U geohazard --if-exists geohazard
docker compose --env-file .env.staging -f compose.staging.yml exec -T postgres createdb -U geohazard -O geohazard geohazard
docker compose --env-file .env.staging -f compose.staging.yml exec -T postgres pg_restore --no-owner -U geohazard -d geohazard < backups/geohazard-YYYYMMDDTHHMMSSZ.dump
docker compose --env-file .env.staging -f compose.staging.yml up -d --wait
curl --fail https://SITE_DOMAIN/health
```

Replace the dump placeholder with the chosen backup filename and `SITE_DOMAIN`
with the actual hostname. Restore Caddy's saved state, if needed, using a temporary
Compose container attached to the same named volumes:

```bash
docker compose --env-file .env.staging -f compose.staging.yml stop proxy
docker compose --env-file .env.staging -f compose.staging.yml run --rm -T --no-deps --entrypoint tar proxy -C / -xzf - < backups/caddy-state-<date>.tar.gz
docker compose --env-file .env.staging -f compose.staging.yml start proxy
```

Never run `down -v` during routine updates or recovery; it deletes named volumes.

To roll back application images, verify database migration compatibility and
rerun `bash scripts/deploy_staging.sh <prior-40-character-release-sha> https://<site-domain>`.
Image rollback alone does not reverse database migrations. Restore the database
only using the explicit procedure above if schema or data changes must also be
reverted.

Keep exports and backups until they are no longer needed, then remove them
securely. To stop the Compose stack while preserving volumes, run
`docker compose --env-file .env.staging -f compose.staging.yml down` (without
`-v`). If permanently retiring the deployment, delete the OCI VM and any attached
boot or block volumes and public IP that are no longer needed, and remove the DNS
record. Review block volumes in the tenancy's home region so unused resources do
not remain unnoticed.

Before the first deployment to a populated database, back up Postgres and run
the canonical reconciliation preview and apply commands using the release API
image during a maintenance window. From the extracted bundle directory, after
setting `.env.staging`, run:

```bash
export IMAGE_TAG=<release-commit-sha>
docker compose --env-file .env.staging -f compose.staging.yml pull
docker compose --env-file .env.staging -f compose.staging.yml up -d postgres redis
docker compose --env-file .env.staging -f compose.staging.yml run --rm migrate
docker compose --env-file .env.staging -f compose.staging.yml run --rm --no-deps api python -m ingestion.reconcile
docker compose --env-file .env.staging -f compose.staging.yml run --rm --no-deps api python -m ingestion.reconcile --apply
```

For an empty database, migrations run automatically as a one-shot Compose
service before the API starts. Postgres and Redis health checks gate startup,
and the worker waits for a healthy API. The staging worker runs ingestion once
per cycle and waits five minutes after each cycle, including failed source attempts.

Run from the extracted bundle directory:

```bash
bash scripts/deploy_staging.sh <release-commit-sha> https://staging.example.com
```

The script validates Compose, pulls the immutable images, starts the stack,
waits for health, and checks `/health`, `/api/v1/events`, and
`/api/v1/risk-profile/clusters`. Caddy obtains and
renews TLS certificates for `SITE_DOMAIN` and forwards `/api/` and `/ws/` to
the API. Its certificate state and Postgres data use persistent Docker volumes.
The old release SHA is the rollback target: rerun the script with that SHA after
checking schema compatibility. Restore the database backup if a migration or
data reconciliation must be undone. Review `docker compose -f compose.staging.yml
ps` and service logs when health checks fail.

## Epic 2 realtime channel (Person B)

Start Redis and the API, then open the dashboard. `GET /api/v1/subscribe` checks
broker connectivity; the dashboard shows LIVE only while its socket is open.
The Nginx configuration forwards `/ws/` with WebSocket upgrade headers.
Container API/worker Redis and database addresses use Compose service names.

For a custom browser API host, set `VITE_API_BASE_URL` in `web/.env.local`.
The WebSocket URL is derived from that API base using ws/wss and `/ws/events`.
An explicit `VITE_WS_URL=wss://your-host/ws/events` override is also supported in
that file. Restart Vite after environment edits.

The scheduler passes committed canonical event changes to the publisher.
The browser also refreshes the REST event list every 30 seconds.

Redis pub/sub is best-effort, without durable replay. Lost publications recover
through REST; never retry the database transaction because publishing failed.
Each browser uses its own Redis subscription, closed on disconnect. Revisit shared
fan-out if concurrent-client volume warrants it. Multi-process APIs each have
independent subscriptions. No mobile push or managed subscriptions are introduced.

Run backend tests with local PostGIS and Redis available. Realtime integration
tests use a unique test channel so fixture events never enter the live dashboard.
The source tests use saved HTML and never make external network calls.

Backend CI provisions both PostGIS and a health-checked Redis service and sets
`REDIS_URL` explicitly. If the realtime integration test fails while opening a
WebSocket with code 1013, check Redis availability first: subscription happens
before the handshake is accepted. Adding sleeps after publication cannot repair
a failed connection. `TestClient`'s `receive_json()` waits for the next message
and does not accept a `timeout` argument.

## PHIVOLCS volcano bulletins

Use the dashboard's **Volcano bulletins** view or `GET /api/v1/volcanoes`.
The API refreshes on demand at most once every five minutes per process.
Concurrent requests share one fetch. Failed refresh attempts are rate-limited
to once per minute. Cached failures are labelled stale for at most one hour;
older or missing data produces a retryable 503, never synthetic bulletin data.

Settings in the root environment:

| Variable | Default |
| --- | --- |
| `PHIVOLCS_VOLCANO_URL` | `https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin` |
| `PHIVOLCS_VOLCANO_TIMEOUT_SECONDS` | 15 |
| `PHIVOLCS_VOLCANO_CACHE_SECONDS` | 300 |
| `PHIVOLCS_VOLCANO_STALE_SECONDS` | 3600 |

A TLS/network failure raises `PhivolcsFetchError`; changed/invalid HTML raises
`PhivolcsParseError`. Both are logged by class without secret-bearing exception
text. Diagnose the source outside the request path. If the network uses a private
CA, configure a trusted CA bundle through Requests' `REQUESTS_CA_BUNDLE`; do not
disable TLS verification. During implementation on 2026-09-08 the live host failed
certificate-chain validation in this environment. Fixture parsing and endpoint
behavior were verified; a verified live fetch must be retried once trust/source
certificate configuration is corrected.

## Import static layers (Epic 3)

Start PostGIS, install backend dependencies, and apply migration `0003`:

```bash
docker compose up -d postgres redis
backend/.venv/bin/pip install -e 'backend[dev]'
(cd backend && .venv/bin/alembic upgrade head)
```

Obtain reviewed source files using `docs/data-sources.md`. From the repository root:

```bash
PYTHONPATH=backend backend/.venv/bin/python scripts/import_fault_lines.py \
  data/fault_lines/gem_active_faults_harmonized.geojson \
  --source gem \
  --source-url https://github.com/GEMScienceTools/gem-global-active-faults \
  --license-name CC-BY-SA-4.0 --dataset-version YOUR_SOURCE_COMMIT --dry-run
```

Repeat without `--dry-run` to persist the validated snapshot. Use `--source phivolcs`
for reviewed atlas vectors, supplying their source URL, version and license/permission.
For volcano polygons add `--kind volcano_zones`. The command accepts `.geojson`, `.json`
or `.shp` with its sibling files; PDF digitization is a separate GIS task.

A refresh atomically replaces that source in the selected layer, preserving other
sources. Use complete snapshots, not partial updates. Stable identifiers survive
reimport; obsolete features are removed. Invalid or empty imports retain prior data.
Concurrent refreshes serialize using a transaction advisory lock.

Enable **Fault lines** or **Volcano zones** in the dashboard. Loading, empty and retry
states appear independently of live events; source attribution accompanies loaded layers.
Changing basemaps restores the current overlays and visibility settings.

Smoke check `/api/v1/faults` and `/api/v1/volcano-zones` after import. Verify source names,
versions, counts and geometry against the source map. An empty response means no
reference features have been imported, not that an area has no hazard.

For PowerShell, set `$env:PYTHONPATH = "backend"`, use the backend virtual environment's
`Scripts/python.exe`, and pass the same CLI arguments on one line.

Rollback code only after exporting imported data if needed: migration downgrade to
`0002` drops both reference tables.

For this working session a validated 155-feature GEM subset is available locally at
`data/fault_lines/local/gem-ph.geojson`, with source/subset SHA-256 checksums and provenance
in `gem-ph.metadata.json`. It is intentionally ignored by Git. Use it as the CLI input
with `--dataset-version downloaded-2026-09-10` after starting PostGIS.
