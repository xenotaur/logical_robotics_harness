import pathlib
import tempfile
import unittest

from lrh.dev import release_smoke


class ReleaseSmokeHelpersTest(unittest.TestCase):
    def test_normalize_version_accepts_tag_or_plain_version(self) -> None:
        self.assertEqual(release_smoke.normalize_version("v0.2.0"), "0.2.0")
        self.assertEqual(release_smoke.normalize_version("0.2.0"), "0.2.0")
        self.assertEqual(release_smoke.normalize_version(""), "")

    def test_normalize_version_rejects_invalid_value(self) -> None:
        with self.assertRaises(release_smoke.ReleaseSmokeError):
            release_smoke.normalize_version("release-0.2.0")

    def test_resolve_wheel_path_requires_single_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = pathlib.Path(temp_dir)
            dist_dir = repo_root / "dist"
            dist_dir.mkdir()
            (dist_dir / "logical_robotics_harness-0.2.0-py3-none-any.whl").write_text(
                "",
                encoding="utf-8",
            )

            original_repo_root = release_smoke.REPO_ROOT
            release_smoke.REPO_ROOT = repo_root
            try:
                wheel_path = release_smoke._resolve_wheel_path("0.2.0")
            finally:
                release_smoke.REPO_ROOT = original_repo_root

            self.assertEqual(
                wheel_path.name,
                "logical_robotics_harness-0.2.0-py3-none-any.whl",
            )

    def test_resolve_wheel_path_fails_with_multiple_wheels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = pathlib.Path(temp_dir)
            dist_dir = repo_root / "dist"
            dist_dir.mkdir()
            (dist_dir / "logical_robotics_harness-0.2.0-py3-none-any.whl").write_text(
                "",
                encoding="utf-8",
            )
            (dist_dir / "logical_robotics_harness-0.3.0-py3-none-any.whl").write_text(
                "",
                encoding="utf-8",
            )

            original_repo_root = release_smoke.REPO_ROOT
            release_smoke.REPO_ROOT = repo_root
            try:
                with self.assertRaises(release_smoke.ReleaseSmokeError):
                    release_smoke._resolve_wheel_path("")
            finally:
                release_smoke.REPO_ROOT = original_repo_root


if __name__ == "__main__":
    unittest.main()
