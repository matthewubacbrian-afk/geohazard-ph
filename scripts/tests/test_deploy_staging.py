"""Exercise staging mode selection without Docker, images, or a live host."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/deploy_staging.sh"
RELEASE_SHA = "a" * 40


class DeployStagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "scripts").mkdir()
        shutil.copyfile(SCRIPT, self.root / "scripts/deploy_staging.sh")
        (self.root / ".env.staging").write_text("IMAGE_TAG=example\n", encoding="utf-8")
        (self.root / "stubs.sh").write_text(
            "docker() { printf '%s\\n' \"$*\" >> docker_calls.txt; }\n"
            "curl() {\n"
            "  case \"$*\" in\n"
            "    */api/v1/risk-profile/clusters*) printf '%s' \"$PROFILE_RESPONSE\" ;;\n"
            "    *) printf '{}' ;;\n"
            "  esac\n"
            "}\n",
            encoding="utf-8",
        )

    def run_deploy(self, response: str, *extra: str) -> subprocess.CompletedProcess[str]:
        bash = shutil.which("bash")
        if os.name == "nt":
            bash = r"C:\Program Files\Git\bin\bash.exe"
        assert bash is not None
        environment = os.environ.copy()
        environment.update(BASH_ENV="./stubs.sh", PROFILE_RESPONSE=response)
        return subprocess.run(
            [bash, "scripts/deploy_staging.sh", RELEASE_SHA, "https://staging.example.com", *extra],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_held_mode_requires_empty_profile_list_and_no_override(self) -> None:
        result = self.run_deploy("[]")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / "docker_calls.txt").read_text(encoding="utf-8")
        self.assertNotIn("compose.staging.profile.yml", calls)

    def test_reviewed_mode_requires_nonempty_profile_list_and_override(self) -> None:
        result = self.run_deploy('[{"region_name":"NCR"}]', "--with-profile")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / "docker_calls.txt").read_text(encoding="utf-8")
        self.assertIn("compose.staging.profile.yml", calls)

    def test_held_mode_rejects_unexpected_profile_data(self) -> None:
        result = self.run_deploy('[{"region_name":"NCR"}]')
        self.assertNotEqual(result.returncode, 0)

    def test_reviewed_mode_rejects_empty_or_invalid_profile_data(self) -> None:
        for response in ("[]", "{}", "not-json"):
            with self.subTest(response=response):
                result = self.run_deploy(response, "--with-profile")
                self.assertNotEqual(result.returncode, 0)

    def test_unknown_flag_is_rejected_before_docker(self) -> None:
        result = self.run_deploy("[]", "--unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "docker_calls.txt").exists())


if __name__ == "__main__":
    unittest.main()
