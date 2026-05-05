import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from lrh.dev import release_smoke


class ReleaseSmokeHelpersTest(unittest.TestCase):
    def test_normalize_version_accepts_tag_or_plain_version(self) -> None:
        self.assertEqual(release_smoke.normalize_version("v0.2.0"), "0.2.0")
        self.assertEqual(release_smoke.normalize_version("0.2.0"), "0.2.0")
        self.assertEqual(release_smoke.normalize_version(""), "")

    def test_normalize_version_rejects_invalid_value(self) -> None:
        with self.assertRaises(release_smoke.ReleaseSmokeError):
            release_smoke.normalize_version("release-0.2.0")

    def test_run_raises_clear_error_for_missing_command(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(
                release_smoke.ReleaseSmokeError,
                "required command not found",
            ):
                release_smoke._run(["missing-command"])

    def test_run_uses_current_repo_root_when_cwd_not_provided(self) -> None:
        fake_root = pathlib.Path("/tmp/fake-root")

        with mock.patch("subprocess.run") as subprocess_run:
            subprocess_run.return_value = subprocess.CompletedProcess(
                args=["echo"],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
            original_repo_root = release_smoke.REPO_ROOT
            release_smoke.REPO_ROOT = fake_root
            try:
                release_smoke._run(["echo", "ok"])
            finally:
                release_smoke.REPO_ROOT = original_repo_root

        self.assertEqual(subprocess_run.call_args.kwargs["cwd"], fake_root)

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


class ReleaseSmokeDiagnosticsTest(unittest.TestCase):
    def test_parser_enables_diagnostic_mode(self) -> None:
        args = release_smoke._build_parser().parse_args(["v0.2.3", "--diagnose"])

        self.assertEqual(args.expected_version, "v0.2.3")
        self.assertTrue(args.diagnose)

    def test_render_pip_show_not_found_as_diagnostic(self) -> None:
        diagnostics = release_smoke.IsolationDiagnostics(
            python_executable=pathlib.Path("/tmp/venv/bin/python"),
            pyvenv_cfg="include-system-site-packages = false\n",
            pip_version=release_smoke.DiagnosticCommandResult(
                command=("python", "-m", "pip", "--version"),
                returncode=0,
                stdout="pip 24.0\n",
                stderr="",
            ),
            site=release_smoke.DiagnosticCommandResult(
                command=("python", "-m", "site"),
                returncode=0,
                stdout="site output\n",
                stderr="",
            ),
            interpreter=release_smoke.DiagnosticCommandResult(
                command=("python", "-c", "identity"),
                returncode=0,
                stdout="sys.executable = /tmp/venv/bin/python\n",
                stderr="",
            ),
            pip_show=release_smoke.DiagnosticCommandResult(
                command=(
                    "python",
                    "-m",
                    "pip",
                    "show",
                    "-f",
                    "logical-robotics-harness",
                ),
                returncode=1,
                stdout="",
                stderr="WARNING: Package(s) not found: logical-robotics-harness\n",
            ),
            lrh_spec=release_smoke.DiagnosticCommandResult(
                command=("python", "-c", "find_spec"),
                returncode=0,
                stdout="None\n",
                stderr="",
            ),
            pth_files=(),
            environment=(),
        )

        rendered = release_smoke.render_isolation_diagnostics(diagnostics)

        self.assertIn("pip show -f logical-robotics-harness", rendered)
        self.assertIn("returncode: 1", rendered)
        self.assertIn("Package(s) not found", rendered)

    def test_pth_file_discovery_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = pathlib.Path(temp_dir) / "venv"
            site_packages = venv_path / "lib" / "python3.12" / "site-packages"
            site_packages.mkdir(parents=True)
            (site_packages / "zeta.pth").write_text("/zeta\n", encoding="utf-8")
            (site_packages / "alpha.pth").write_text("/alpha\n", encoding="utf-8")

            diagnostics = release_smoke._discover_pth_files(venv_path)

        self.assertEqual(
            [item.path.name for item in diagnostics], ["alpha.pth", "zeta.pth"]
        )
        self.assertEqual(
            [item.contents for item in diagnostics], ["/alpha\n", "/zeta\n"]
        )

    def test_filtered_environment_redacts_sensitive_values(self) -> None:
        filtered = release_smoke._filtered_environment(
            {
                "PYTHONPATH": "/workspace/src",
                "PIP_INDEX_URL": "https://user:password@example.invalid/simple",
                "LRH_TOKEN": "abc123",
                "UNRELATED_SECRET": "not included",
            }
        )

        self.assertEqual(
            filtered,
            (
                ("LRH_TOKEN", "<redacted>"),
                ("PIP_INDEX_URL", "<redacted>"),
                ("PYTHONPATH", "/workspace/src"),
            ),
        )


class ReleaseSmokeRunTest(unittest.TestCase):
    def _build_fake_paths(
        self, root: pathlib.Path
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        fake_venv = root / "venv"
        fake_python = fake_venv / "bin" / "python"
        fake_lrh = fake_venv / "bin" / "lrh"
        return fake_venv, fake_python, fake_lrh

    def test_run_release_smoke_installs_wheel_via_venv_python_with_force_reinstall(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")

            fake_wheel = (
                release_smoke.REPO_ROOT
                / "dist"
                / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
            )

            commands: list[list[str]] = []

            def _fake_run(
                command: list[str], *, cwd: pathlib.Path | None = None
            ) -> str:
                del cwd
                commands.append(command)
                if command == [str(fake_lrh), "--version"]:
                    return "lrh 0.2.1"
                return ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch("subprocess.run") as subprocess_run,
                mock.patch("shutil.rmtree") as rmtree,
            ):
                subprocess_run.return_value = subprocess.CompletedProcess(
                    args=[
                        str(fake_python),
                        "-m",
                        "pip",
                        "show",
                        "logical-robotics-harness",
                    ],
                    returncode=1,
                    stdout="",
                    stderr="",
                )

                exit_code = release_smoke.run_release_smoke("v0.2.1", preserve=False)

        self.assertEqual(exit_code, 0)
        self.assertIn(
            [
                str(fake_python),
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                str(fake_wheel),
            ],
            commands,
        )
        self.assertIn(
            [release_smoke.sys.executable, "-m", "venv", str(fake_venv)],
            commands,
        )
        self.assertIn([str(fake_lrh), "--version"], commands)
        self.assertIn([str(fake_lrh), "snapshot", "--help"], commands)
        self.assertTrue(
            commands.index(
                [
                    str(fake_python),
                    "-m",
                    "pip",
                    "install",
                    "--force-reinstall",
                    str(fake_wheel),
                ]
            )
            > commands.index([str(fake_python), "-m", "pip", "--version"])
        )
        subprocess_run.assert_called_once_with(
            [str(fake_python), "-m", "pip", "show", "logical-robotics-harness"],
            check=False,
            capture_output=True,
            text=True,
            cwd=release_smoke.REPO_ROOT,
        )
        rmtree.assert_called_once_with(fake_root, ignore_errors=True)

    def test_run_release_smoke_prints_diagnostics_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT
                / "dist"
                / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str], *, cwd: pathlib.Path | None = None
            ) -> str:
                del cwd
                commands.append(command)
                return "lrh 0.2.1" if command[-1] == "--version" else ""

            diagnostics = release_smoke.IsolationDiagnostics(
                python_executable=fake_python,
                pyvenv_cfg="",
                pip_version=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                site=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                interpreter=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                pip_show=release_smoke.DiagnosticCommandResult((), 1, "", "not found"),
                lrh_spec=release_smoke.DiagnosticCommandResult((), 0, "None", ""),
                pth_files=(),
                environment=(),
            )

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "collect_isolation_diagnostics",
                    return_value=diagnostics,
                ) as collect_diagnostics,
                mock.patch.object(
                    release_smoke,
                    "render_isolation_diagnostics",
                    return_value="diagnostic text",
                ) as render_diagnostics,
                mock.patch("subprocess.run") as subprocess_run,
                mock.patch("builtins.print") as print_mock,
            ):
                subprocess_run.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                    stdout="",
                    stderr="",
                )
                release_smoke.run_release_smoke("v0.2.1", preserve=True, diagnose=True)

        collect_diagnostics.assert_called_once_with(fake_venv, fake_python)
        render_diagnostics.assert_called_once_with(diagnostics)
        print_mock.assert_any_call("diagnostic text")
        self.assertLess(
            commands.index([str(fake_python), "-m", "pip", "--version"]),
            commands.index(
                [
                    str(fake_python),
                    "-m",
                    "pip",
                    "install",
                    "--force-reinstall",
                    str(fake_wheel),
                ]
            ),
        )

    def test_run_release_smoke_preserve_skips_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, _, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT
                / "dist"
                / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str], *, cwd: pathlib.Path | None = None
            ) -> str:
                del cwd
                commands.append(command)
                return "lrh 0.2.1" if command[-1] == "--version" else ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch("subprocess.run") as subprocess_run,
                mock.patch("shutil.rmtree") as rmtree,
            ):
                subprocess_run.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                    stdout="",
                    stderr="",
                )
                release_smoke.run_release_smoke("", preserve=True)

        rmtree.assert_not_called()
        self.assertIn([str(fake_venv / "bin" / "lrh"), "--version"], commands)
        self.assertIn([str(fake_venv / "bin" / "lrh"), "snapshot", "--help"], commands)

    def test_run_release_smoke_raises_when_lrh_console_script_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            _, _, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_wheel = (
                release_smoke.REPO_ROOT
                / "dist"
                / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
            )

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", return_value=""),
                mock.patch("subprocess.run") as subprocess_run,
            ):
                subprocess_run.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                    stdout="",
                    stderr="",
                )
                with self.assertRaisesRegex(
                    release_smoke.ReleaseSmokeError,
                    "installed console script is missing",
                ):
                    release_smoke.run_release_smoke("v0.2.1", preserve=True)


if __name__ == "__main__":
    unittest.main()
