# Project completion plan

Reviewed: 2026-10-17 (Asia/Manila). Baseline: origin/main `173f21be`.

## Goal and completion rule

Deliver the existing public-awareness monitoring scope with verified code, accurate
operational documentation, and explicit release evidence. Each feature uses an
isolated branch/worktree, regression tests, all package suites, configured lint and
build checks, Conventional Commits, a pushed PR, and passing CI before merge.
Update this plan and the status register with every delivery. Preserve existing
quality holds and deferred scope; passing code checks cannot replace permission,
scientific validation, device evidence, or deployed-state verification.

## Epic checklist and distance to completion

| Epic | Implemented evidence | Remaining acceptance gates |
| --- | --- | --- |
| 1: feed/API/map | USGS ingestion, persisted events, interactive dashboard | Reverify suites and deployed feed/health; staging host absent in recorded evidence |
| 2: PHIVOLCS/realtime | Canonical deduplication, committed-event publishing, volcano feed | Operational source/TLS and realtime smoke checks on deployment |
| 3: reference layers | Importer/API/toggles; recorded 155-feature GEM import | PHIVOLCS reuse permission, reviewed vectors, national coverage evidence |
| 4: mobile | Saved locations, foreground nearby alerts, offline cache, native CI | Fix cache isolation/races/storage failures; device-flow evidence; background push and store release remain deferred |
| 5: regional profiles | Historical pipeline, validation/sensitivity reports, API/UI | Integrate credential fix; domain-approved sparse-region policy and new validated artifact; current export remains held |
| 6: stretch | NASA reference overlay merged; InSAR metadata research recorded | InSAR footprint/reuse and independent reference gates; no production deformation claim |
| 7: scene review | Transient API, camera clients, warnings and provisional blur handling merged | Integrate training PR; same-sample baseline evaluation CLI; approved image data, thresholds, real-scene and device/resource validation |
| Staging | Multi-architecture release workflow and published historical bundle | Make held-export mode deployable; host/DNS/configuration and live verification |

A single percentage would obscure these independent gates. The monitoring code is
substantially implemented; the complete operational product is not yet evidenced.
Historical plans are context, not proof that every unchecked historical item is
current scope. No open GitHub issues were returned during this audit. PRs #32 and
#36 are open; #36 conflicts with current main.

## Prioritized delivery queue

- [x] P0 tracking: published this assessment and corrected stale Epic 7/current-process claims in `docs/project-status.md`; PR #39 merged after all five CI checks passed (remote main `f53117e2`).
- [x] P1 verification debt: PR #40 merged at `4004ad3f` after independent review and all five CI checks passed. Backend 148 tests, ML 65 tests, portable Ruff, web build/tests, mobile Jest/TypeScript/Android, and iOS simulator build are required in CI.
- [ ] P0 web map dependency security: upgrade MapLibre GL beyond the affected `<=6.4.0` releases, adapt the Vite worker and imports, verify map behavior and production build, and record the WebGL2 compatibility requirement. This takes priority over the remaining integration queue because the current production dependency has a critical attribution XSS advisory.
- [ ] P1 web development-tool security: separately upgrade vulnerable Vite/Vitest dependency paths after the map fix, with web tests/build and a fresh dependency audit. Keep this separate from the production map migration for reviewability.
- [ ] P1 existing credential fix: review/integrate PR #32; correct its contradictory `docs/runbook.md` dotenv instructions. Preserve shell precedence and artifact hold.
- [ ] P1 staging held-export mode: change `compose.staging.yml`, release packaging/checks and runbook so a deployment can omit a held profile export. Existing API empty-state behavior remains explicit; test both reviewed-export and no-export configurations.
- [ ] P2 mobile cache isolation: scope `mobile/src/services/eventFeed.ts` cached events to normalized API URL and reject superseded results in `mobile/src/navigation/RootNavigator.tsx`. Test server switching, offline fallback and out-of-order responses.
- [ ] P2 mobile persistence resilience: return freshly fetched events even when local cache writes fail, with a separate persistence warning; test rejected writes and usable fresh results.
- [ ] P2 scene training integration: review PR #36, resolve documentation conflicts while preserving Epic 6 records, rerun all checks and merge only after fresh CI.
- [ ] P2 scene baseline CLI: implement same-held-out-sample baseline comparison with explicit label mapping; keep export fail-closed and test incomplete/mismatched comparisons. Derive a focused implementation plan from the integrated training code first.
- [ ] P2 setup consistency: correct Windows README environment paths and outdated runtime/CI descriptions; verify commands against the documented environment layout.
- [ ] P3 release preparation: run available smoke checks, prepare exact operator/device/domain-review evidence requirements, and record unresolved external gates.

## Execution details

Before each behavioral slice, write a focused plan with exact files, interfaces,
regression cases and commands. Add a failing regression, verify the expected
failure, implement the smallest fix, then verify the regression and full suites.
Run backend and ML `pytest -v`, web `npm test` and `npm run build`, mobile
`npm test -- --runInBand` and TypeScript checking, Python Ruff, structure
verification, and `git diff --check`. Provision a dedicated PostGIS test database
and Redis instance; do not run destructive integration fixtures against app data.
Inspect existing PRs in isolated checkouts; leave worktrees owned by other chats
untouched. New worktrees created by this session are archived only after verifying the PR is merged and its merge commit is contained in remote main.

## Known gaps and constraints

- Documentation: stale Epic 7 branch status and present-tense runtime claims;
  Windows quick-start virtual-environment path mismatch; staging/export conflict.
- Bugs: API-independent mobile cache key, out-of-order refresh race, cache-write
  failure discarding fresh network data (audit; regression reproduction pending).
- Weak tests: missing mobile server-switch and rejected-storage cases; no physical
  camera coverage; synthetic scene tests do not establish recognition quality.
- Technical debt: PR #40 resolves the original 18 backend and 11 ML lint findings under explicit package rules. Two applied migrations retain narrowly scoped style exceptions. The web dependency audit still reports nine findings (three moderate, three high, three critical); the production MapLibre path is first, followed by the development-tool path.
- External gates: OCI/DNS, source-owner permission, domain review, image reuse and
  real evaluation data, physical devices and platform-specific runtime evidence.
- No paid infrastructure provisioning, contact with third parties, fabricated
  signoff, or relaxation of scientific/data-quality gates is implied by this plan.

## Session evidence (2026-10-17)

- PR #39 merged the assessment and corrected the Epic 7 status after five green
  CI checks; its worktree and branch were removed after merge verification.
- [Verification baseline plan](docs/superpowers/plans/2026-10-17-verification-baseline.md)
  and PR #40 delivered portable backend/ML Ruff and blocking mobile TypeScript
  checking. Local backend `pytest -v` passed 148 tests with dedicated PostGIS and
  Redis; ML `pytest -v` passed 65 tests; package Ruff, mobile TypeScript,
  structure verification and whitespace checks passed. Fresh PR #40 backend,
  ML, web, mobile/Android and iOS simulator CI all passed before merge.
- Dedicated local test containers `geohazard-session-postgres` (55432) and
  `geohazard-session-redis` (56379) are session test services, not staging
  evidence. Stop/remove only these when no further tests need them.
- The [MapLibre security design](docs/superpowers/specs/2026-10-17-maplibre-security-design.md)
  and [implementation plan](docs/superpowers/plans/2026-10-17-maplibre-security.md)
  define the next isolated slice. No release, domain, permission, or device gate
  is cleared by dependency or verification changes.
