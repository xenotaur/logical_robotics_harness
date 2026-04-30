import os
import pathlib
import subprocess
import tempfile
import unittest
import venv

_PIP_COMMAND_TIMEOUT_SECONDS = 120


class PromptCliInstallSmokeTests(unittest.TestCase):
    def _pip_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        env["PIP_NO_INPUT"] = "1"
        env.setdefault("PIP_DEFAULT_TIMEOUT", "15")
        return env

    def _run_with_timeout(
        self, args: list[str], *, cwd: pathlib.Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                args,
                check=False,
                capture_output=True,
                text=True,
                cwd=str(cwd) if cwd else None,
                env=self._pip_env(),
                timeout=_PIP_COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                "Timed out while running command after "
                f"{_PIP_COMMAND_TIMEOUT_SECONDS}s: {exc.cmd}\n"
                f"stdout:\n{exc.stdout or ''}\n"
                f"stderr:\n{exc.stderr or ''}"
            )

    def _maybe_skip_for_unavailable_build_deps(
        self, result: subprocess.CompletedProcess[str], install_mode: str
    ) -> None:
        if result.returncode == 0:
            return

        lower_stderr = result.stderr.lower()
        network_markers = (
            "no matching distribution found",
            "could not find a version that satisfies the requirement",
            "proxyerror",
            "tunnel connection failed",
            "temporary failure in name resolution",
        )
        if any(marker in lower_stderr for marker in network_markers):
            self.skipTest(
                "Skipping "
                f"{install_mode} install smoke due to unavailable "
                "build dependencies in environment."
            )

    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def test_installed_prompt_cli_works_from_isolated_repo(self) -> None:
        repo_root = self._repo_root()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            venv_dir = temp_path / "venv"
            run_dir = temp_path / "target_repo"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "project" / "executions").mkdir(parents=True, exist_ok=True)

            venv.EnvBuilder(with_pip=True).create(venv_dir)
            python_bin = venv_dir / "bin" / "python"
            lrh_bin = venv_dir / "bin" / "lrh"

            install_editable = self._run_with_timeout(
                [
                    str(python_bin),
                    "-m",
                    "pip",
                    "install",
                    "--no-input",
                    "-e",
                    str(repo_root),
                ]
            )
            self._maybe_skip_for_unavailable_build_deps(
                install_editable, install_mode="editable"
            )
            self.assertEqual(
                install_editable.returncode, 0, msg=install_editable.stderr
            )

            help_result = self._run_with_timeout([str(lrh_bin), "--help"], cwd=run_dir)
            self.assertEqual(help_result.returncode, 0, msg=help_result.stderr)
            self.assertIn("Logical Robotics Harness", help_result.stdout)

            label_result = self._run_with_timeout(
                [str(lrh_bin), "prompt", "label", "--slug", "example"], cwd=run_dir
            )
            self.assertEqual(label_result.returncode, 0, msg=label_result.stderr)
            self.assertIn("prompt_id: PROMPT(AD_HOC:EXAMPLE)", label_result.stdout)
            self.assertIn(
                "execution_dir: project/executions/AD_HOC", label_result.stdout
            )

            record_result = self._run_with_timeout(
                [
                    str(lrh_bin),
                    "prompt",
                    "record-execution",
                    "--prompt-id",
                    "PROMPT(AD_HOC:EXAMPLE)[2026-04-30T00:00:00-04:00]",
                    "--slug",
                    "example",
                    "--dry-run",
                ],
                cwd=run_dir,
            )
            self.assertEqual(record_result.returncode, 0, msg=record_result.stderr)
            self.assertIn("output_file:", record_result.stdout)
            self.assertIn("prompt_id: PROMPT(AD_HOC:EXAMPLE)", record_result.stdout)


if __name__ == "__main__":
    unittest.main()
