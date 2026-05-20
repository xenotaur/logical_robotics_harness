import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest

from lrh.meta import workspace


class TestMetaSetUnset(unittest.TestCase):
    def test_set_project_dir_and_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            reg = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            ws = workspace.resolve_meta_workspace(cwd=root)

            result = workspace.set_project_fields_in_workspace(
                ws,
                selector="demo",
                project_dir="project/control",
                short_name="demo2",
                display_name="Demo Two",
            )
            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["locators"]["project_dir"], "project/control")
            self.assertEqual(parsed["project"]["short_name"], "demo2")
            self.assertEqual(parsed["project"]["display_name"], "Demo Two")
            self.assertEqual(parsed["identity"]["project_id"], reg.project_id)

    def test_set_project_dir_rejects_absolute_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            ws = workspace.resolve_meta_workspace(cwd=root)

            with self.assertRaises(workspace.MetaRegistryError):
                workspace.set_project_fields_in_workspace(
                    ws, selector="demo", project_dir="/abs"
                )
            with self.assertRaises(workspace.MetaRegistryError):
                workspace.set_project_fields_in_workspace(
                    ws, selector="demo", project_dir="../escape"
                )

    def test_set_and_unset_local_repo_path_respects_trust_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            reg = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            ws = workspace.resolve_meta_workspace(cwd=root)

            workspace.set_project_fields_in_workspace(
                ws, selector="demo", local_repo_path=str(repo)
            )
            private_file = ws.state_dir / "local_state.toml"
            self.assertTrue(private_file.exists())

            workspace.set_meta_config_value(
                ws, "trusted-persistent-local-state", "true"
            )
            workspace.set_project_fields_in_workspace(
                ws, selector="demo", local_repo_path=str(repo)
            )
            trusted_file = ws.catalog_root / ".lrh" / "trusted_local_state.toml"
            self.assertTrue(trusted_file.exists())

            workspace.unset_project_fields_in_workspace(
                ws, selector="demo", local_repo_path=True
            )
            private_data = tomllib.loads(private_file.read_text(encoding="utf-8"))
            trusted_data = tomllib.loads(trusted_file.read_text(encoding="utf-8"))
            self.assertNotIn(reg.project_id, private_data.get("bindings", {}))
            self.assertNotIn(reg.project_id, trusted_data.get("bindings", {}))

    def test_set_is_atomic_when_project_dir_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            reg = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            ws = workspace.resolve_meta_workspace(cwd=root)
            with self.assertRaises(workspace.MetaRegistryError):
                workspace.set_project_fields_in_workspace(
                    ws,
                    selector="demo",
                    local_repo_path=str(repo),
                    project_dir="../escape",
                )
            private_file = ws.state_dir / "local_state.toml"
            self.assertFalse(private_file.exists())
            parsed = tomllib.loads(
                (root / "projects" / "repo" / "project.toml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(parsed["identity"]["project_id"], reg.project_id)

    def test_unset_does_not_create_files_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            ws = workspace.resolve_meta_workspace(cwd=root)
            result = workspace.unset_project_fields_in_workspace(
                ws, selector="demo", local_repo_path=True
            )
            self.assertEqual(result.binding_paths, ())
            self.assertFalse((ws.state_dir / "local_state.toml").exists())
            self.assertFalse(
                (ws.catalog_root / ".lrh" / "trusted_local_state.toml").exists()
            )


class TestMetaSetUnsetCli(unittest.TestCase):
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
            cwd=cwd,
            env=env,
        )

    def test_set_rejects_unknown_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root, spec=workspace.MetaWorkspaceSpec(workspace_name="Demo")
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo), short_name="demo"
                ),
            )
            result = self._run_lrh(
                ["meta", "set", "demo", "--display-name", "X", "--bogus", "x"],
                root,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unrecognized arguments", result.stderr)
