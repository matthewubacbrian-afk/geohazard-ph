# ADR 0001: Record Architecture Decisions

## Status

Accepted

## Context

GeoHazard PH combines public hazard data, spatial queries, a web map, and mobile alerts. Early decisions need to remain visible because ingestion, mapping, and alerting choices affect correctness and deployment complexity.

## Decision

Use Architecture Decision Records in `docs/adr/` for notable technical decisions. Start with Python/FastAPI for backend and ingestion, PostgreSQL/PostGIS for geospatial data, Redis for cache/pub-sub, React/Vite/MapLibre for web, and React Native for mobile.

## Consequences

The monorepo is organized around backend, web, mobile, data, infra, docs, and scripts. Future changes such as moving to Supabase or swapping React Native for Flutter should be recorded in their own ADR.
