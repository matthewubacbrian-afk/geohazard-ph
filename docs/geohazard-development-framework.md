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
- Epic 6: landslide reference overlay implemented; InSAR remains deferred research.
- Epic 7: camera scene review demonstrator; local browser inference delivered,
  with real-scene evaluation and mobile/server inference acceptance open.

These epic labels describe project scope; historical phase summaries and unchecked
plan items are not current status without confirmation in the project status register.

Data correctness is treated as a high-risk concern, especially for ingestion, coordinates, deduplication, and map display.

## Completion evidence

Reviewed: 2026-11-06. Evaluate each epic separately for implemented behavior,
deployed operation, data rights, scientific validation and device acceptance.
Use [the current queue](../PLAN.md#current-delivery-queue-2026-11-06) and
[dated staging acceptance](staging-acceptance-2026-11-06.md); an unchecked item
in a historical plan is current only when reconfirmed there. Core monitoring
acceptance does not require completing the deferred InSAR research workstream.
