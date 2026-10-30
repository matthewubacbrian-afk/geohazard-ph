# Mobile scene retake - Design

**Date:** 2026-10-31

## Problem

The standalone Android QA app leaves a captured scene with Analyze but no Retake
until analysis returns a result or quality warning. An unavailable or unconfigured
API therefore leaves no direct way to replace the photo in SceneAnalysisScreen.

## Goals

- Every captured preview offers exactly one replacement action before analysis,
  after errors, after a quality warning, and after a result.
- Replacement clears the previous image and analysis state before camera completion;
  cancellation returns to the empty Open camera state.
- Retake remains disabled during capture or analysis to prevent stale analysis races.
- Rendered screen interaction tests reproduce the defect and protect the transitions.

## Non-goals

No API, camera-service, model, storage, Android-build, or safety-language changes.

## Context And Constraints

SceneAnalysisScreen already has capture(true), which clears image, base64, result,
selected rank, quality warning, and error before awaiting the camera. Retake is
currently duplicated inside quality-warning and result branches. Follow
CODING_STANDARDS.md, docs/testing-standards.md, and docs/error-handling-and-logging.md.
The user authorized fixing observed defects on a separate managed worktree/branch
and delegated routine decisions; this bounded design implements that authorization.

## Alternatives Considered

- Add a third Retake to the normal preview branch: small but keeps duplicated
  controls and inconsistent disabled behavior; rejected in favor of one action.
- Clear the photo automatically on analysis failure: removes the user's ability
  to retry the same image and changes error recovery; rejected.

## Design

Render one shared Pressable after the result/no-result conditional, inside the
image-present branch. It calls capture(true), uses disabled={isCapturing ||
isAnalyzing}, and says Retake blurry photo during qualityWarning, otherwise Retake
photo. Remove both old Retake controls. Continue anyway, Analyze, and Open camera
retain their existing handlers and behavior.

Use react-test-renderer 18.3.1, matching React 18.3.1, as a pinned development-only
dependency with matching renderer types. Tests use React.createElement and act,
mock camera/API service boundaries and SVG, and inspect actual rendered controls,
images, and messages. No snapshots or source-text assertions.

Interfaces and configuration are unchanged. Existing typed errors remain visible
until retake or retry clears them. Image/base64 remain transient; no new persistence,
logging, schema, coordinate, or datetime handling is introduced.

## Rollout

Commit on fix/mobile-scene-retake in managed mobile-scene-retake worktree. Hold PR
creation and merge until the parent completes readiness and QA pipeline integration.
Parent performs separate spec/quality reviews and physical standalone APK acceptance.

## Files

- mobile/src/screens/SceneAnalysisScreen.tsx: shared Retake action.
- mobile/tests/sceneAnalysisScreen.test.ts: rendered interaction regressions.
- mobile/package.json and mobile/package-lock.json: pinned renderer development dependency.
- docs/testing-standards.md: narrow mobile screen-interaction testing allowance.
- docs/superpowers/specs/2026-10-31-mobile-scene-retake-design.md: bounded design.
- docs/superpowers/plans/2026-10-31-mobile-scene-retake.md: execution and evidence.

## Testing Strategy

Prove immediate Retake fails before the source fix. Exercise pending replacement,
camera cancellation, typed 503/network errors and clearing, pending-analysis disabled
state, quality-warning Continue anyway, and result replacement. Run the entire
mobile suite, strict TypeScript check, structure verifier, and git diff --check.

## Acceptance Criteria

- [ ] Normal captured preview immediately exposes one enabled Retake.
- [ ] Pending retake removes old preview and messages; cancellation shows Open camera.
- [ ] Analysis errors preserve Retake and retake clears the error.
- [ ] Analysis disables Retake; warning continuation and post-result retake work.
- [ ] Regression fails on original JSX and passes with the shared control.
- [ ] Mobile tests, strict TypeScript, structure and whitespace checks pass.

## Out Of Scope (backlog)

Physical APK acceptance belongs to the parent QA stream. No additional defect or
feature is bundled with this change.

## Spec self-review

Checked scope, state transitions, interfaces, and goal-to-acceptance mapping. No
unfinished sections or new domain terminology.

## Related documents

- Implementation plan: docs/superpowers/plans/2026-10-31-mobile-scene-retake.md.
- Template: docs/superpowers/templates/plan-template.md.
- Terminology: docs/glossary.md.
