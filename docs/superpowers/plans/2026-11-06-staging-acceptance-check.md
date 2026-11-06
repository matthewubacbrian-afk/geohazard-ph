# Staging Acceptance Check — Implementation Plan

> **For agentic workers:** Use the test-driven-development and verification-before-completion skills for this bounded change.

**Goal:** Collect a repeatable staging ingestion and feed snapshot on demand.

**Architecture:** A Python CLI reads recent scheduled runs from GitHub and public
staging health and source event lists over HTTPS. The runbook covers the separate
browser recovery check and how to interpret the snapshot.

**Tech Stack:** Python 3.11+, GitHub CLI, unittest.

## Global Constraints

- Follow `AGENTS.md` and the repository Python and verification standards.
- Use bounded calls with TLS verification. Read public endpoints and run metadata.
- Report event occurrence time separately from workflow time. Keep raw event rows
  and authentication diagnostics out of the report.
- Keep the check on demand. Browser recovery and database restore need their own evidence.

### Task 1: Collect the staging snapshot

**Files:** Create `scripts/check_staging_acceptance.py` and
`scripts/tests/test_check_staging_acceptance.py`. Update `docs/runbook.md` and
`.github/workflows/backend-ci.yml` to document and run the fixture-based tests.

**Interfaces:** From the repo root, run `python scripts/check_staging_acceptance.py`.
The command writes JSON with a UTC observation timestamp, health status, recent
scheduled run metadata, consecutive successful runs, and source counts and
latest `occurred_at` values. Exit 0 means evidence was collected. Exit 1 means
a required response or GitHub query could not be read or validated.

- [x] Add fixture-based tests for scheduled-run ordering, failed runs, empty feeds,
  timezone-aware event times, bounded cold-start retry and safe error output.
- [x] Observe failing tests before adding the collector.
- [x] Implement the CLI and document how to confirm reconnect and a later live
  notification in the browser. Run fixture tests and lint in CI.
- [x] Run the fixture tests, Ruff, structure check, whitespace check and one live
  staging snapshot. Record the result without treating it as sustained operation.
- [ ] Commit the change with Conventional Commits and open a PR.

## Notes for the executor

The live command uses the existing public staging URL and an authenticated
`gh` session. Tests inject responses and never contact staging or GitHub.
