import os
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest


class DevelopScriptTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _script_path(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "develop"

    def _write_fake_python(
        self, temp_dir: pathlib.Path, exit_code: int
    ) -> pathlib.Path:
        fake_python = temp_dir / "python"
        fake_python.write_text(
            textwrap.dedent(f"""\
                #!/bin/bash
                echo "fake pip output" >&2
                exit {exit_code}
                """),
            encoding="utf-8",
        )
        fake_python.chmod(fake_python.stat().st_mode | stat.S_IXUSR)
        return fake_python

    def test_develop_script_preserves_install_exit_code_and_prints_diagnostic(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = pathlib.Path(temp_dir_str)
            self._write_fake_python(temp_dir=temp_dir, exit_code=23)
            env = os.environ.copy()
            env["PATH"] = f"{temp_dir}:{env['PATH']}"

            result = subprocess.run(
                [str(self._script_path())],
                check=False,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
                env=env,
            )

        self.assertEqual(result.returncode, 23)
        self.assertIn(
            "scripts/develop failed during editable development install.",
            result.stderr,
        )
        self.assertIn("scripts/version tools", result.stderr)
        self.assertIn("scripts/test", result.stderr)

    def test_develop_script_success_path_has_no_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = pathlib.Path(temp_dir_str)
            self._write_fake_python(temp_dir=temp_dir, exit_code=0)
            env = os.environ.copy()
            env["PATH"] = f"{temp_dir}:{env['PATH']}"

            result = subprocess.run(
                [str(self._script_path())],
                check=False,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertNotIn(
            "scripts/develop failed during editable development install.",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
