# GeoHazard PH - Project Overview

Reviewed: 2026-11-06 (Asia/Manila). Use [project status](project-status.md) for
completion and [PLAN.md](../PLAN.md) for the current acceptance queue.

GeoHazard PH aggregates public geohazard records and reference layers for
awareness and preparedness in the Philippines. It is a deployed demonstrator;
it does not issue official warnings, predict earthquakes or determine safe places.

## Implemented monitoring scope

- Earthquake ingestion from USGS and PHIVOLCS, canonical event matching, REST API
  and browser realtime delivery. Staging has a six-hour ingestion schedule configured;
  manual refresh is verified and automatic triggering remains unverified. Browser
  REST refresh and WSS do not themselves fetch new source data.
- PHIVOLCS volcano bulletins and sourced reference overlays. GVP is part of the
  source architecture; it is not established here as an accepted live staging feed.
- Interactive web map, imported GEM fault references, recorded regional activity
  counts and the optional coarse NASA susceptibility reference.
- Mobile saved locations, foreground radius matching and offline cache, with dated
  physical Android acceptance against a local API. Background push and store
  publishing are deferred; current staging and physical iOS acceptance remain open.
- Local browser scene review, deployed and exercised on public fixtures. It is an
  uncalibrated visual-cue demonstrator; mobile uses a separate server inference path.

## Remaining scope and release gates

PHIVOLCS vector permission and national coverage remain unresolved. The historical
regional ML export is held pending domain policy and validation; activity shading
counts records and does not release those labels. Representative scene evaluation,
phone performance, mobile/server model provisioning and remaining device checks are
open. InSAR remains research with no measured displacement layer.

## Active deployment

Render serves the static web app and FastAPI API; Supabase stores PostGIS data;
Upstash relays post-commit messages; GitHub Actions runs the selected published
worker image. Oracle/colocated Compose is an alternative deployment path.

See [deployment operations](free-split-deployment.md),
[November 6 staging acceptance](staging-acceptance-2026-11-06.md), and
[system architecture](geohazard-system-architecture.md). A successful manual
cycle or browser fixture test does not establish sustained operational or
scientific readiness.
