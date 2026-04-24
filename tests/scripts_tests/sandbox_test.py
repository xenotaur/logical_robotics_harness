import os
import pathlib
import subprocess
import sys
import unittest


class TestSandboxScript(unittest.TestCase):
    def _sandbox_script(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2] / "scripts" / "sandbox"

    def test_sandbox_runs_non_interactive_command_with_isolated_paths(self) -> None:
        script = self._sandbox_script()
        command = [
            sys.executable,
            str(script),
            "--cleanup",
            "--",
            sys.executable,
            "-c",
            (
                "import os, pathlib; "
                "workspace = pathlib.Path.cwd(); "
                "root = workspace.parent; "
                "assert workspace.name == 'workspace'; "
                "assert pathlib.Path(os.environ['HOME']) == root / 'home'; "
                "assert pathlib.Path(os.environ['XDG_CONFIG_HOME']) == "
                "root / 'xdg' / 'config'; "
                "assert pathlib.Path(os.environ['XDG_STATE_HOME']) == "
                "root / 'xdg' / 'state'; "
                "assert pathlib.Path(os.environ['XDG_CACHE_HOME']) == "
                "root / 'xdg' / 'cache'; "
                "assert pathlib.Path(os.environ['XDG_DATA_HOME']) == "
                "root / 'xdg' / 'data'; "
                "assert pathlib.Path(os.environ['TMPDIR']) == root / 'tmp'"
            ),
        ]

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)

    def test_sandbox_returns_wrapped_command_exit_code(self) -> None:
        script = self._sandbox_script()
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--cleanup",
                "--",
                sys.executable,
                "-c",
                "import sys; sys.exit(7)",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 7)
