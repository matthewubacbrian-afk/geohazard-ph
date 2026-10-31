import hashlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock

from scripts import mobile_qa_artifact as qa


class QaArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.apk = self.root / "qa.apk"
        self.release = self.root / "release.apk"
        self.release.write_bytes(b"release")
        self.lock = self.root / "package-lock.json"
        self.lock.write_bytes(b"lock")
        self.commit = "a" * 40
        self.qa_manifest = {
            "package": qa.QA_PACKAGE,
            "label": "GeoHazard QA",
            "debuggable": False,
            "cleartext": True,
            "target_sdk": 34,
        }
        self.release_manifest = {
            **self.qa_manifest,
            "package": qa.RELEASE_PACKAGE,
            "cleartext": False,
        }
        self.inspect = lambda apk, _: self.qa_manifest if apk == self.apk else self.release_manifest
        self.make_apk()

    def make_apk(self, *, bundle=True, abis=None):
        with zipfile.ZipFile(self.apk, "w") as archive:
            if bundle:
                archive.writestr("assets/index.android.bundle", b"js")
            for abi in qa.REQUIRED_ABIS if abis is None else abis:
                archive.writestr(f"lib/{abi}/libhermes.so", b"native")

    def record(self):
        return qa.build_record(
            self.apk, self.release, self.lock, self.commit, "aapt", inspect=self.inspect
        )

    def test_record_identifies_exact_artifact_and_source(self):
        record = self.record()
        self.assertEqual(record["commit"], self.commit)
        self.assertEqual(record["application_id"], qa.QA_PACKAGE)
        self.assertEqual(record["apk_sha256"], hashlib.sha256(self.apk.read_bytes()).hexdigest())
        self.assertEqual(record["lockfile_sha256"], hashlib.sha256(b"lock").hexdigest())
        self.assertEqual(set(record["native_abis"]), qa.REQUIRED_ABIS)

    def test_missing_bundle_fails(self):
        self.make_apk(bundle=False)
        with self.assertRaisesRegex(ValueError, "bundle"):
            self.record()

    def test_empty_bundle_fails(self):
        self.make_apk(bundle=False)
        with zipfile.ZipFile(self.apk, "a") as archive:
            archive.writestr("assets/index.android.bundle", b"")
        with self.assertRaisesRegex(ValueError, "bundle"):
            self.record()

    def test_missing_phone_abi_fails(self):
        self.make_apk(abis={"arm64-v8a", "x86", "x86_64"})
        with self.assertRaisesRegex(ValueError, "ABI"):
            self.record()

    def test_wrong_identity_or_debuggable_qa_fails(self):
        for change in (
            {"package": qa.RELEASE_PACKAGE},
            {"debuggable": True},
            {"cleartext": False},
            {"label": "GeoHazard PH"},
        ):
            with self.subTest(change=change):
                original = self.qa_manifest.copy()
                self.qa_manifest.update(change)
                with self.assertRaisesRegex(ValueError, "QA manifest"):
                    self.record()
                self.qa_manifest = original

    def test_cleartext_or_debuggable_release_fails(self):
        for change in (
            {"cleartext": True},
            {"cleartext": None},
            {"debuggable": True},
            {"target_sdk": 27},
        ):
            with self.subTest(change=change):
                original = self.release_manifest.copy()
                self.release_manifest.update(change)
                with self.assertRaisesRegex(ValueError, "Release manifest"):
                    self.record()
                self.release_manifest = original

    def test_invalid_commit_fails(self):
        self.commit = "main"
        with self.assertRaisesRegex(ValueError, "commit"):
            self.record()

    def test_aapt_manifest_parser_checks_final_binary_attributes(self):
        run = Mock(
            side_effect=[
                subprocess.CompletedProcess(
                    [],
                    0,
                    "package: name='com.geohazardph.mobile.qa'\ntargetSdkVersion:'34'\napplication-label:'GeoHazard QA'",
                    "",
                ),
                subprocess.CompletedProcess(
                    [], 0, "A: android:usesCleartextTraffic(0x010104ec)=(type 0x12)0xffffffff", ""
                ),
            ]
        )
        self.assertEqual(qa.inspect_manifest(self.apk, "aapt", run=run), self.qa_manifest)

    def test_unknown_cleartext_attribute_fails_closed(self):
        run = Mock(
            side_effect=[
                subprocess.CompletedProcess(
                    [],
                    0,
                    "package: name='qa'\ntargetSdkVersion:'34'\napplication-label:'GeoHazard QA'",
                    "",
                ),
                subprocess.CompletedProcess([], 0, "A: android:usesCleartextTraffic=@0x1234", ""),
            ]
        )
        with self.assertRaisesRegex(ValueError, "cleartext"):
            qa.inspect_manifest(self.apk, "aapt", run=run)

    def test_network_security_resource_requires_explicit_review(self):
        run = Mock(
            side_effect=[
                subprocess.CompletedProcess(
                    [],
                    0,
                    "package: name='com.geohazardph.mobile'\ntargetSdkVersion:'34'\napplication-label:'GeoHazard PH'",
                    "",
                ),
                subprocess.CompletedProcess(
                    [], 0, "A: android:networkSecurityConfig(0x01010527)=@0x7f120001", ""
                ),
            ]
        )
        with self.assertRaisesRegex(ValueError, "network security"):
            qa.inspect_manifest(self.release, "aapt", run=run)

    def test_absent_cleartext_flag_is_not_an_explicit_policy(self):
        run = Mock(
            side_effect=[
                subprocess.CompletedProcess(
                    [],
                    0,
                    "package: name='com.geohazardph.mobile'\ntargetSdkVersion:'34'\napplication-label:'GeoHazard PH'",
                    "",
                ),
                subprocess.CompletedProcess([], 0, "E: application", ""),
            ]
        )
        self.assertIsNone(qa.inspect_manifest(self.release, "aapt", run=run)["cleartext"])


if __name__ == "__main__":
    unittest.main()
