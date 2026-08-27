# Runbook

## Ingestion Failure

1. Check which source failed and whether the source is reachable.
2. Inspect the saved raw payload or HTML snapshot.
3. Confirm whether the parser failed because the source shape changed.
4. Disable only the affected source if bad data could reach users.
5. Add or update a fixture before changing parser logic.

## Data Accuracy Concern

1. Treat coordinate, magnitude, alert-level, and deduplication issues as high priority.
2. Preserve raw payloads for reprocessing.
3. Verify against the source site or API before publishing corrections.

## Local Scaffold Check

Run from the repository root:

```bash
python scripts/verify_structure.py
```
