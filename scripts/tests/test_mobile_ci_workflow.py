import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "mobile-ci.yml"


class MobileCiWorkflowTests(unittest.TestCase):
    def test_release_artifact_reports_are_generated_without_uploading_binaries(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        android_job, ios_job = workflow.split("  ios-simulator:", maxsplit=1)

        self.assertIn("./gradlew assembleRelease", android_job)
        self.assertIn("index.android.bundle.map", android_job)
        self.assertIn("app-release.apk", android_job)
        self.assertIn("--platform android", android_job)
        self.assertIn("--platform ios", ios_job)
        self.assertIn("-configuration Release", ios_job)
        self.assertIn("SOURCEMAP_FILE", ios_job)
        self.assertIn("GeoHazardPH.app", ios_job)
        self.assertEqual(workflow.count("actions/upload-artifact@v7"), 6)
        upload_paths = [
            [
                line.strip().removeprefix("path: ")
                for line in block.splitlines()
                if line.startswith("          path: ")
            ]
            for block in workflow.split("uses: actions/upload-artifact@v7")[1:]
        ]
        self.assertEqual(
            upload_paths,
            [
                ["${{ runner.temp }}/mobile-process-trace-android.json"],
                ["${{ runner.temp }}/mobile-image-input-trace-android.json"],
                ["${{ runner.temp }}/mobile-artifact-report-android.json"],
                ["${{ runner.temp }}/mobile-process-trace-ios.json"],
                ["${{ runner.temp }}/mobile-image-input-trace-ios.json"],
                ["${{ runner.temp }}/mobile-artifact-report-ios.json"],
            ],
        )
        self.assertIn("if-no-files-found: error", workflow)
        self.assertEqual(workflow.count("--lockfile package-lock.json"), 2)

    def test_inventory_script_is_exercised_in_python_ci(self):
        backend_workflow = (ROOT / ".github" / "workflows" / "backend-ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("pytest -q scripts/tests/test_mobile_artifact_inventory.py", backend_workflow)
        self.assertIn("ruff check", backend_workflow)
        self.assertIn("scripts/mobile_artifact_inventory.py", backend_workflow)

    def test_release_builds_capture_scoped_node_coverage(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        android_job, ios_job = workflow.split("  ios-simulator:", maxsplit=1)

        self.assertIn(
            'NODE_V8_COVERAGE="$RUNNER_TEMP/mobile-node-coverage-android" \\',
            android_job,
        )
        self.assertIn(
            'NODE_V8_COVERAGE="$RUNNER_TEMP/mobile-node-coverage-ios" \\',
            ios_job,
        )
        self.assertIn("scripts/mobile_process_coverage.py", workflow)
        self.assertIn("mobile-process-trace-android.json", android_job)
        self.assertIn("mobile-process-trace-ios.json", ios_job)
        backend_workflow = (ROOT / ".github" / "workflows" / "backend-ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/tests/test_mobile_process_coverage.py", backend_workflow)

    def test_release_builds_capture_scoped_image_inputs(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        android_job, ios_job = workflow.split("  ios-simulator:", maxsplit=1)
        for job, platform in ((android_job, "android"), (ios_job, "ios")):
            self.assertIn("GEOHAZARD_IMAGE_INPUT_TRACE_DIR", job)
            self.assertIn("NODE_OPTIONS=", job)
            self.assertIn("mobile_image_input_observer.cjs", job)
            self.assertIn("mobile_image_input_summary.py", job)
            self.assertIn(f"mobile-image-input-trace-{platform}.json", job)
        backend_workflow = (ROOT / ".github" / "workflows" / "backend-ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/tests/test_mobile_image_input_summary.py", backend_workflow)
        self.assertIn("scripts/mobile_image_input_summary.py", backend_workflow)
        self.assertIn("scripts/tests/test_mobile_image_input_observer.cjs", android_job)

    def test_android_setup_skips_obsolete_default_tools_package(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        setup_start = workflow.index("uses: android-actions/setup-android@v4")
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

    def test_ios_simulator_build_uses_pods_without_signing(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("  ios-simulator:", workflow)
        ios_job = workflow[workflow.index("  ios-simulator:") :]

        self.assertIn("runs-on: macos-15", ios_job)
        self.assertIn("cache-dependency-path: mobile/package-lock.json", ios_job)
        self.assertIn("run: npm ci", ios_job)
        self.assertIn("run: pod install", ios_job)
        self.assertIn("ios/GeoHazardPH.xcworkspace", ios_job)
        self.assertIn("-scheme GeoHazardPH", ios_job)
        self.assertIn("generic/platform=iOS Simulator", ios_job)
        self.assertIn("CODE_SIGNING_ALLOWED=NO", ios_job)


if __name__ == "__main__":
    unittest.main()
