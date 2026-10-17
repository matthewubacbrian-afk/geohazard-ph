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

- [ ] P0 tracking: publish this assessment and correct stale Epic 7/current-process claims in `docs/project-status.md`.
- [ ] P1 verification debt: resolve the 18 backend and 11 ML baseline Ruff findings and enforce lint plus mobile TypeScript checks in CI before behavioral merges. Preserve semantics and existing regression coverage.
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
- Technical debt: fresh baseline Ruff checks found 18 backend findings and 11 ML findings. These must be resolved before claiming full lint compliance.
- External gates: OCI/DNS, source-owner permission, domain review, image reuse and
  real evaluation data, physical devices and platform-specific runtime evidence.
- No paid infrastructure provisioning, contact with third parties, fabricated
  signoff, or relaxation of scientific/data-quality gates is implied by this plan.

## Session evidence

- Read repository standards, glossary, testing/git contracts, current remote
  history, status, historical roadmap and the two open PRs.
- Read-only GPT Astra audit identified the prioritized defects above.
- Created isolated `codex/project-completion-plan` from current remote main.
- Fresh baseline checks are in progress; no suite-pass claim is made yet.

## Usage-limit handoff (2026-10-17)

- Assessment/plan committed as `be99c53e`, pushed in PR #39; independent review
  found no important issues. Structure and whitespace checks passed.
- PR #39 backend, ML and web CI passed at the last check; native mobile jobs were
  still pending. No feature or documentation PR was merged by this session.
- The GPT Astra implementation agent hit its usage limit before making source
  changes. `codex/verification-baseline` is clean at the plan commit.
- Local baseline: backend collection failed because Pillow was absent. Declared
  Pillow 12.3.0 and NumPy 2.2.6 are now installed; backend suite needs rerunning.
- Local ML suite and web/mobile dependency installations were still running at
  handoff. Do not report them as passed without collecting their final results.
- Dedicated test containers: `geohazard-session-postgres` on port 55432 and
  `geohazard-session-redis` on port 56379. These are session test services, not
  staging deployment evidence. Stop/remove only these session containers when
  no longer needed; do not touch existing project data or other chat services.
- Resume with the portable lint/CI baseline slice, then existing PR integration,
  staging held-export mode, and mobile cache defects in the queue above.
- Existing quality holds and external gates remain unchanged. All authored
  repository changes are committed and pushed; no implementation is claimed.

Final collected baseline results: ML **63 passed**. Web and mobile dependency
installation completed. Web installation reported nine dependency audit findings
(three moderate, three high, three critical); investigate the dependency paths and
compatible remediation before release, without applying force upgrades blindly.
Web/mobile local test/build runs remain outstanding. These collected results
supersede the pending-install/test observations above.
