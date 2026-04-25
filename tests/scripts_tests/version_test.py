import os
import pathlib
import subprocess
import unittest


class VersionScriptTests(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _version_script(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "version"

    def test_version_script_prints_lrh_version_by_default(self) -> None:
        completed = subprocess.run(
            [str(self._version_script())],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertRegex(completed.stdout.strip(), r"^lrh (unknown|[^\n]+)$")

    def test_version_script_exposes_expected_subcommands(self) -> None:
        completed = subprocess.run(
            [str(self._version_script()), "--help"],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("tools", completed.stdout)
        self.assertIn("verify", completed.stdout)
        self.assertIn("tag", completed.stdout)
        self.assertIn("push", completed.stdout)


if __name__ == "__main__":
    unittest.main()
