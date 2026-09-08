# Epic 2 Person A - Implementation Plan

> **For agentic workers:** Execute this plan task-by-task. Keep the checklist updated as work is completed.

**Objective:** Implement the PHIVOLCS earthquake feed and cross-source canonicalization so USGS and PHIVOLCS reports of the same earthquake are stored with one canonical identity, one display-primary event, and correct `/events` filtering.

**Scope:** Person A owns the earthquake adapter, ingest transaction seam, canonical matching, persistence migration, `/events` queries, and scheduler integration. Person B owns Redis publishing, `/ws/events`, web live updates, and the PHIVOLCS volcano feed.

**References:**
- `docs/adr/0002-epic2-realtime-phivolcs-contracts.md`
- `docs/superpowers/specs/2026-08-29-epic2-realtime-phivolcs-design.md`
- `docs/superpowers/plans/2026-08-29-epic2-realtime-phivolcs.md`

## How It Works

1. The USGS and PHIVOLCS adapters convert source payloads into the same `HazardEvent` schema.
2. `ingest_events` upserts each source record using `(source, external_id)` so both providers remain auditable.
3. Before committing, `match_and_link` compares candidate rows by time, distance, and magnitude. A true match receives one shared `canonical_id`.
4. The matching group is assigned one `is_primary` row. PHIVOLCS wins; otherwise the earliest event wins. The other source row remains stored with `is_primary=false`.
5. The transaction commits the fully resolved rows. Only after commit does `ingest_events` call Person B's `on_committed` callback with every changed row, including demotions.
6. `/events` reads the persisted decision: primary rows are returned by default, while `include_duplicates=true` exposes the source rows for audit and debugging.

This order is important: the database is authoritative, canonicalization happens before broadcast, and downstream consumers never need to recalculate whether two events are duplicates.

## Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, and `docs/glossary.md`.
- Canonicalization runs synchronously before `session.commit()` and before the post-commit callback.
- The callback receives every touched row, including rows demoted from `is_primary=true` to `false`.
- Preserve both source rows and their `source`/`external_id`; never collapse matched rows into one database row.
- PHIVOLCS wins the `is_primary` tie-break. Without PHIVOLCS, use earliest `occurred_at`, then earliest `created_at`.
- Matching requires all tolerance dimensions: time +/-120 seconds, distance approximately 5 km, and magnitude delta approximately 0.5.
- Do not modify Person B's publisher, WebSocket, web, or volcano files.

## Checklist

### A1. Implement PHIVOLCS earthquake ingestion

**How to implement:** Follow the existing USGS adapter pattern. Keep HTTP fetching and source parsing at the ingestion boundary, validate required fields there, normalize timestamps to UTC, and return typed `HazardEvent` objects to the service layer.

- [x] Add a real parser and `fetch_recent_events(settings)` in `backend/ingestion/sources/phivolcs_earthquake.py`.
- [x] Map records to `HazardEvent` with `hazard_type="earthquake"` and `source="phivolcs"`.
- [x] Preserve the PHIVOLCS external identifier when available; keep unavailable magnitude/depth values nullable.
- [x] Add typed fetch/parse failure handling consistent with the backend error rules.
- [x] Add a saved response fixture and DB-free parser tests in `backend/tests/unit/test_phivolcs_earthquake_parser.py`.

### A2. Add the ingest commit seam

**How to implement:** Make `ingest_events` the one shared transaction path for all earthquake sources. Track the ORM rows touched during upsert, call `match_and_link(session)`, flush if IDs are needed, commit once, then convert the touched rows into `EventChange` values for the callback.

- [ ] Add the `EventChange` schema with the ADR fields and snake_case wire names.
- [ ] Generalize `ingest_usgs_events` into `ingest_events(session, events, on_committed=None)`.
- [ ] Keep per-source upsert behavior based on `dedup_key`.
- [ ] Run canonicalization before commit.
- [ ] Build changes from all inserted, updated, and primary-status-flipped rows.
- [ ] Invoke `on_committed(changes)` only after a successful `session.commit()`.
- [ ] Keep an optional compatibility wrapper only if existing callers still require it.
- [ ] Add unit tests proving the callback receives resolved rows after commit.

### A3. Persist canonical identity

**How to implement:** Add the columns to the SQLAlchemy model and add them in one additive Alembic migration. Set existing rows to self-canonical primaries so the migration does not change their visible behavior. Index `(canonical_id, is_primary)` because list and summary queries depend on it.

- [ ] Add `canonical_id`, `is_primary`, and `match_confidence` to `HazardEvent`.
- [ ] Create Alembic migration `0002_add_hazard_event_canonical.py`.
- [ ] Backfill existing rows with `canonical_id=id` and `is_primary=true`.
- [ ] Add the composite index on `(canonical_id, is_primary)`.
- [ ] Keep the existing unique constraint on `(source, external_id)`.
- [ ] Verify the migration against the PostGIS integration database.

### A4. Implement cross-source matching

**How to implement:** Keep the mathematical matching and tie-break rules in small, DB-independent helpers, then let `match_and_link` load candidate ORM rows and persist the result. Compare only earthquake rows from different sources; require every tolerance to pass; reuse an existing canonical ID when either row is already linked.

- [ ] Add pure matching helpers in `backend/app/services/dedup.py` where practical.
- [ ] Implement `match_and_link(session)` for unmatched and late-arriving rows.
- [ ] Use a haversine distance calculation and explicit tolerance settings/constants.
- [ ] Assign a shared `canonical_id` and `match_confidence` to matching rows.
- [ ] Recompute `is_primary` deterministically when a match is found.
- [ ] Ensure re-ingestion is order-independent and does not repeatedly create new identities.
- [ ] Add DB-free tests for:
  - [ ] true USGS/PHIVOLCS match;
  - [ ] aftershock sequence that must remain separate;
  - [ ] PHIVOLCS arriving after USGS and demoting the USGS row;
  - [ ] magnitude just outside tolerance;
  - [ ] distance just outside tolerance.

### A5. Update `/events` and `/events/summary`

**How to implement:** Keep filtering and grouping in `app/services/events.py`; keep the route thin. Add `is_primary=true` to the default list predicate, skip that predicate only for `include_duplicates=true`, and make summaries count canonical primary rows rather than raw source rows.

- [ ] Update `list_events` to accept `source` and `include_duplicates`.
- [ ] Default list queries to `is_primary=true`.
- [ ] Return all source rows when `include_duplicates=true`.
- [ ] Add the `source` and `include_duplicates` query parameters to the route.
- [ ] Include canonical fields in the event response needed by consumers.
- [ ] Update summary queries to count canonical primary events and support `source`.
- [ ] Add integration coverage for default primary-only results, duplicate opt-in, source filtering, and canonical summary counts.
- [ ] Update API contract and glossary documentation if response fields or terms change.

### A6. Connect the scheduler

**How to implement:** Have the scheduler fetch USGS and PHIVOLCS data independently, pass both lists through `ingest_events`, and log source, fetched count, changed count, and failures. The scheduler may wire Person B's callback, but must not contain Redis or WebSocket logic.

- [ ] Add PHIVOLCS earthquake ingestion to `backend/ingestion/scheduler.py`.
- [ ] Route both USGS and PHIVOLCS through `ingest_events`.
- [ ] Replace scheduler `print()` calls with structured logging.
- [ ] Confirm the scheduler passes Person B's publisher callback without importing or implementing publisher logic.

## Testing

### Unit tests, no database or network

Run from `backend/`:

```bash
pytest -v tests/unit/test_phivolcs_earthquake_parser.py
pytest -v tests/unit/test_canonicalize.py
pytest -v tests/unit/test_ingest_events.py
```

Cover parser mapping, fetch/parse failures, callback timing, matching tolerances, tie-break behavior, and aftershock non-merging.

### Integration tests, provisioned PostGIS

Run from `backend/` with the repository's integration services available:

```bash
pytest -v tests/integration/test_canonical_dedup.py
pytest -v tests/integration/test_events_source_filter.py
pytest -v tests/integration/test_events_api.py
```

Verify migrations apply, both source rows survive, canonical IDs are shared for true matches, primary rows are selected by default, and `include_duplicates=true` exposes both rows.

### Final verification

From the repository root:

```bash
pytest -v
python scripts/verify_structure.py
git diff --check
```

The completion bar is: all checklist items are checked, the four canonicalization scenarios pass, and no Person B-owned files were modified.
