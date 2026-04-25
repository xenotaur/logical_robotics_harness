import pathlib
import subprocess
import tempfile
import unittest
import venv


class VersionInstallSmokeTests(unittest.TestCase):
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

    def _python_in_venv(self, venv_dir: pathlib.Path) -> pathlib.Path:
        return venv_dir / "bin" / "python"

    def _lrh_in_venv(self, venv_dir: pathlib.Path) -> pathlib.Path:
        return venv_dir / "bin" / "lrh"

    def _create_venv(self, venv_dir: pathlib.Path) -> pathlib.Path:
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        return self._python_in_venv(venv_dir)

    def _assert_cli_matches_metadata(self, venv_dir: pathlib.Path) -> None:
        python_bin = self._python_in_venv(venv_dir)
        lrh_bin = self._lrh_in_venv(venv_dir)

        metadata_result = subprocess.run(
            [
                str(python_bin),
                "-c",
                (
                    "import importlib.metadata;"
                    "print(importlib.metadata.version('logical-robotics-harness'))"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(metadata_result.returncode, 0, msg=metadata_result.stderr)
        metadata_version = metadata_result.stdout.strip()

        cli_result = subprocess.run(
            [str(lrh_bin), "--version"],
            check=False,
            capture_output=True,
            text=True,
            cwd=tempfile.gettempdir(),
        )
        self.assertEqual(cli_result.returncode, 0, msg=cli_result.stderr)
        self.assertEqual(cli_result.stderr, "")
        self.assertEqual(cli_result.stdout.strip(), f"lrh {metadata_version}")

    def test_lrh_version_matches_metadata_for_editable_and_wheel_installs(self) -> None:
        repo_root = self._repo_root()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            editable_venv = temp_path / "venv_editable"
            editable_python = self._create_venv(editable_venv)
            install_editable = subprocess.run(
                [str(editable_python), "-m", "pip", "install", "-e", str(repo_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self._maybe_skip_for_unavailable_build_deps(
                install_editable, install_mode="editable"
            )
            self.assertEqual(
                install_editable.returncode, 0, msg=install_editable.stderr
            )
            self._assert_cli_matches_metadata(editable_venv)

            wheel_dir = temp_path / "wheelhouse"
            wheel_dir.mkdir(parents=True, exist_ok=True)
            build_wheel = subprocess.run(
                [
                    str(editable_python),
                    "-m",
                    "pip",
                    "wheel",
                    str(repo_root),
                    "--no-deps",
                    "-w",
                    str(wheel_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self._maybe_skip_for_unavailable_build_deps(
                build_wheel, install_mode="wheel build"
            )
            self.assertEqual(build_wheel.returncode, 0, msg=build_wheel.stderr)

            wheels = sorted(wheel_dir.glob("*.whl"))
            self.assertEqual(len(wheels), 1)

            wheel_venv = temp_path / "venv_wheel"
            wheel_python = self._create_venv(wheel_venv)
            install_wheel = subprocess.run(
                [
                    str(wheel_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    str(wheels[0]),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self._maybe_skip_for_unavailable_build_deps(
                install_wheel, install_mode="wheel install"
            )
            self.assertEqual(install_wheel.returncode, 0, msg=install_wheel.stderr)
            self._assert_cli_matches_metadata(wheel_venv)


if __name__ == "__main__":
    unittest.main()
