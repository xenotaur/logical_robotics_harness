"""``scripts/test`` warns when an active environment does not supply $PYTHON.

The interpreter is a stub that exits 0, so no real test suite runs; only the
environment preflight and its stderr output are exercised.
"""

import os
import pathlib
import stat
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
WARNING = "scripts/test: warning:"


class WrongEnvironmentWarningTest(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.root = pathlib.Path(temp_dir.name).resolve()
        self.env_prefix = self.root / "env"
        self.other_prefix = self.root / "other"

    def _stub_python3(self, prefix: pathlib.Path) -> pathlib.Path:
        bin_dir = prefix / "bin"
        bin_dir.mkdir(parents=True)
        python3 = bin_dir / "python3"
        python3.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        python3.chmod(python3.stat().st_mode | stat.S_IXUSR)
        return bin_dir

    def _run(
        self, python_bin: pathlib.Path, env_vars: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": os.pathsep.join([str(python_bin), "/usr/bin", "/bin"]),
            "HOME": str(self.root),
        }
        env.update(env_vars)
        return subprocess.run(
            ["scripts/test"],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
            timeout=60,
        )

    def test_warns_when_conda_python_is_outside_the_active_env(self) -> None:
        other_bin = self._stub_python3(self.other_prefix)

        result = self._run(other_bin, {"CONDA_PREFIX": str(self.env_prefix)})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(WARNING, result.stderr)
        self.assertIn(str(self.env_prefix), result.stderr)
        self.assertIn(str(other_bin / "python3"), result.stderr)

    def test_warns_when_venv_python_is_outside_the_active_env(self) -> None:
        other_bin = self._stub_python3(self.other_prefix)

        result = self._run(other_bin, {"VIRTUAL_ENV": str(self.env_prefix)})

        self.assertIn(WARNING, result.stderr)

    def test_silent_when_python_comes_from_the_active_env(self) -> None:
        env_bin = self._stub_python3(self.env_prefix)

        result = self._run(env_bin, {"CONDA_PREFIX": str(self.env_prefix)})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(WARNING, result.stderr)

    def test_silent_when_no_environment_is_active(self) -> None:
        other_bin = self._stub_python3(self.other_prefix)

        result = self._run(other_bin, {})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(WARNING, result.stderr)


if __name__ == "__main__":
    unittest.main()
