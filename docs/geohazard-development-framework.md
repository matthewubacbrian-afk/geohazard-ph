# GeoHazard PH - Development Framework

This document belongs to the versioned project docs. The original root-level reference file remains available while the repo is being scaffolded.

The project follows a lightweight Agile workflow with phase-based epics:

- Epic 1: MVP earthquake feed, API, and map.
- Epic 2: PHIVOLCS scraping, volcano data, realtime delivery, and deduplication.
- Epic 3: static hazard layers.
- Epic 4: mobile alerts and offline cache.
- Epic 5: landslide and InSAR stretch work.

Data correctness is treated as a high-risk concern, especially for ingestion, coordinates, deduplication, and map display.
