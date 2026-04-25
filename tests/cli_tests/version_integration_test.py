import importlib.metadata
import subprocess
import tempfile
import unittest

from lrh import version as lrh_version


class TestLrhVersionIntegration(unittest.TestCase):
    def test_lrh_dashdash_version_matches_installed_package_metadata(self) -> None:
        try:
            expected_version = importlib.metadata.version(lrh_version.DISTRIBUTION_NAME)
        except importlib.metadata.PackageNotFoundError:
            expected_version = "unknown"

        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                ["lrh", "--version"],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stderr, "")

        output = result.stdout.strip()
        self.assertNotEqual(output, "")

        self.assertEqual(output, f"lrh {expected_version}")


if __name__ == "__main__":
    unittest.main()
