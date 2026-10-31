# Mobile scene retake - Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline for this bounded
> delegated fix. Steps use checkbox syntax for tracking. Parent handles independent
> spec and quality reviews; do not create another implementation agent.

**Goal:** Offer one guarded Retake action whenever a captured scene exists.

**Architecture:** Test rendered SceneAnalysisScreen with camera/API boundaries
mocked, then move existing replacement behavior into one shared image-present action.

**Tech Stack:** React Native, TypeScript, Jest, react-test-renderer 18.3.1.

**Spec:** docs/superpowers/specs/2026-10-31-mobile-scene-retake-design.md

## Global Constraints

- Follow AGENTS.md, CODING_STANDARDS.md and applicable docs.
- Conventional Commits; documentation commits use docs type.
- No API/service/model changes, device control, shared dependency mutation, secrets,
  generated artifacts, or paid infrastructure.
- Run mobile npm test -- --runInBand and npx tsc --noEmit, repository structure
  verification and git diff --check. No running services or credentials required.

### Task 1: Capture rendered replacement regression

**Files:**
- Modify: mobile/package.json, mobile/package-lock.json, docs/testing-standards.md
- Create: mobile/tests/sceneAnalysisScreen.test.ts

**Interfaces:**
- Consumes: SceneAnalysisScreen({apiBaseUrl, isActive}), captureSceneImage and analyzeScene.
- Produces: deterministic visible-control tests using React.createElement and act.

- [x] **Step 1:** Install exact development dependencies with
  `npm install --save-dev --save-exact react-test-renderer@18.3.1 @types/react-test-renderer@18.3.1`.
  Allow focused renderer interaction tests in mobile standards while retaining
  service tests as the default.
- [x] **Step 2:** Render the screen, press Open camera, resolve captured image A,
  and assert one enabled Retake photo. Use deferred camera promises to assert
  removal before completion and Open camera after cancellation. Mock API rejection
  for typed 503/network errors; assert Retake survives and clears messages. Assert
  pending analysis disables Retake. Exercise quality-warning continuation and result.
- [x] **Step 3:** Run `npm test -- --runInBand tests/sceneAnalysisScreen.test.ts` on
  original source; expect missing Retake assertions to fail, not setup errors.

### Task 2: Share the guarded Retake action

**Files:**
- Modify: mobile/src/screens/SceneAnalysisScreen.tsx
- Test: mobile/tests/sceneAnalysisScreen.test.ts

**Interfaces:**
- Consumes: existing capture(true), qualityWarning, isCapturing, isAnalyzing.
- Produces: exactly one image-present replacement control; no service signature changes.

- [x] **Step 1:** Remove result and warning Retake blocks, then render after the
  result conditional inside the captured image branch:

```tsx
<Pressable accessibilityRole="button" disabled={isCapturing || isAnalyzing}
  onPress={() => void capture(true)} style={styles.secondaryButton}>
  <Text style={styles.secondaryText}>
    {qualityWarning ? 'Retake blurry photo' : 'Retake photo'}
  </Text>
</Pressable>
```

- [x] **Step 2:** Run targeted tests and confirm all interaction cases pass.
- [x] **Step 3:** Run full mobile tests, TypeScript, structure and whitespace checks.
- [x] **Step 4:** Record red/green evidence below; commit code/tests/dependencies with
  `fix: keep scene retake available for every captured preview`, and documentation
  separately with `docs: document scene retake regression coverage`.

## Notes for the executor

Tasks are sequential. Use isolated local dependencies; existing device dependencies
may be read/copied but never modified. A draft PR may run CI while QA pipeline
PR #81 is pending; merge this fix only after that dependency has merged.
Reviewers should check one Retake per image state and disabled analysis behavior.

## Execution evidence

- Baseline: original screen, excluding the new regression file, passed 10 suites / 61 tests.
- Red: `node node_modules/jest/bin/jest.js --runInBand tests/sceneAnalysisScreen.test.ts`
  on unchanged original JSX failed 9 cases / passed 1. Failures were missing Retake
  controls (expected one, received zero), not import/setup errors; existing result
  replacement passed.
- Green: the same targeted command passed all 10 cases after the shared-control fix.
- Full package verification: `npm test -- --runInBand` passed 11 suites / 71 tests,
  zero snapshots; `npx tsc --noEmit` exited 0.
- Repository verification: Python 3.11 `scripts/verify_structure.py` passed all 140
  expected paths; `git diff --check` exited 0.
- Local tooling used Node 22.22.0 explicitly. Dependencies were copied into this
  worktree and renderer packages installed there; shared device dependencies were
  never modified. npm generated the pinned renderer/types lockfile graph.
- Implementation commit: `aaad630b`; design/testing allowance commit: `ab2ce9a4`.
- Independent spec and code-quality reviews found no blockers; reviewers reran
  the full package or targeted interaction checks successfully.
- Integrated QA pipeline head `3c3c0f73` to build a fresh standalone APK containing
  this repair. The draft PR depends on #81; physical acceptance of the new APK
  remains pending and must not be inferred from the older capture record.
