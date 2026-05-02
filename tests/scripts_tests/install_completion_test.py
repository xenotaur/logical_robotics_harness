import os
import pathlib
import subprocess
import unittest


class InstallCompletionScriptTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _script_path(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "install-completion"

    def test_script_runs_and_prints_guidance(self) -> None:
        result = subprocess.run(
            [str(self._script_path())],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
            env=os.environ.copy(),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Detected shell:", result.stdout)
        self.assertIn("To enable completion now:", result.stdout)
        self.assertIn("To persist, add this line", result.stdout)

    def test_script_uses_zsh_command_when_shell_is_zsh(self) -> None:
        env = os.environ.copy()
        env["SHELL"] = "/bin/zsh"
        result = subprocess.run(
            [str(self._script_path())],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Detected shell: zsh", result.stdout)
        self.assertIn("register-python-argcomplete --shell zsh lrh", result.stdout)

    def test_script_handles_missing_shell_env(self) -> None:
        env = os.environ.copy()
        env.pop("SHELL", None)
        result = subprocess.run(
            [str(self._script_path())],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Detected shell:", result.stdout)

    def test_script_handles_empty_shell_env(self) -> None:
        env = os.environ.copy()
        env["SHELL"] = ""
        result = subprocess.run(
            [str(self._script_path())],
            check=False,
            capture_output=True,
            text=True,
            cwd=self._repo_root(),
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Detected shell: unknown", result.stdout)
