# GeoHazard PH - Development Framework

This document preserves the historical phase framework and domain principles.
For current completion, operational prerequisites, and deferred work, use the
[canonical project status](project-status.md).

The project follows a lightweight Agile workflow with phase-based epics:

- Epic 1: MVP earthquake feed, API, and map.
- Epic 2: PHIVOLCS scraping, volcano data, realtime delivery, and deduplication.
- Epic 3: static hazard layers.
- Epic 4: mobile alerts and offline cache.
- Epic 5: regional seismic risk profiles (historical-data ML pipeline).
- Epic 6: landslide and InSAR stretch work; deferred.

These epic labels describe project scope; historical phase summaries and unchecked
plan items are not current status without confirmation in the project status register.

Data correctness is treated as a high-risk concern, especially for ingestion, coordinates, deduplication, and map display.
