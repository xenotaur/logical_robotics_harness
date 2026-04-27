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


class ReleaseSmokeRunTest(unittest.TestCase):
    def test_run_release_smoke_installs_wheel_via_venv_python_with_force_reinstall(
        self,
    ) -> None:
        fake_root = pathlib.Path("/tmp/lrh-release-smoke-root")
        fake_venv = fake_root / "venv"
        fake_python = fake_venv / "bin" / "python"
        fake_lrh = fake_venv / "bin" / "lrh"
        fake_wheel = (
            release_smoke.REPO_ROOT
            / "dist"
            / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
        )

        commands: list[list[str]] = []

        def _fake_run(command: list[str], *, cwd: pathlib.Path | None = None) -> str:
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
            mock.patch("pathlib.Path.exists", return_value=True),
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

    def test_run_release_smoke_preserve_skips_cleanup(self) -> None:
        fake_root = pathlib.Path("/tmp/lrh-release-smoke-root")
        fake_venv = fake_root / "venv"
        fake_wheel = (
            release_smoke.REPO_ROOT
            / "dist"
            / ("logical_robotics_harness-0.2.1-py3-none-any.whl")
        )
        commands: list[list[str]] = []

        def _fake_run(command: list[str], *, cwd: pathlib.Path | None = None) -> str:
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
            mock.patch("pathlib.Path.exists", return_value=True),
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


if __name__ == "__main__":
    unittest.main()
