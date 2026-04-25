import os
import pathlib
import subprocess
import unittest


class VersionScriptTests(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _version_script(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "version"

    def test_version_script_reports_lrh_metadata_section(self) -> None:
        completed = subprocess.run(
            [str(self._version_script())],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("LRH package metadata", completed.stdout)
        self.assertRegex(completed.stdout, r"lrh (unknown|[^\n]+)")
        self.assertIn("LRH CLI", completed.stdout)


if __name__ == "__main__":
    unittest.main()
