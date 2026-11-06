# Mobile advisory identities — Design

**Date:** 2026-10-20

## Problem

The Release inventories in PR #54 list 34 npm dependency-chain findings but omit the underlying advisory identifiers and installed versions. Reviewers cannot connect a finding to a specific affected range without regenerating npm's raw audit payload, which the workflow intentionally does not retain.

## Goals

- Record each finding's installed lockfile node version, npm advisory source ID, advisory URL, and affected range in the small Android and iOS reports.
- Preserve deterministic output and the existing `undetermined` disposition.
- Reject malformed lockfile or advisory fields instead of silently producing partial evidence.

## Non-goals

- Do not classify exploitability, affected API use, build-only status, or attack paths.
- Do not upload raw audit JSON, source maps, bundles, APKs, or apps.
- Do not update dependencies or app behavior.

## Context And Constraints

`scripts/mobile_artifact_inventory.py` consumes a fresh npm audit and Release source map. Its `dependency_paths` are npm install locations, not a shortest path from the root dependency. `mobile/package-lock.json` maps those locations to exact resolved versions. The workflow already has the lockfile and audit payload during both native builds. Follow `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md` for script changes.

## Alternatives Considered

- A separate report would duplicate package and platform observations and make reviewers reconcile two artifacts.
- Querying advisory services at report time would add network dependence and could diverge from the audit result used in that CI run.
- Chosen: enrich the current report from the existing audit JSON and tracked lockfile, preserving one snapshot per platform.

## Design

### Architecture and data flow

Pass `--lockfile mobile/package-lock.json` to the existing script. Parse its `packages` object and use each audit `nodes` location as a key. For each finding, retain the existing fields and add sorted `installed_nodes` (`path`, `version`), sorted `via_packages` for string entries in `via`, and sorted `advisory_references` for direct advisory objects in `via` (`source`, `url`, `range`). A chain entry can have an empty `advisory_references` list and a `via_packages` link to the affected child. No risk label changes.

### Components and interfaces

- `scripts/mobile_artifact_inventory.py`: `build_report(platform, source_map_path, artifact_path, audit_json_path, lockfile_path)` accepts the additional required path. `main()` requires `--lockfile`. Every audit node must resolve to a package object with a nonempty string `version`. Every `via` entry must be a nonempty package string or object with a positive integer `source`, nonempty HTTPS `url`, and nonempty `range`; only these evidence fields are emitted.
- `.github/workflows/mobile-ci.yml`: both Android and iOS inventory invocations pass `mobile/package-lock.json`.
- `scripts/tests/test_mobile_artifact_inventory.py` and workflow tests: assert exact enriched report fields and failure paths.

### Configuration, error handling, and data

No new environment variable or persistent schema. Invalid inputs raise `ValueError` with a package-specific message; the CLI exits nonzero and CI does not upload a misleading success report. Keep stable sorted ordering and omit advisory titles or raw audit payload content.

## Rollout

One isolated branch and PR. Run focused tests, full package suites/linters/structure checks, and five CI checks. Inspect both generated reports on the final commit before merge.

## Files

- `scripts/mobile_artifact_inventory.py` — parse the lockfile and enrich findings.
- `scripts/tests/test_mobile_artifact_inventory.py` — report and malformed-input tests.
- `scripts/tests/test_mobile_ci_workflow.py` — required workflow argument test.
- `.github/workflows/mobile-ci.yml` — pass lockfile to both inventories.
- `docs/mobile-artifact-evidence-2026-10-20.md` — describe identity evidence and its limits.
- `PLAN.md` and `docs/project-status.md` — current epic tracking.

## Testing Strategy

Small fixture audit and lockfile tests prove direct and inherited findings, exact versions, deterministic order, and invalid missing/malformed evidence. Workflow test proves both platforms pass `--lockfile`. Run the full backend, ML, web, and mobile suites and configured lint/build checks; CI confirms native builds and reports.

## Acceptance Criteria

- [ ] Every real audit finding in both final reports has installed version evidence and either a direct advisory reference or an inherited package link.
- [ ] All findings remain `undetermined`.
- [ ] Focused tests and all five CI checks pass on the reviewed PR head.
- [ ] Plan and status match merged code and remaining exposure-review work.

## Out Of Scope (backlog)

Shortest root-to-node dependency path, affected API use, attack-path analysis, New Architecture readiness, and supported framework migration remain separate Epic 4 work.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-20-mobile-advisory-identities.md`.
- Terminology: `docs/glossary.md`.
