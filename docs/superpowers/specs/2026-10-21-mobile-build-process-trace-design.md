# Mobile Release Build Process Trace — Design

**Date:** 2026-10-21

## Problem

The mobile Release reports list 34 dependency-chain advisories and source-map
packages, but neither report observes which affected Node modules or functions
execute while Gradle and Xcode package the app. The source reviews in
`docs/mobile-advisory-attack-path-gates-2026-10-21.md` therefore cannot
distinguish a loaded parser from an invoked affected operation in those builds.

## Goals

- Observe Node function coverage during each existing non-published Android and
  iOS Release build, scoped to that build command.
- Publish a small JSON summary of loaded files and executed named functions for
  the five directly affected packages: `braces`, `fast-xml-parser`,
  `image-size`, `node-forge`, and `sprintf-js`.
- Validate missing and malformed coverage rather than emitting an empty success
  report, and document what the observation can and cannot establish.
- Preserve the existing Release-artifact report schema and all 34
  `undetermined` dispositions.

## Non-goals

- Capture input values, exploit payloads, native/DEX execution, or device calls.
- Instrument arbitrary third-party JavaScript by wrapping exports or changing
  application source. A named function absent from V8 coverage is not a
  security clearance.
- Change dependencies, release packaging, or the held Epic 5 profile export.

## Context And Constraints

`.github/workflows/mobile-ci.yml` builds Android and iOS Release artifacts and
uploads separate artifact-inventory JSON files. Node 22 runs Metro from the
native build tools. `NODE_V8_COVERAGE` directs Node to write per-process V8
coverage JSON at process exit. A local Node 24 probe of pinned `image-size`
1.2.1 observed module-load entries on import and named `imageSize`/PNG
functions only after a PNG call. CI still has to establish that each native
Release step propagates the variable to its Node children.

## Alternatives Considered

- A `NODE_OPTIONS=--require` hook could log exact module loads and wrap APIs,
  but mutates the process under measurement and risks changing packaging.
- Source-only call-graph inspection is reproducible but cannot show execution
  in the exact CI Release commands.
- A second standalone Metro bundle is simpler but differs from the Gradle and
  Xcode Release invocation and repeats the limit of the local asset review.

## Design

The Android `assembleRelease` and iOS Release `xcodebuild` steps set
`NODE_V8_COVERAGE` to distinct directories under `$RUNNER_TEMP` for that
command only. After each Release build, a Python summarizer reads all
`coverage-*.json` files, limits file URLs to the installed
`mobile/node_modules` tree, and selects the five direct advisory packages at
any nesting depth. For each selected package it emits sorted relative paths
whose module wrapper executed and sorted named functions with nonzero V8
function-entry counts. The report also records platform and number of coverage
files. No raw coverage file is uploaded.

`build_report(platform: str, coverage_dir: Path, node_modules_root: Path) ->
dict` raises `ValueError` for no coverage files, malformed JSON/shape, or no
covered files under the requested installed tree. It does not require every
target package to appear: their absence is an observation. The CLI accepts
`--platform`, `--coverage-dir`, `--node-modules-root`, and `--output`.
Function names can be anonymous or optimized; the summary includes only
nonempty names and makes no argument/control claim. Paths are relative to
`mobile/node_modules` so the uploaded summary omits runner paths.

The two new summary artifacts are separate from the existing Android/iOS
Release reports. The dated review will compare them with source observations
and identify remaining entry-point, input-provenance, process-effect, and
device gates. All advisory dispositions remain `undetermined`.

## Rollout

Add the summarizer with test-first fixtures, then wire it into the two existing
Release steps and upload the summaries. Inspect final exact-head CI summaries
and compare both unchanged-format Release reports with the PR #63 baseline
before merging.

## Files

- `scripts/mobile_process_coverage.py`: validate and summarize V8 coverage.
- `scripts/tests/test_mobile_process_coverage.py`: synthetic coverage tests.
- `.github/workflows/mobile-ci.yml`: scoped coverage and summary uploads.
- `scripts/tests/test_mobile_ci_workflow.py`: workflow contract tests.
- `docs/mobile-build-process-trace-2026-10-21.md`: dated observed evidence.
- `PLAN.md`, `docs/project-status.md`, and a focused plan: tracking.

## Testing Strategy

Synthetic coverage tests separate module wrapper execution from named API
execution; exercise zero-count functions, nested packages, paths outside the
installed tree, no coverage files, and malformed files. Workflow tests assert
both Release commands set scoped coverage directories, summarize after
packaging, and upload distinct artifacts. Local script, mobile, web, backend,
and ML checks follow `CODING_STANDARDS.md`; exact-head CI must pass all five
jobs. Compare final Android/iOS Release JSON against PR #63: 34 advisories,
25 source-map packages, source-map hashes, and native inventories unchanged;
only the Android APK file hash may differ.

## Acceptance Criteria

- [ ] Synthetic parser and workflow tests pass after observed pre-change failures.
- [ ] Both exact-head CI jobs upload valid coverage summaries, with no missing
      or malformed coverage silently accepted.
- [ ] All five exact-head checks pass and both Release-report comparisons pass.
- [ ] The dated review states actual loaded/called observations without
      changing any of the 34 dispositions.

## Out Of Scope (backlog)

Trace input provenance, indirect native/device paths, and function arguments
in later attack-path and device evidence slices. Repeat this evidence after the
supported React Native migration.
