import os
import pathlib
import subprocess
import unittest


class ReleaseSmokeScriptTests(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def test_release_smoke_help_succeeds(self) -> None:
        completed = subprocess.run(
            ["scripts/release-smoke", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("expected_version", completed.stdout)
        self.assertIn("--preserve", completed.stdout)


if __name__ == "__main__":
    unittest.main()
