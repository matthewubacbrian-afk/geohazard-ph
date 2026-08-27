# GeoHazard PH - System Architecture

This document belongs to the versioned project docs. The original root-level reference file remains available while the repo is being scaffolded.

The starter architecture has five layers:

- Public data sources: USGS, PHIVOLCS pages, Smithsonian GVP, GEM faults, and stretch GIS datasets.
- Ingestion and ETL: scheduled workers normalize, validate, deduplicate, and persist data.
- Core store: PostgreSQL/PostGIS for spatial data and Redis for cache/pub-sub.
- API: FastAPI REST and realtime endpoints.
- Clients: React web dashboard and React Native mobile app.
