from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
