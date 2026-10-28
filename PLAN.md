# Project completion plan

Reviewed: 2026-10-28 (Asia/Manila). Initial audit baseline: origin/main `173f21be`.

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
| 4: mobile | Saved locations, foreground nearby alerts, URL-scoped and ordered offline cache, native CI, Release-artifact and advisory-identity evidence, New Architecture build readiness and configured Release startup CI checks on React Native 0.75.5; critical advisory patched and unused navigation removed | Per-advisory API/attack-path review, New Architecture device flows, supported framework migration, and post-migration device evidence; background push and store release remain deferred |
| 5: regional profiles | Historical pipeline, validation/sensitivity reports, API/UI; Kaggle `.env` credential loader merged | Domain-approved sparse-region policy and new validated artifact; current export remains held |
| 6: stretch | NASA reference overlay merged; InSAR metadata research recorded | InSAR footprint/reuse and independent reference gates; no production deformation claim |
| 7: scene review | Transient API, camera clients, warnings and provisional blur handling merged | Integrate training PR; same-sample baseline evaluation CLI; approved image data, thresholds, real-scene and device/resource validation |
| Staging | Multi-architecture release workflow; held-export default and reviewed-export override implemented; branch verification confirmed under updated actions | Prepare a new bundle, then host/DNS/configuration and live verification; publication on main remains untested under the updated actions, and profile publication still needs Epic 5 approval |

A single percentage would obscure these independent gates. The monitoring code is
substantially implemented; the complete operational product is not yet evidenced.
Historical plans are context, not proof that every unchecked historical item is
current scope. No open GitHub issues were returned during the initial audit.
PR #32 was incorporated through PR #43; PR #36 remains in the integration queue.
PR #36 is currently open with conflicts against `main`; it is not approved for merge.
The 34-row mobile audit in PR #65 is a dated baseline. After GitHub withdrew
the `braces` and `sprintf-js` advisories, PR #66's live Android/iOS reports each
returned 12 undetermined rows without a lockfile change. This is an audit-feed
change, not evidence that the app or installed packages are safe.
PR #71's dated reports have nine undetermined rows after three inherited chain
rows disappeared from the audit feed. The direct `node-forge` row remains high
and undetermined. No lockfile, source-map, native-inventory, or compact-trace
change explains the row drop; it is not safety or device evidence.

## Prioritized delivery queue

- [x] P0 tracking: published this assessment and corrected stale Epic 7/current-process claims in `docs/project-status.md`; PR #39 merged after all five CI checks passed (remote main `f53117e2`).
- [x] P1 verification debt: PR #40 merged at `4004ad3f` after independent review and all five CI checks passed. Backend 148 tests, ML 65 tests, portable Ruff, web build/tests, mobile Jest/TypeScript/Android, and iOS simulator build are required in CI.
- [x] P0 web map dependency security: PR #41 merged at `59a0c75e` after the web suite (175 tests), production build, browser map smoke check, zero production audit findings, and five green CI checks. The patched MapLibre migration includes a WebGL2 fallback; its isolated worktree and branch were removed after merge verification.
- [x] P1 web development-tool security: PR #42 merged at `a31197b0` after a clean `npm ci`, 175 web tests, production build, zero full/production audit findings (down from eight), independent review and five green CI checks. Its isolated worktree and branch were removed after merge verification.
- [x] P1 existing credential fix: PR #43 merged at `5877a0c8`, incorporating PR #32's loader, correcting `docs/runbook.md`, and isolating tests from a developer's real `.env`. Local ML tests passed 72/72, focused tests 12/12, Ruff, structure and whitespace checks passed; independent review's finding was fixed and all five CI checks passed. Both merged branches and worktrees were removed. See the [focused integration plan](docs/superpowers/plans/2026-10-18-kaggle-credential-integration.md).
- [x] P1 staging held-export mode: [PR #45](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/45) merged at `a80d9adc` after all five CI checks passed. The base Compose deployment omits the held export and verifies an empty profile list; a separate, explicit reviewed-export override verifies a non-empty list. Release packaging, CI checks, deploy-script tests, and the runbook cover both modes. See the [focused plan](docs/superpowers/plans/2026-10-18-staging-held-export.md). Live deployment remains gated by a host and DNS, and profile publication remains gated by Epic 5 review.
- [x] P2 mobile cache isolation: [PR #46](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/46) merged at `8854903b` after all five CI checks passed. Offline caching and initial restoration use normalized API URL keys; the old unscoped cache is not reused. A server change clears visible events and ignores the prior server's response. See the [focused plan](docs/superpowers/plans/2026-10-18-mobile-cache-isolation.md). Device-flow evidence remains pending.
- [x] P2 mobile refresh ordering: [PR #47](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/47) merged at `40dce118` after all five CI checks passed. The controller ignores superseded same-URL success and error results and invalidates pending work on a server change; see the [focused plan](docs/superpowers/plans/2026-10-19-mobile-refresh-ordering.md).
- [x] P2 mobile cache-write ordering: [PR #48](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/48) merged at `c61945a6` after all five CI checks passed. Latest-request tokens and serialized per-server cache writes prevent stale offline restoration; see the [focused plan](docs/superpowers/plans/2026-10-19-mobile-cache-write-ordering.md).
- [x] P2 mobile persistence resilience: [PR #49](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/49) merged at `de9170d9` after all five CI checks passed. A failed offline-cache write now preserves fresh events and shows a separate warning; see the [focused plan](docs/superpowers/plans/2026-10-19-mobile-cache-resilience.md).
- [x] P1 mobile critical transitive patch: [PR #50](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/50) merged at `3557b28a` after all five CI checks passed. The lockfile resolves `shell-quote` 1.12.0; the production audit fell from 42 findings, including one critical, to 41 with zero critical. Its isolated worktree and branches were removed after verifying the tested head on remote main. See the [focused plan](docs/superpowers/plans/2026-10-19-mobile-shell-quote-patch.md). A raw audit count does not establish app exploitability.
- [x] P2 mobile compatible dependency refresh: [PR #51](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/51) merged at `f59a6881` after all five CI checks passed. Only `brace-expansion`, `compression`, and `joi` changed within existing ranges; the production audit fell from 41 to 38 findings, with zero critical. Its tested head is on remote main, and its worktree and branches were removed. See the [focused plan](docs/superpowers/plans/2026-10-19-mobile-compatible-dependency-refresh.md) and [audit record](docs/mobile-dependency-audit-2026-10-19.md).
- [x] P2 mobile unused navigation dependency: [PR #52](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/52) merged at `a3366d9c` after five green CI checks. It removed unused `@react-navigation/native` and 12 orphaned lock entries without changing app or native code; the production audit fell from 38 to 34 findings (six moderate, 28 high, zero critical). Its tested head is on remote main, and its worktree and branches were removed. See the [focused plan](docs/superpowers/plans/2026-10-19-mobile-unused-navigation-removal.md) and [audit record](docs/mobile-dependency-audit-2026-10-19.md).
- [x] P2 mobile major-migration design: [PR #53](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/53) merged at `9fd7ec19` after independent Astra review and all five CI checks passed. It recorded the React Native/Metro upgrade boundaries, artifact-evidence gaps, platform floors, and four bounded follow-up features. The tested head is on remote main; its worktree and branches were removed. See the [assessment](docs/mobile-rn-migration-assessment-2026-10-20.md) and [focused plan](docs/superpowers/plans/2026-10-20-mobile-rn-migration-assessment.md).
- [x] P2 mobile release-artifact exposure record: [PR #54](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/54) merged at `b669f9c3` after independent review and five exact-head CI checks passed. The final Android/iOS reports record 25 source-map packages, 34 audit-chain findings (six moderate, 28 high, zero critical), and only `react-native` listed among those findings; the corrected iOS list has only the app and Hermes executables. All dispositions remain undetermined. The tested head is on remote main, and its worktree and branches were removed. See the [dated evidence](docs/mobile-artifact-evidence-2026-10-20.md), [migration assessment](docs/mobile-rn-migration-assessment-2026-10-20.md), and [focused implementation plan](docs/superpowers/plans/2026-10-20-mobile-artifact-exposure.md).
- [x] P2 mobile advisory identity evidence: [PR #55](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/55) merged at `bed6c572` after independent review and five exact-head CI checks passed. Both final reports have 34 findings with installed versions, five directly affected packages, six direct advisory references, and 29 inherited-link findings; none changed disposition. The tested head is on remote main, and its worktree and branches were removed. See the [design](docs/superpowers/specs/2026-10-20-mobile-advisory-identities-design.md) and [plan](docs/superpowers/plans/2026-10-20-mobile-advisory-identities.md).
- [x] P2 mobile advisory path and precondition record: [PR #56](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/56) merged at `29fa1a2e` after independent review, five exact-head CI checks, and inspection of both final Release reports. The six direct references and five shortest production lockfile paths are recorded with affected-operation preconditions; all 34 dispositions remain undetermined. The tested head is on remote main, and its worktree and branches were removed. See the [dated review](docs/mobile-advisory-exposure-review-2026-10-20.md) and [focused plan](docs/superpowers/plans/2026-10-20-mobile-advisory-paths.md).
- [x] P2 `fast-xml-parser` consumer-call review: [PR #57](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/57) merged at `521faeed` after independent review, five exact-head CI checks, and inspection of both final Release reports. The pinned Android and Apple CLI packages have three direct `XMLParser`/`XMLValidator` use files and no direct `XMLBuilder` call; other consumers and input control remain unverified. All 34 dispositions remain undetermined. The tested head is on remote main, and its worktree and branches were removed. See the [dated review](docs/mobile-fast-xml-parser-callsites-2026-10-20.md).
- [x] P2 `image-size` consumer-call review: [PR #58](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/58) merged at `3827dd03` after independent review, five exact-head CI checks, and both final Release report inspections. Metro passes local asset paths/buffers to `image-size`; its extension gate excludes JXL/HEIF/ICNS names, but the parser dispatches by file bytes. Crafted-input provenance remains unverified and all 34 dispositions remain undetermined. The tested head is on remote main, and its worktree and branches were removed. See the [dated review](docs/mobile-image-size-callsites-2026-10-20.md).
- [x] P2 `node-forge` consumer-call review: [PR #59](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/59) merged at `61f85055` after independent review, five exact-head CI checks, and inspection of both Release reports. The [dated source review](docs/mobile-node-forge-callsites-2026-10-20.md) finds no direct `selfsigned` use in the pinned middleware's distributed JavaScript, while `selfsigned.generate` verifies its new certificate. All 34 dispositions remain undetermined; the tested head is on remote main, and the worktree and branches were removed.
- [x] P2 `braces` consumer-call review: [PR #60](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/60) merged at `b10296a2` after independent review and five exact-head CI checks. Its final Android/iOS Release reports retain the same 34 undetermined advisory entries, 25 source-map packages, native inventories, and source-map hashes as PR #59; the iOS bundle hash also matches. The [bounded review](docs/mobile-braces-callsites-2026-10-21.md) distinguishes production from development-only consumers and fixed CLI globs from local cache paths. An untrusted deep-pattern path remains unverified. Its tested head is on remote main, and its worktree and branches were removed.
- [x] P2 `sprintf-js` consumer-call review: [PR #61](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/61) merged at `ed13a9cd` after independent review, five exact-head CI checks, and both final Release-report inspections. Metro's inspected YAML loader uses the `js-yaml` library, while the pinned `argparse` formatter is imported by the separate YAML CLI. Other callers and untrusted format-string provenance remain unverified; all 34 dispositions stay undetermined. The tested head is on remote main, and its worktree and branches were removed. See the [bounded review](docs/mobile-sprintf-js-callsites-2026-10-21.md).
- [x] P2 mobile cross-advisory gate matrix: [PR #62](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/62) merged at `ec96864a` after independent review, five exact-head CI checks, and both final Release-report comparisons. The [six-advisory matrix](docs/mobile-advisory-attack-path-gates-2026-10-21.md) preserves all 34 undetermined dispositions; its tested head is on remote main, and its worktree and branches were removed.
- [x] P2 `image-size` asset provenance: [PR #63](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/63) merged at `695e9ff8` after independent review, five exact-head CI checks, and final Android/iOS Release-report comparison with PR #62. Two non-published local Metro bundles copied no images; the installed/tracked candidate signatures were PNG or SVG. The reports retained 34 undetermined findings, 25 source-map packages, and the same native inventories and source-map hashes; only the Android APK file hash differed. The tested head is on remote main, and the worktree and branch were removed after its ignored files were preserved outside the checkout. At that dated snapshot, both parser-advisory references and all 34 audit rows remained undetermined; see the [bounded review](docs/mobile-image-asset-provenance-2026-10-21.md) and [focused plan](docs/superpowers/plans/2026-10-21-mobile-image-asset-provenance.md).
- [x] P2 mobile exact-build advisory process trace: [PR #64](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/64) merged at `ecbe6173` after independent review and five exact-head checks on `2fe27ea8`. Both [process summaries](docs/mobile-build-process-trace-2026-10-21.md) observed Metro build activity and matched across platforms. Both final Release reports retained 34 undetermined findings, 25 source-map packages, identical source-map hashes and native inventories against PR #63; only the Android APK hash differed. The tested head is on main, and the worktree and branch were removed after ignored files were preserved. At that dated run, all 34 dispositions were undetermined; bounded `image-size` call and input provenance was the next slice.
- [x] P2 mobile exact-Release image-input trace: [PR #66](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/66) merged at `c398d31c` after independent review and five exact-head checks on `a80ecd85`. Both final Android/iOS traces recorded two pinned `image-size` module loads and zero parser calls; [the dated evidence](docs/mobile-image-input-trace-2026-10-24.md) limits this to those Release processes. The live audit changed from PR #65's 34 undetermined rows to 12 undetermined rows after two upstream withdrawals, with no lockfile change. Both final reports retained the source-map hashes, 25-package lists, native inventories, and five-package process summaries; only the Android APK hash differed. The tested head is on main. Ignored caches were preserved outside the checkout before the merged worktree and branches were removed.
- [x] P2 `fast-xml-parser` direct `XMLBuilder` consumer inventory: [PR #68](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/68) merged at `60322d92` after five exact-head checks on `4d711939`. The [dated review](docs/mobile-xml-builder-path-2026-10-25.md) searched 7,540 installed JavaScript files and tracked mobile source, finding only the three pinned CLI parser/validator consumers and the package export. The exact-Release traces loaded builder files but recorded no executed named builder function. Android differed from PR #67 only in its APK hash; iOS and compact traces matched. This does not establish dynamic/generated callers, input control, device behavior, or safety; all 12 then-current audit rows stayed `undetermined`.
- [x] P2 `node-forge` direct-caller and key-path inventory: [PR #69](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/69) merged at `d2fec772` after independent review and five exact-head checks on `449b0d31`. The [dated review](docs/mobile-node-forge-path-2026-10-25.md) found no external direct `selfsigned`/forge token among 7,540 installed JavaScript files or tracked mobile source. `selfsigned.generate` internally verifies its newly constructed certificate and accepts optional caller-supplied PEM keys; no project caller or supplied-key path was established. PR #68's scoped Release process summaries recorded no forge file load. PR #69's Android report differed from PR #68 only in the APK hash; iOS and all compact traces matched. All 12 then-current audit rows stayed `undetermined`. The worktree registration and merged branches were removed after preserving 24 ignored paths; its empty directory remains after automatic command review blocked final deletion.
- [x] P2 automatic PR CI action maintenance: [PR #70](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/70) merged at `fcf8c0b6` after independent review and five passing checks on `cf95281f`. The four automatic PR workflows use maintained action majors and Ubuntu 24.04 for Linux. Android differed from PR #69 only in its APK hash; iOS and all compact traces matched, retaining 12 undetermined audit rows. The tested commit is on remote main; the clean worktree and merged branches were removed after preserving 24 ignored paths. See the [focused plan](docs/superpowers/plans/2026-10-26-ci-action-runtime-pr-workflows.md).
- [x] P2 manual staging CI action maintenance: [PR #71](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/71) merged at `271310fd` after five green checks on `da7d3189`. Branch-only staging run `40482711712` passed verification and skipped publication. Both final Release reports and compact traces matched PR #70 except the exact reviewed 12-to-9 audit-feed change and Android APK hash. At that checkpoint, all nine rows remained `undetermined`; the direct `node-forge` row remained high. The tested head is on remote main; 25 ignored paths were preserved before removing the clean worktree and branches. See the [focused plan](docs/superpowers/plans/2026-10-27-staging-action-runtime.md). Publication and live-host evidence remain separate gates.
- [ ] P2 mobile remaining advisory attack-path review (deferred until a new caller/input route or framework migration): keep dynamic/generated `fast-xml-parser` builder and `node-forge` callers, certificate/key and comment/CDATA provenance, generated/external `image-size` inputs, and device attribution open. The withdrawn `braces` and `sprintf-js` references remain historical unless reinstated or new evidence warrants review. Package names and dependency paths cannot establish build-only status or exploitability. Repeat the audit and review after framework migration.
- [x] P2 mobile New Architecture **build** readiness: [PR #73](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/73) merged at `fb283e6e` after independent review and all five checks on `f98bd22f`. Android/iOS Debug and non-published Release builds passed on React Native 0.75.5 with both opt-in flags. Against PR #72, Android changed only its APK hash and 16 added app/Codegen native entries across four ABIs; iOS audited JSON and all four compact traces matched exactly. The iOS artifact hash covers the main JavaScript bundle, not its native executable. At that checkpoint, all nine audit rows were undetermined, including high direct `node-forge`; the tested head is on remote main. Twenty-five ignored paths were preserved before removing the clean merged worktree and branches. See the [focused plan](docs/superpowers/plans/2026-10-27-mobile-new-architecture-readiness.md).
[PR #74](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/74)
merged the PR #73 tracking closeout at `771d529a`. Its five exact-head checks
passed on `fe7b35af`; Release reports and compact traces matched PR #73 except
for the Android APK hash. This is documentation closeout, not device evidence.

The 2026-10-28 [main Mobile CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40618628164)
returned 11 undetermined Android and iOS audit rows, adding direct `deepmerge`
[GHSA-gcqx-w48m-w2h4](https://github.com/advisories/GHSA-gcqx-w48m-w2h4)
and its inherited `@react-native-community/cli-config` path to PR #74's nine.
The lockfile did not change; other report fields matched PR #74 except the
Android APK hash. The advisory has no patched version recorded. This changed
audit result is not app-safety or device evidence.

- [x] P2 current-app maintenance gate: verified that the Android and iOS non-published Release apps install, launch, and remain alive on CI simulators via the startup smoke gate in Mobile CI ([PR #75](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/75), merged at `20fc771a`). The gate is startup-only (no flow or advisory clearance), records screenshots/logs, and fails closed. Keep React Native 0.75.5 and current OS minimums while repairing observed defects.
- [x] P2 PHIVOLCS earthquake feed text correction: the 2026-10-28 Android check found `Â°` in both API and phone. Commit `67963987` decodes the source response as strict UTF-8 before parsing. A regression failed before and passed after; full backend tests passed 151/151 and Ruff passed. A local one-off poll updated 1,676 unique events, and the existing API returned a recent place name with `°`. The 27 older malformed rows were absent from the current feed and were not backfilled. Exact-head CI and corrected Android display remain pending; see [runtime evidence](docs/mobile-runtime-smoke-test.md#2026-10-29-phivolcs-text-correction-check).
- [ ] P2 PHIVOLCS historical text backfill: decide whether older source rows with `Â°` need a separately reviewed repair. Do not infer the correct text from a character replacement without comparing source data; the current feed does not contain those 27 IDs.
- [ ] P2 mobile New Architecture device-flow acceptance: verify saved-location persistence, offline cache, camera permission/capture, and SVG overlay rendering on actual Android/iOS devices with the exact app commit. CI simulator builds do not establish these flows.
- [ ] P2 mobile supported framework migration (after current-app runtime and staging evidence): decide the Android SDK 24/iOS 15.1 support floor, then migrate React Native/React/Metro/native templates and tools coherently to a supported release; verify complete CI and release artifacts.
- [ ] P2 mobile post-migration disposition: repeat advisory/artifact analysis and record Android/iOS device-flow evidence before release acceptance.
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
- Bugs: no known unresolved mobile cache correctness bug in the audited flows;
  runtime/device behavior still needs evidence.
- Weak tests: no physical
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
