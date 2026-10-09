# Mobile Android CI SDK Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the Android SDK setup in PR #17 and verify both the mobile tests and Android debug build in CI.

**Architecture:** Keep the workflow's existing Node/Jest and Android build sequence. Add standard-library regression tests for the Android setup action's package input and the Gradle wrapper's tracked executable mode, then explicitly install the pinned SDK packages and build the debug app.

**Tech Stack:** GitHub Actions YAML, Python `unittest`, React Native, Jest, Gradle, Android SDK.

**Spec:** `docs/superpowers/specs/2026-10-09-mobile-android-ci-setup-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, and `docs/testing-standards.md`.
- Keep the repair on the focused `fix/mobile-android-ci` branch until its verification is complete.
- Do not change app dependencies or generated native project contents; change only the Gradle wrapper's tracked executable bit required by Linux CI.
- Keep SDK versions at Android 34, Build Tools 34.0.0, Platform Tools, NDK 26.1.10909125, and JDK 17.
- Conventional Commits; run the mobile tests, workflow regression test, `python scripts\verify_structure.py`, and `git diff --check`.
- Before updating PR #17, confirm its remote head remains `ff9ab974ce91b89080d00d322532f25bfd712c6f`; update it only with a fast-forward push.

---

### Task 1: Add a workflow regression test

**Files:**
- Create: `scripts/tests/test_mobile_ci_workflow.py`

**Interfaces:**
- Consumes: `.github/workflows/mobile-ci.yml`.
- Produces: standard-library tests that require an empty `packages` input, confirm the explicit SDK install and Android build remain present, and check that Git tracks the wrapper as executable.

- [x] **Step 1: Write the failing test**

Create `scripts/tests/test_mobile_ci_workflow.py` with:

```python
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "mobile-ci.yml"


class MobileCiWorkflowTests(unittest.TestCase):
    def test_android_setup_skips_obsolete_default_tools_package(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        setup_start = workflow.index("uses: android-actions/setup-android@v3")
        install_start = workflow.index("- name: Install Android SDK packages", setup_start)
        setup_step = workflow[setup_start:install_start]

        self.assertIn('packages: ""', setup_step)

    def test_explicit_android_sdk_install_and_build_are_preserved(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('sdkmanager "platforms;android-34"', workflow)
        self.assertIn('"build-tools;34.0.0"', workflow)
        self.assertIn('"platform-tools"', workflow)
        self.assertIn('"ndk;26.1.10909125"', workflow)
        self.assertIn("./gradlew assembleDebug", workflow)

    def test_android_gradle_wrapper_is_tracked_as_executable(self):
        result = subprocess.run(
            ["git", "ls-files", "--stage", "--", "mobile/android/gradlew"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )

        self.assertEqual(result.stdout.split(maxsplit=1)[0], "100755", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the test and verify the expected failure**

Run from the repository root:

```powershell
python -m unittest discover -s scripts/tests -p test_mobile_ci_workflow.py
```

Expected: `test_android_setup_skips_obsolete_default_tools_package` fails because the current workflow does not pass an explicit `packages` input. The package-list/build-preservation test passes.

- [x] **Step 3: Keep the test in the working tree for the fix**

Do not commit an intermediate failing test. The repository commit checklist requires package tests to pass, so commit the test together with the passing workflow fix in Task 2.

### Task 2: Fix SDK setup and make the Gradle wrapper executable

**Files:**
- Modify: `.github/workflows/mobile-ci.yml`
- Modify file mode: `mobile/android/gradlew`

**Interfaces:**
- Consumes: the regression test from Task 1.
- Produces: the Android setup action receives `packages: ""`, and Git tracks the Gradle wrapper with executable mode `100755`.

- [x] **Step 1: Configure the action to skip additional default packages**

Change the setup step to:

```yaml
      - uses: android-actions/setup-android@v3
        with:
          packages: ""
```

Keep the existing `Install Android SDK packages` step and its explicit package list unchanged.

- [x] **Step 2: Track the Gradle wrapper as executable**

```powershell
git update-index --chmod=+x mobile/android/gradlew
git ls-files --stage -- mobile/android/gradlew
```

Expected: the index reports mode `100755` for `mobile/android/gradlew`.

- [x] **Step 3: Run the regression test and confirm it passes**

```powershell
python -m unittest discover -s scripts/tests -p test_mobile_ci_workflow.py
```

Expected: all three workflow tests pass, including the wrapper mode test.

- [ ] **Step 4: Commit the test and CI fixes together**

```powershell
git add scripts/tests/test_mobile_ci_workflow.py .github/workflows/mobile-ci.yml docs/superpowers/specs/2026-10-09-mobile-android-ci-setup-design.md docs/superpowers/plans/2026-10-09-mobile-android-ci-setup.md
git commit -m "fix: make android ci build the native app"
```

### Task 3: Verify the mobile package and repository structure

**Files:**
- Verify: `mobile/`, `scripts/tests/`, `.github/workflows/mobile-ci.yml`.

- [x] **Step 1: Install the lockfile dependencies and run mobile tests**

```powershell
Set-Location mobile
npm ci
npm test -- --runInBand
Set-Location ..
```

Expected: the mobile Jest suite passes without modifying `mobile/package-lock.json`.

- [x] **Step 2: Run the workflow regression test and structure verifier**

```powershell
python -m unittest discover -s scripts/tests -p test_mobile_ci_workflow.py
python scripts\verify_structure.py
git diff --check
```

Expected: both workflow tests pass, all expected scaffold paths exist, and `git diff --check` reports no whitespace errors.

### Task 4: Update PR #17 and verify hosted Android build

**Files:**
- Publish: commits on `fix/mobile-android-ci` to remote `feat/mobile-native-runtime` only after confirming the remote PR head is still the pinned parent SHA.

- [ ] **Step 1: Confirm branch ancestry and current remote PR head**

Run:

```powershell
gh pr view 17 --repo matthewubacbrian-afk/geohazard-ph --json headRefName,headRefOid
git merge-base --is-ancestor c3fe846b26cfd67c2355b82879a8c815e0e4ebc7 HEAD
```

Expected: the PR head branch is `feat/mobile-native-runtime`, its OID is `c3fe846b26cfd67c2355b82879a8c815e0e4ebc7`, and the ancestor check exits 0. If the remote head moved, do not force-push or overwrite it; rebase the fix branch onto the updated head and repeat local verification.

- [ ] **Step 2: Fast-forward the existing PR branch**

```powershell
git push origin HEAD:refs/heads/feat/mobile-native-runtime
```

Expected: the push is accepted as a fast-forward; no force option is used.

- [ ] **Step 3: Wait for PR CI and inspect the Android job**

Open `https://github.com/matthewubacbrian-afk/geohazard-ph/pull/17/checks` and wait for the new run to complete. Confirm Mobile CI passes its SDK setup, explicit SDK install, and `./gradlew assembleDebug` steps, and confirm all other required PR checks pass.

Expected: the PR is merge-ready with all checks green. Do not merge it in this task.

## Notes for the executor

- The Windows development environment may not have the Android SDK. GitHub's Ubuntu runner is the authoritative verification for `assembleDebug`.
- The workflow change is isolated from native application behavior. If the hosted build fails after SDK setup, capture the full failing Gradle task and follow TDD with a focused native-build regression before changing app or Gradle code.
