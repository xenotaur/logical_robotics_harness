import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest

from lrh.meta import workspace


def _canonical(path: pathlib.Path) -> pathlib.Path:
    return path.resolve()


class TestMetaInitRuntime(unittest.TestCase):
    def test_init_workspace_in_empty_directory_creates_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            result = workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            expected_paths = [
                root / ".lrh",
                root / ".lrh" / "config.toml",
                root / "projects",
                root / "private" / "logs",
                root / "private" / "chats",
                root / "private" / "cache",
                root / "private" / "state",
                root / "private" / "tmp",
                root / "private" / "secrets",
                root / ".gitignore",
                root / "README.md",
            ]
            for expected_path in expected_paths:
                self.assertTrue(expected_path.exists(), f"missing {expected_path}")

            gitignore = (root / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("private/logs/", gitignore)
            self.assertIn("private/secrets/", gitignore)

            config = (root / ".lrh" / "config.toml").read_text(encoding="utf-8")
            self.assertIn('schema_version = "0.1"', config)
            self.assertIn('mode = "local"', config)
            self.assertIn('name = "Demo Workspace"', config)
            self.assertGreater(len(result.created), 0)

    def test_init_workspace_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            second_result = workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            self.assertEqual(second_result.created, ())
            self.assertEqual(second_result.updated, ())
            self.assertGreater(len(second_result.unchanged), 0)

    def test_init_workspace_fails_on_incompatible_state_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            (root / ".lrh").write_text("not a directory", encoding="utf-8")

            with self.assertRaises(workspace.MetaInitError):
                workspace.init_workspace(
                    root,
                    spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                )

    def test_init_workspace_force_replaces_incompatible_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            (root / ".lrh").write_text("not a directory", encoding="utf-8")

            result = workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                force=True,
            )
            self.assertTrue((root / ".lrh").is_dir())
            self.assertIn(root / ".lrh", result.created)

    def test_init_workspace_config_conflict_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            (root / ".lrh").mkdir(parents=True)
            (root / ".lrh" / "config.toml").write_text(
                'schema_version = "broken"\n', encoding="utf-8"
            )

            with self.assertRaises(workspace.MetaInitError):
                workspace.init_workspace(
                    root,
                    spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                )

            forced_result = workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                force=True,
            )
            self.assertIn(root / ".lrh" / "config.toml", forced_result.updated)

    def test_init_workspace_config_path_directory_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            (root / ".lrh" / "config.toml").mkdir(parents=True)

            with self.assertRaises(workspace.MetaInitError):
                workspace.init_workspace(
                    root,
                    spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                )

    def test_init_workspace_force_replaces_directory_config_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            config_dir = root / ".lrh" / "config.toml"
            config_dir.mkdir(parents=True)
            (config_dir / "placeholder.txt").write_text("x", encoding="utf-8")

            result = workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                force=True,
            )

            self.assertTrue((root / ".lrh" / "config.toml").is_file())
            self.assertIn(root / ".lrh" / "config.toml", result.updated)

    def test_init_workspace_escapes_workspace_name_for_valid_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _canonical(pathlib.Path(tmp_dir))
            workspace_name = 'A "B" \\\\ C\nD'

            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name=workspace_name),
            )

            config_text = (root / ".lrh" / "config.toml").read_text(encoding="utf-8")
            parsed = tomllib.loads(config_text)

            self.assertEqual(parsed["workspace"]["name"], workspace_name)

    def test_init_workspace_writes_normalized_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = _canonical(pathlib.Path(tmp_dir))
            target = base / "a" / ".." / "workspace"

            workspace.init_workspace(
                target,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            parsed = tomllib.loads(
                (target.resolve() / ".lrh" / "config.toml").read_text(encoding="utf-8")
            )
            for key in (
                "catalog_root",
                "projects_dir",
                "config_dir",
                "state_dir",
                "cache_dir",
            ):
                self.assertTrue(pathlib.Path(parsed["paths"][key]).is_absolute())


class TestMetaInitCli(unittest.TestCase):
    def _run_lrh(
        self,
        args: list[str],
        cwd: pathlib.Path,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = pathlib.Path("src").resolve()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_path) if not existing else f"{src_path}{os.pathsep}{existing}"
        )
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
        )

    def test_lrh_meta_init_cli_defaults_to_hybrid_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
            }
            result = self._run_lrh(
                ["meta", "init", "--name", "CLI Workspace"],
                root,
                env_overrides=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Initialized LRH hybrid meta workspace", result.stdout)
            self.assertTrue((root / ".lrh" / "config.toml").exists())
            self.assertTrue((xdg_config / "lrh" / "config.toml").exists())
            self.assertTrue((xdg_cache / "lrh" / "cache").exists())
            self.assertTrue((xdg_state / "lrh" / "private" / "state").exists())

    def test_lrh_meta_init_cli_hybrid_with_positional_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace_root = root / "workspace"
            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
            }

            result = self._run_lrh(
                ["meta", "init", str(workspace_root), "--name", "CLI Workspace"],
                root,
                env_overrides=env,
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue((workspace_root / ".lrh" / "config.toml").exists())
            parsed = tomllib.loads(
                (xdg_config / "lrh" / "config.toml").read_text(encoding="utf-8")
            )
            self.assertEqual(parsed["workspace"]["mode"], "hybrid")
            self.assertEqual(
                pathlib.Path(parsed["paths"]["catalog_root"]).resolve(),
                workspace_root.resolve(),
            )

    def test_lrh_meta_init_cli_mode_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            result = self._run_lrh(
                ["meta", "init", "--mode", "local", "--name", "CLI Workspace"],
                root,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Initialized LRH local meta workspace", result.stdout)
            self.assertTrue((root / ".lrh" / "config.toml").exists())

    def test_lrh_meta_init_cli_mode_global(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
            }
            result = self._run_lrh(
                ["meta", "init", "--mode", "global", "--name", "CLI Workspace"],
                root,
                env_overrides=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Initialized LRH global meta workspace", result.stdout)
            self.assertTrue((xdg_config / "lrh" / "config.toml").exists())

    def test_lrh_meta_init_cli_handles_invalid_xdg_state_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            xdg_config = root / "xdg-config"
            xdg_state_home_file = root / "xdg-state-home-file"
            xdg_state_home_file.write_text("not-a-directory", encoding="utf-8")
            xdg_cache = root / "xdg-cache"
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state_home_file),
                "XDG_CACHE_HOME": str(xdg_cache),
            }
            result = self._run_lrh(
                ["meta", "init", "--mode", "global", "--name", "CLI Workspace"],
                root,
                env_overrides=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("error: unable to create directory at", result.stdout)
            self.assertNotIn("Traceback", result.stdout)


if __name__ == "__main__":
    unittest.main()
