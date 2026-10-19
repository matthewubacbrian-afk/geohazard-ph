# Project completion plan

Reviewed: 2026-10-18 (Asia/Manila). Initial audit baseline: origin/main `173f21be`.

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
| 5: regional profiles | Historical pipeline, validation/sensitivity reports, API/UI; Kaggle `.env` credential loader merged | Domain-approved sparse-region policy and new validated artifact; current export remains held |
| 6: stretch | NASA reference overlay merged; InSAR metadata research recorded | InSAR footprint/reuse and independent reference gates; no production deformation claim |
| 7: scene review | Transient API, camera clients, warnings and provisional blur handling merged | Integrate training PR; same-sample baseline evaluation CLI; approved image data, thresholds, real-scene and device/resource validation |
| Staging | Multi-architecture release workflow; held-export default and reviewed-export override implemented | Prepare a new bundle, then host/DNS/configuration and live verification; profile publication still needs Epic 5 approval |

A single percentage would obscure these independent gates. The monitoring code is
substantially implemented; the complete operational product is not yet evidenced.
Historical plans are context, not proof that every unchecked historical item is
current scope. No open GitHub issues were returned during the initial audit.
PR #32 was incorporated through PR #43; PR #36 remains in the integration queue.

## Prioritized delivery queue

- [x] P0 tracking: published this assessment and corrected stale Epic 7/current-process claims in `docs/project-status.md`; PR #39 merged after all five CI checks passed (remote main `f53117e2`).
- [x] P1 verification debt: PR #40 merged at `4004ad3f` after independent review and all five CI checks passed. Backend 148 tests, ML 65 tests, portable Ruff, web build/tests, mobile Jest/TypeScript/Android, and iOS simulator build are required in CI.
- [x] P0 web map dependency security: PR #41 merged at `59a0c75e` after the web suite (175 tests), production build, browser map smoke check, zero production audit findings, and five green CI checks. The patched MapLibre migration includes a WebGL2 fallback; its isolated worktree and branch were removed after merge verification.
- [x] P1 web development-tool security: PR #42 merged at `a31197b0` after a clean `npm ci`, 175 web tests, production build, zero full/production audit findings (down from eight), independent review and five green CI checks. Its isolated worktree and branch were removed after merge verification.
- [x] P1 existing credential fix: PR #43 merged at `5877a0c8`, incorporating PR #32's loader, correcting `docs/runbook.md`, and isolating tests from a developer's real `.env`. Local ML tests passed 72/72, focused tests 12/12, Ruff, structure and whitespace checks passed; independent review's finding was fixed and all five CI checks passed. Both merged branches and worktrees were removed. See the [focused integration plan](docs/superpowers/plans/2026-10-18-kaggle-credential-integration.md).
- [x] P1 staging held-export mode: [PR #45](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/45) merged at `a80d9adc` after all five CI checks passed. The base Compose deployment omits the held export and verifies an empty profile list; a separate, explicit reviewed-export override verifies a non-empty list. Release packaging, CI checks, deploy-script tests, and the runbook cover both modes. See the [focused plan](docs/superpowers/plans/2026-10-18-staging-held-export.md). Live deployment remains gated by a host and DNS, and profile publication remains gated by Epic 5 review.
- [ ] P2 mobile cache isolation: scope `mobile/src/services/eventFeed.ts` cached events and initial restoration to the normalized API URL. Test server switching, offline fallback, and rejection of the old unscoped cache. See the [focused plan](docs/superpowers/plans/2026-10-18-mobile-cache-isolation.md).
- [ ] P2 mobile refresh ordering: reject superseded responses from repeated same-URL manual refreshes in `mobile/src/navigation/RootNavigator.tsx`; test out-of-order responses. The cache-isolation slice handles cross-server invalidation.
- [ ] P2 mobile persistence resilience: return freshly fetched events even when local cache writes fail, with a separate persistence warning; test rejected writes and usable fresh results.
- [ ] P2 mobile dependency audit triage: a 2026-10-18 `npm audit --omit=dev` reported 42 findings (10 moderate, 31 high, 1 critical), with direct findings in React Native 0.75 and React Navigation 6 and a critical transitive `shell-quote` finding. Assess which code reaches the shipped app, identify compatible updates and native-build impact, then plan bounded upgrades. A raw audit count is not an app exploitability finding.
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

- Documentation: some historical Epic 7 and runtime descriptions and the Windows
  quick-start virtual-environment path still need reconciliation. The staging/export
  conflict is addressed by the held-export deployment mode.
- Bugs: API-independent mobile cache key, out-of-order refresh race, cache-write
  failure discarding fresh network data (audit; regression reproduction pending).
- Weak tests: missing mobile server-switch and rejected-storage cases; no physical
  camera coverage; synthetic scene tests do not establish recognition quality.
- Technical debt: PR #40 resolves the original 18 backend and 11 ML lint findings under explicit package rules. Two applied migrations retain narrowly scoped style exceptions. The baseline web audit reported nine findings; PR #41 removed the production finding and PR #42 removed the remaining eight development-tool findings in their respective audited lockfiles.
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
  define the current isolated slice. Local focused MapView tests passed 34/34;
  the full web suite passed 175/175 across 35 files; `npm run build` emitted a
  bundled worker asset; `npm audit --omit=dev` reported zero findings. The full
  audit retains eight development-tool findings. Independent review, browser
  smoke, and all five feature PR CI checks passed; PR #41 merged at `59a0c75e`.
  No release, domain, permission, or device gate is cleared by dependency or
  verification changes.
- The web development-tool branch passed a clean `npm ci`, 175/175 tests across
  35 files, production build with bundled map worker, zero full and production
  audit findings, structure verification, and whitespace check. Vitest 5 needed
  one constructable MapView test mock; app behavior was unchanged. Independent
  review and all five CI checks passed; PR #42 merged at `a31197b0`.
- PR #43 merged the Kaggle credential loader at `5877a0c8`, and GitHub marked
  PR #32 merged through that history. The branch corrected the contrary runbook
  statement and passed 72 ML tests, ML Ruff, structure and whitespace checks.
  Independent review found and the branch fixed two tests' dependence on the
  developer's real `.env`; all five CI checks passed. Both merged worktrees and
  branches were removed. The loader has not downloaded data or changed the held
  profile export.
