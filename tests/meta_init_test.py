import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest

from lrh.meta import workspace


class TestMetaInitRuntime(unittest.TestCase):
    def test_init_workspace_in_empty_directory_creates_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
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
            self.assertIn('mode = "workspace"', config)
            self.assertIn('name = "Demo Workspace"', config)
            self.assertGreater(len(result.created), 0)

    def test_init_workspace_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
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
            root = pathlib.Path(tmp_dir)
            (root / ".lrh").write_text("not a directory", encoding="utf-8")

            with self.assertRaises(workspace.MetaInitError):
                workspace.init_workspace(
                    root,
                    spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                )

    def test_init_workspace_force_replaces_incompatible_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
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
            root = pathlib.Path(tmp_dir)
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
            root = pathlib.Path(tmp_dir)
            (root / ".lrh" / "config.toml").mkdir(parents=True)

            with self.assertRaises(workspace.MetaInitError):
                workspace.init_workspace(
                    root,
                    spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
                )

    def test_init_workspace_force_replaces_directory_config_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
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
            root = pathlib.Path(tmp_dir)
            workspace_name = 'A "B" \\\\ C\nD'

            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name=workspace_name),
            )

            config_text = (root / ".lrh" / "config.toml").read_text(encoding="utf-8")
            parsed = tomllib.loads(config_text)

            self.assertEqual(parsed["workspace"]["name"], workspace_name)


class TestMetaInitCli(unittest.TestCase):
    def _run_lrh(
        self, args: list[str], cwd: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        src_path = pathlib.Path("src").resolve()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_path) if not existing else f"{src_path}{os.pathsep}{existing}"
        )
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
        )

    def test_lrh_meta_init_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            result = self._run_lrh(["meta", "init", "--name", "CLI Workspace"], root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Initialized LRH meta workspace", result.stdout)
            self.assertTrue((root / ".lrh" / "config.toml").exists())


if __name__ == "__main__":
    unittest.main()
