# Mobile advisory paths — Design

**Date:** 2026-10-20

## Problem

PR #55 records six direct advisory references across five affected mobile npm packages, but the 34 npm chain findings still lack a concise, reviewable explanation of how the affected packages enter the production dependency graph and what operation each advisory requires. A raw npm count or absent source-map package name cannot support a risk disposition.

## Goals

- Record installed versions, shortest observed production-graph root paths, advisory IDs/links, and affected-operation preconditions for all six direct advisories.
- Distinguish observed package paths and source-map absence from unverified affected-API use, native inclusion, and attack-path reachability.
- Keep all 34 finding dispositions undetermined and identify the next evidence required to change them.
- Update the tracked Epic 4 plan/status after PR #55 merged.

## Non-goals

- Do not claim that the findings are exploitable, build-only, unreachable, or remediated.
- Do not change dependencies, mobile behavior, CI, or the Release report schema.
- Do not commit raw npm tree/audit output or generated app artifacts.

## Context And Constraints

The final PR #55 Android/iOS Release reports contain 34 finding rows, 25 source-map package names, five directly affected packages, six direct references, and 29 inherited `via` links. All five directly affected package names are absent from both maps. `npm ls braces fast-xml-parser image-size node-forge sprintf-js --omit=dev --package-lock-only --all --json` reads the tracked lockfile and yields root paths; this is a production dependency graph, not a packaged-code graph. Official GitHub Advisory Database pages describe affected operations and version ranges. Follow `CODING_STANDARDS.md`, `docs/testing-standards.md`, and the project's no-unfounded-safety-claim rule.

## Alternatives Considered

- Add a shortest-path algorithm to the Release report now: more automation, but npm's peer/hoisting semantics could produce misleading paths without broader testing and would add another native CI cycle.
- Infer build-only status from package names and source-map absence: faster but unsupported because native/static code and build outputs are not fully attributed.
- Chosen: a dated review record using npm's lockfile-only tree and primary advisory sources, with explicit limits and reproducible commands. A later code slice can automate path checks if ongoing maintenance warrants it.

## Design

### Architecture and data flow

Use PR #55's final reports as the advisory/version snapshot. Use npm's production-graph tree to record the shortest observed root-to-affected-package path, retaining the second `fast-xml-parser` path as context. Read each advisory's affected-operation description from its canonical GitHub Advisory Database page. A single table connects six IDs to five packages, versions, paths, required input/operation, and current evidence limit. Do not convert path evidence into a risk disposition.

### Components and interfaces

- `docs/mobile-advisory-exposure-review-2026-10-20.md`: dated evidence, six source-linked rows, reproducibility commands, unresolved checks, and exact `undetermined` status.
- `docs/mobile-artifact-evidence-2026-10-20.md` and `docs/mobile-dependency-audit-2026-10-19.md`: link the review without replacing the original artifact observations.
- `PLAN.md`, `docs/project-status.md`, and the PR #55 focused plan: record PR #55 as merged and the remaining API/attack-path work as an open gate.

### Configuration, error handling, and data

No code, configuration, API, or schema change. Do not publish raw source maps, npm audit JSON, APKs, or apps. Advisory URLs and affected ranges are dated observations that may change with future advisories; rerun this review after dependency migration.

## Rollout

One documentation branch and PR, separately reviewed. Run structure, link/ID consistency, whitespace checks and all five CI checks. This record can merge without clearing the Epic 4 advisory or device gate.

## Files

- `docs/mobile-advisory-exposure-review-2026-10-20.md` — six-advisory path and precondition record.
- `docs/mobile-artifact-evidence-2026-10-20.md` — link to the review.
- `docs/mobile-dependency-audit-2026-10-19.md` — link to the review.
- `PLAN.md`, `docs/project-status.md` — current Epic 4 tracking.
- `docs/superpowers/plans/2026-10-20-mobile-advisory-identities.md` — close the merged PR #55 plan.

## Testing Strategy

Verify the five package names, versions, six GHSA IDs, and shortest paths against the saved final PR #55 reports and a fresh lockfile-only npm tree. Check links against the six official advisory pages. Run `git diff --check`, `python scripts/verify_structure.py`, package suites and lint/build commands where locally available, and require five green CI checks. No new test mirrors this documentation-only record.

## Acceptance Criteria

- [ ] All six direct references and installed versions match both final PR #55 reports.
- [ ] Each affected package has a reproducible shortest observed production-graph path and an operation precondition linked to its advisory.
- [ ] All risk dispositions remain undetermined, with specific unresolved evidence listed.
- [ ] Plan, status, and prior focused plan agree with PR #55's merged state.
- [ ] Independent review and five exact-head CI checks pass before merge.

## Out Of Scope (backlog)

Affected API call-site verification in transitive consumers, untrusted-input/attack-path tracing, native binary attribution, New Architecture readiness, supported framework migration, and device-flow evidence remain separate work.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-20-mobile-advisory-paths.md`.
- Terminology: `docs/glossary.md`.
