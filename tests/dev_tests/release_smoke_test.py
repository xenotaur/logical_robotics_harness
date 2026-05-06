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

    def test_venv_command_environment_removes_pythonpath(self) -> None:
        sanitized = release_smoke._venv_command_environment(
            {"PYTHONPATH": "/workspace/src", "PIP_INDEX_URL": "https://example.invalid"}
        )

        self.assertNotIn("PYTHONPATH", sanitized)
        self.assertEqual(sanitized["PIP_INDEX_URL"], "https://example.invalid")

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
            (dist_dir / "lrh-0.2.0-py3-none-any.whl").write_text(
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
                "lrh-0.2.0-py3-none-any.whl",
            )

    def test_resolve_wheel_path_fails_with_multiple_wheels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = pathlib.Path(temp_dir)
            dist_dir = repo_root / "dist"
            dist_dir.mkdir()
            (dist_dir / "lrh-0.2.0-py3-none-any.whl").write_text(
                "",
                encoding="utf-8",
            )
            (dist_dir / "lrh-0.3.0-py3-none-any.whl").write_text(
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
    def test_parser_enables_diagnostic_and_strict_isolation_modes(self) -> None:
        args = release_smoke._build_parser().parse_args(
            ["v0.2.3", "--diagnose", "--strict-isolation"]
        )

        self.assertEqual(args.expected_version, "v0.2.3")
        self.assertTrue(args.diagnose)
        self.assertTrue(args.strict_isolation)

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
                    "lrh",
                ),
                returncode=1,
                stdout="",
                stderr="WARNING: Package(s) not found: lrh\n",
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

        self.assertIn("pip show -f lrh", rendered)
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

    def test_check_preinstall_visibility_detects_pip_package(self) -> None:
        fake_python = pathlib.Path("/tmp/venv/bin/python")

        def _fake_capture(
            command: list[str], *, env: object | None = None
        ) -> release_smoke.DiagnosticCommandResult:
            self.assertIsInstance(env, dict)
            self.assertNotIn("PYTHONPATH", env)
            if command[:4] == [str(fake_python), "-m", "pip", "show"]:
                return release_smoke.DiagnosticCommandResult(
                    tuple(command), 0, "Name: lrh\n", ""
                )
            return release_smoke.DiagnosticCommandResult(
                tuple(command), 0, "None\n", ""
            )

        with mock.patch.object(
            release_smoke, "_capture_diagnostic_command", side_effect=_fake_capture
        ):
            visibility = release_smoke.check_preinstall_visibility(fake_python)

        self.assertTrue(visibility.is_visible)

    def test_check_preinstall_visibility_detects_lrh_import_spec(self) -> None:
        fake_python = pathlib.Path("/tmp/venv/bin/python")

        def _fake_capture(
            command: list[str], *, env: object | None = None
        ) -> release_smoke.DiagnosticCommandResult:
            self.assertIsInstance(env, dict)
            self.assertNotIn("PYTHONPATH", env)
            if command[:4] == [str(fake_python), "-m", "pip", "show"]:
                return release_smoke.DiagnosticCommandResult(
                    tuple(command),
                    1,
                    "",
                    "WARNING: Package(s) not found: lrh\n",
                )
            return release_smoke.DiagnosticCommandResult(
                tuple(command), 0, "ModuleSpec(name='lrh')\n", ""
            )

        with mock.patch.object(
            release_smoke, "_capture_diagnostic_command", side_effect=_fake_capture
        ):
            visibility = release_smoke.check_preinstall_visibility(fake_python)

        self.assertTrue(visibility.is_visible)

    def test_check_preinstall_visibility_treats_not_found_as_not_visible(self) -> None:
        fake_python = pathlib.Path("/tmp/venv/bin/python")

        def _fake_capture(
            command: list[str], *, env: object | None = None
        ) -> release_smoke.DiagnosticCommandResult:
            self.assertIsInstance(env, dict)
            self.assertNotIn("PYTHONPATH", env)
            if command[:4] == [str(fake_python), "-m", "pip", "show"]:
                return release_smoke.DiagnosticCommandResult(
                    tuple(command),
                    1,
                    "",
                    "WARNING: Package(s) not found: lrh\n",
                )
            return release_smoke.DiagnosticCommandResult(
                tuple(command), 0, "None\n", ""
            )

        with mock.patch.object(
            release_smoke, "_capture_diagnostic_command", side_effect=_fake_capture
        ):
            visibility = release_smoke.check_preinstall_visibility(fake_python)

        self.assertFalse(visibility.is_visible)


class ReleaseSmokeRunTest(unittest.TestCase):
    def _build_fake_paths(
        self, root: pathlib.Path
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        fake_venv = root / "venv"
        fake_python = fake_venv / "bin" / "python"
        fake_lrh = fake_venv / "bin" / "lrh"
        return fake_venv, fake_python, fake_lrh

    def _visibility(self, *, visible: bool) -> release_smoke.PreinstallVisibility:
        pip_show_returncode = 0 if visible else 1
        pip_show_stdout = "Name: lrh\n" if visible else ""
        return release_smoke.PreinstallVisibility(
            pip_show=release_smoke.DiagnosticCommandResult(
                ("python", "-m", "pip", "show", "lrh"),
                pip_show_returncode,
                pip_show_stdout,
                "",
            ),
            lrh_spec=release_smoke.DiagnosticCommandResult(
                ("python", "-c", "find_spec"),
                0,
                "None\n",
                "",
            ),
        )

    def test_run_release_smoke_installs_wheel_via_venv_python_with_force_reinstall(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")

            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )

            commands: list[list[str]] = []
            command_envs: list[object | None] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd
                commands.append(command)
                command_envs.append(env)
                if command == [str(fake_lrh), "--version"]:
                    return "lrh 0.2.1"
                return ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.dict(
                    release_smoke.os.environ, {"PYTHONPATH": "/workspace/src"}
                ),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=False),
                ) as check_visibility,
                mock.patch("shutil.rmtree") as rmtree,
            ):
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
        check_visibility.assert_called_once_with(fake_python, command_environ=mock.ANY)
        self.assertNotIn(
            "PYTHONPATH", check_visibility.call_args.kwargs["command_environ"]
        )
        install_command_index = commands.index(
            [
                str(fake_python),
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                str(fake_wheel),
            ]
        )
        self.assertIsInstance(command_envs[install_command_index], dict)
        self.assertNotIn("PYTHONPATH", command_envs[install_command_index])
        rmtree.assert_called_once_with(fake_root, ignore_errors=True)

    def test_run_release_smoke_prints_diagnostics_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd, env
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
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=False),
                ),
                mock.patch("builtins.print") as print_mock,
            ):
                release_smoke.run_release_smoke("v0.2.1", preserve=True, diagnose=True)

        collect_diagnostics.assert_called_once_with(
            fake_venv, fake_python, command_environ=mock.ANY
        )
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

    def test_default_mode_warns_but_continues_when_preinstall_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            _, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd, env
                commands.append(command)
                return "lrh 0.2.1" if command[-1] == "--version" else ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=True),
                ),
                mock.patch("builtins.print") as print_mock,
            ):
                exit_code = release_smoke.run_release_smoke("v0.2.1", preserve=True)

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
        warning_calls = [
            call
            for call in print_mock.call_args_list
            if call.args and "WARNING: pre-install LRH visibility" in call.args[0]
        ]
        self.assertTrue(warning_calls)

    def test_strict_isolation_fails_when_preinstall_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            _, fake_python, _ = self._build_fake_paths(fake_root)
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd, env
                commands.append(command)
                return ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=True),
                ),
            ):
                with self.assertRaisesRegex(
                    release_smoke.ReleaseSmokeError,
                    "--diagnose --preserve",
                ) as context:
                    release_smoke.run_release_smoke(
                        "v0.2.1", preserve=True, strict_isolation=True
                    )

        self.assertIn("Strict isolation mode fails", str(context.exception))
        self.assertNotIn(
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

    def test_strict_isolation_passes_when_preinstall_not_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            _, fake_python, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd, env
                commands.append(command)
                return "lrh 0.2.1" if command[-1] == "--version" else ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=False),
                ),
            ):
                exit_code = release_smoke.run_release_smoke(
                    "v0.2.1", preserve=True, strict_isolation=True
                )

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

    def test_diagnose_strict_isolation_prints_diagnostics_before_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, fake_python, _ = self._build_fake_paths(fake_root)
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )

            diagnostics = release_smoke.IsolationDiagnostics(
                python_executable=fake_python,
                pyvenv_cfg="",
                pip_version=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                site=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                interpreter=release_smoke.DiagnosticCommandResult((), 0, "", ""),
                pip_show=release_smoke.DiagnosticCommandResult((), 0, "Name: x", ""),
                lrh_spec=release_smoke.DiagnosticCommandResult((), 0, "None", ""),
                pth_files=(),
                environment=(),
            )

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", return_value=""),
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
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=True),
                ),
                mock.patch("builtins.print") as print_mock,
            ):
                with self.assertRaises(release_smoke.ReleaseSmokeError):
                    release_smoke.run_release_smoke(
                        "v0.2.1",
                        preserve=True,
                        diagnose=True,
                        strict_isolation=True,
                    )

        collect_diagnostics.assert_called_once_with(
            fake_venv, fake_python, command_environ=mock.ANY
        )
        render_diagnostics.assert_called_once_with(diagnostics)
        print_mock.assert_any_call("diagnostic text")

    def test_run_release_smoke_preserve_skips_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_root = pathlib.Path(temp_dir)
            fake_venv, _, fake_lrh = self._build_fake_paths(fake_root)
            fake_lrh.parent.mkdir(parents=True, exist_ok=True)
            fake_lrh.write_text("", encoding="utf-8")
            fake_wheel = (
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )
            commands: list[list[str]] = []

            def _fake_run(
                command: list[str],
                *,
                cwd: pathlib.Path | None = None,
                env: object | None = None,
            ) -> str:
                del cwd, env
                commands.append(command)
                return "lrh 0.2.1" if command[-1] == "--version" else ""

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", side_effect=_fake_run),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=False),
                ),
                mock.patch("shutil.rmtree") as rmtree,
            ):
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
                release_smoke.REPO_ROOT / "dist" / ("lrh-0.2.1-py3-none-any.whl")
            )

            with (
                mock.patch("tempfile.mkdtemp", return_value=str(fake_root)),
                mock.patch.object(
                    release_smoke, "_resolve_wheel_path", return_value=fake_wheel
                ),
                mock.patch.object(release_smoke, "_run", return_value=""),
                mock.patch.object(
                    release_smoke,
                    "check_preinstall_visibility",
                    return_value=self._visibility(visible=False),
                ),
            ):
                with self.assertRaisesRegex(
                    release_smoke.ReleaseSmokeError,
                    "installed console script is missing",
                ):
                    release_smoke.run_release_smoke("v0.2.1", preserve=True)


if __name__ == "__main__":
    unittest.main()
