import unittest

from scripts.verify_structure import EXPECTED_PATHS


class VerifyStructureExpectationsTests(unittest.TestCase):
    def test_native_mobile_project_files_replace_empty_platform_markers(self):
        expected_paths = set(EXPECTED_PATHS)

        self.assertIn("mobile/index.js", expected_paths)
        self.assertIn("mobile/android/gradlew", expected_paths)
        self.assertIn("mobile/ios/GeoHazardPH.xcodeproj/project.pbxproj", expected_paths)
        self.assertNotIn("mobile/android/.gitkeep", expected_paths)
        self.assertNotIn("mobile/ios/.gitkeep", expected_paths)
