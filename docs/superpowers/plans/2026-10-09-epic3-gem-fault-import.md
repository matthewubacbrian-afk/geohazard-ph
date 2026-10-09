# Epic 3 GEM Fault Import — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import and verify an immutable, open-licensed GEM active-fault snapshot in the local GeoHazard PH database with an auditable local receipt and accurate coverage documentation.

**Architecture:** Reuse the existing static-layer parser, CLI, transactional source replacement, and faults API. Download a commit-pinned GeoJSON to the ignored local data directory, record the SHA-256 and validation counts, run a dry-run before applying the snapshot, verify the API result, then update the source/runbook/status documentation.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostGIS, PowerShell, Docker Compose, GeoJSON.

**Spec:** `docs/superpowers/specs/2026-10-09-epic3-gem-fault-import-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/data-sources.md`, and `docs/testing-standards.md`.
- Keep the work on `feat/epic3-gem-fault-import`; do not edit `main`.
- Pin source commit `56816508ad92fd6846dad1163b1c8c01376a2cd1` and license `CC-BY-SA-4.0`.
- Never commit source GeoJSON, generated receipt, credentials, or database dump. Both local files belong under ignored `data/fault_lines/local/`.
- Run the dry-run and inspect its JSON summary before applying the source replacement.
- Do not import PHIVOLCS vectors, infer fault geometry, alter API/schema/migrations, or claim nationwide completeness.
- Conventional Commits. Run backend tests if importer code changes, `python scripts\verify_structure.py` when tracked structure changes, and `git diff --check` before committing.

---

### Task 1: Download the immutable GEM source and verify its local copy

**Files:**
- Create locally (ignored): `data/fault_lines/local/gem_active_faults_harmonized.geojson`
- Read: `data/fault_lines/local/` ignore rule in `.gitignore`.

**Interfaces:**
- Consumes: public raw GeoJSON at the pinned upstream commit.
- Produces: local input file and its SHA-256 value; no tracked data artifact.

- [x] **Step 1: Verify the destination is ignored**

From the repository root:

```powershell
git check-ignore data/fault_lines/local/gem_active_faults_harmonized.geojson
```

Expected: Git reports the matching `data/fault_lines/local/` ignore rule. Stop if the path is not ignored.

- [x] **Step 2: Download the pinned input**

```powershell
$gemCommit = "56816508ad92fd6846dad1163b1c8c01376a2cd1"
$gemUrl = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/$gemCommit/geojson/gem_active_faults_harmonized.geojson"
$gemPath = "data/fault_lines/local/gem_active_faults_harmonized.geojson"
New-Item -ItemType Directory -Force "data/fault_lines/local" | Out-Null
Invoke-WebRequest -Uri $gemUrl -OutFile $gemPath
```

Expected: the GeoJSON exists at `$gemPath` and its URL includes the full commit SHA.

- [x] **Step 3: Calculate the raw SHA-256 and inspect the FeatureCollection header**

```powershell
$gemSha256 = (Get-FileHash -LiteralPath $gemPath -Algorithm SHA256).Hash.ToLowerInvariant()
$gemSourceFeatureCount = @((Get-Content -LiteralPath $gemPath -Raw | ConvertFrom-Json).features).Count
if ($gemSourceFeatureCount -lt 1) { throw "Pinned GEM GeoJSON contains no source features" }
"commit=$gemCommit sha256=$gemSha256 source_features=$gemSourceFeatureCount"
```

Expected: a non-empty source FeatureCollection and a 64-character lowercase SHA-256 are printed.

### Task 2: Validate the source and write the local receipt

**Files:**
- Read: `scripts/import_fault_lines.py` and `backend/ingestion/sources/static_layers.py`.
- Create locally (ignored): `data/fault_lines/local/gem-ph.metadata.json`.

**Interfaces:**
- Consumes: `$gemPath`, `$gemCommit`, `$gemUrl`, `$gemSha256`, and the existing importer CLI.
- Produces: accepted row count in the CLI's structured log and a local JSON receipt with source metadata and dry-run result.

- [x] **Step 1: Ensure the backend virtual environment and PostGIS are ready**

Run from the repository root:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e "backend[dev]"
docker compose up -d postgres redis
Set-Location backend
.venv/Scripts/python.exe -m alembic upgrade head
Set-Location ..
```

Expected: the backend development dependencies install, Postgres and Redis report running, and Alembic upgrades the local schema through the static-layer migration.

- [x] **Step 2: Run the importer in dry-run mode**

```powershell
$env:PYTHONPATH = "backend"
$dryRunLines = & backend/.venv/Scripts/python.exe scripts/import_fault_lines.py $gemPath --source gem --source-url $gemUrl --license-name CC-BY-SA-4.0 --dataset-version $gemCommit --dry-run 2>&1
if ($LASTEXITCODE -ne 0) { throw "GEM import dry-run failed" }
$dryRun = $dryRunLines | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.message -eq "Static layer validated" } | Select-Object -Last 1
if ($null -eq $dryRun -or [int]$dryRun.count -lt 1) { throw "Dry-run did not report any accepted Philippine fault features" }
"accepted_features=$($dryRun.count)"
```

Expected: the existing parser reports `Static layer validated` with a positive `count`; no invalid geometry or CRS error occurs.

- [x] **Step 3: Review the source-to-accepted count and write a receipt**

```powershell
$receipt = [ordered]@{
    source = "gem"
    source_url = $gemUrl
    license_name = "CC-BY-SA-4.0"
    dataset_version = $gemCommit
    sha256 = $gemSha256
    downloaded_at = (Get-Date).ToUniversalTime().ToString("o")
    source_feature_count = $gemSourceFeatureCount
    accepted_feature_count = [int]$dryRun.count
    validation_status = "passed"
}
$receipt | ConvertTo-Json | Set-Content -LiteralPath "data/fault_lines/local/gem-ph.metadata.json" -Encoding utf8
```

Expected: the ignored receipt contains the exact input hash, pinned version, actual feature counts, UTC download time, and passed validation status.

### Task 3: Apply the snapshot and verify the API

**Files:**
- Uses: `scripts/import_fault_lines.py`, `backend/app/services/static_layers.py`, and `backend/app/api/v1/faults.py`.

**Interfaces:**
- Consumes: the reviewed local receipt and the matching validated GeoJSON.
- Produces: one local GEM fault snapshot; the API returns the same accepted count and pinned provenance.

- [x] **Step 1: Apply the same pinned source without dry-run**

```powershell
$applyLines = & backend/.venv/Scripts/python.exe scripts/import_fault_lines.py $gemPath --source gem --source-url $gemUrl --license-name CC-BY-SA-4.0 --dataset-version $gemCommit 2>&1
if ($LASTEXITCODE -ne 0) { throw "GEM import failed; inspect the error before retrying" }
$apply = $applyLines | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.message -eq "Static layer imported" } | Select-Object -Last 1
if ($null -eq $apply -or [int]$apply.count -ne [int]$dryRun.count) { throw "Applied count differs from the validated dry-run count" }
```

Expected: the existing transaction replaces only the `gem` source and its applied count matches the dry-run count.

- [x] **Step 2: Start the local API if it is not already running**

From a separate PowerShell terminal:

```powershell
Set-Location backend
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected: FastAPI listens at `http://127.0.0.1:8000`.

- [x] **Step 3: Compare API count and provenance against the receipt**

From the repository root in another PowerShell terminal:

```powershell
$apiRows = @(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/faults?source=gem")
$receipt = Get-Content -LiteralPath "data/fault_lines/local/gem-ph.metadata.json" -Raw | ConvertFrom-Json
if ($apiRows.Count -ne [int]$receipt.accepted_feature_count) { throw "API count does not match the import receipt" }
if (@($apiRows | Where-Object { $_.source -ne "gem" -or $_.dataset_version -ne $receipt.dataset_version -or $_.license_name -ne $receipt.license_name }).Count -ne 0) { throw "API provenance does not match the import receipt" }
if (@($apiRows | Where-Object { $_.geometry.type -notin @("LineString", "MultiLineString") }).Count -ne 0) { throw "API returned an unexpected geometry type" }
"api_gem_faults=$($apiRows.Count) version=$($receipt.dataset_version)"
```

Expected: the API count equals the receipt's accepted count; every row has GEM source, the pinned version, CC BY-SA 4.0 license, and a fault-line geometry type.

### Task 4: Record the verified snapshot and its limits

**Files:**
- Modify: `docs/data-sources.md`.
- Modify: `docs/runbook.md`.
- Modify: `docs/project-status.md`.

- [x] **Step 1: Update the source record**

Add a GEM snapshot note containing the pinned commit, immutable file URL, CC-BY-SA-4.0 license, observed input SHA-256, source feature count, accepted/imported feature count, and the retrieval/import date. Copy the values from `data/fault_lines/local/gem-ph.metadata.json`; do not copy the ignored source file.

- [x] **Step 2: Make the runbook command reproducible**

Replace the Epic 3 example's `YOUR_SOURCE_COMMIT` placeholder and generic repository URL with the pinned commit and raw file URL used by the import. Keep the dry-run command before the apply command, and retain rollback, attribution, and coverage caveats.

- [x] **Step 3: Update the authoritative project status**

Change the Epic 3 row only after API verification. State that the pinned GEM fault snapshot is locally imported and verified, while PHIVOLCS geometry, volcano zones, and national completeness remain unresolved.

### Task 5: Run required verification and commit documentation

**Files:**
- Verify: all three updated documentation files; ensure ignored local data is not staged.

- [x] **Step 1: Run backend static-layer tests**

```powershell
Set-Location backend
pytest -v tests/unit/test_static_layers.py
Set-Location ..
```

Expected: the static layer parsing and validation tests pass.

- [x] **Step 2: Run the full backend suite and final repository checks**

```powershell
Set-Location backend
pytest -v
Set-Location ..
python scripts\verify_structure.py
git status --short
git diff --check
```

Expected: backend tests pass, all expected project paths exist, only the three intended docs are tracked as modified, ignored input/receipt remain untracked by Git, and `git diff --check` reports no errors.

- [x] **Step 3: Commit the verified documentation update**

```powershell
git add docs/data-sources.md docs/runbook.md docs/project-status.md
git commit -m "docs: record verified GEM fault import"
```

## Notes for the executor

- If Docker, backend dependencies, or the local database are unavailable, complete source download and dry-run only, retain no completion claim for the import, and record the missing local prerequisite in the execution summary.
- If the pinned file cannot be downloaded or the dry-run rejects it, do not switch to a moving upstream branch or partially apply the data. Report the concrete failure and leave the database untouched.
- If a code defect is found in the existing importer, add a focused failing test first, verify it fails for that defect, implement the minimal fix, then run the complete backend suite before proceeding.
