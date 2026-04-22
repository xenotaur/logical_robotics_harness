import pathlib
import tempfile
import tomllib
import unittest

from lrh.meta import workspace


class TestMetaRegisterRuntime(unittest.TestCase):
    def test_register_project_creates_record_for_lrh_repository(self) -> None:
        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as repo_dir,
        ):
            workspace_root = pathlib.Path(workspace_dir)
            repo_root = pathlib.Path(repo_dir)
            (repo_root / "project").mkdir()
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                workspace_root,
                repo_locator=str(repo_root),
            )

            self.assertFalse(result.existed)
            self.assertTrue(result.record_path.exists())
            data = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(data["project"]["project_id"], result.project_id)
            self.assertEqual(data["project"]["setup_state"], "lrh_project_present")
            self.assertEqual(data["locator"]["repo"], str(repo_root.resolve()))
            self.assertEqual(
                data["identity"]["canonical_url"], repo_root.resolve().as_uri()
            )

    def test_register_project_detects_non_lrh_setup_state(self) -> None:
        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as repo_dir,
        ):
            workspace_root = pathlib.Path(workspace_dir)
            repo_root = pathlib.Path(repo_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                workspace_root,
                repo_locator=str(repo_root),
            )

            data = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(data["project"]["setup_state"], "not_set_up")
            self.assertTrue(result.project_id.startswith("proj-"))

    def test_register_project_requires_initialized_workspace(self) -> None:
        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as repo_dir,
        ):
            with self.assertRaises(workspace.MetaRegisterError):
                workspace.register_project(
                    pathlib.Path(workspace_dir),
                    repo_locator=repo_dir,
                )

    def test_register_project_rejects_duplicate_without_force(self) -> None:
        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as repo_dir,
        ):
            workspace_root = pathlib.Path(workspace_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            workspace.register_project(workspace_root, repo_locator=repo_dir)

            with self.assertRaises(workspace.MetaRegisterError):
                workspace.register_project(workspace_root, repo_locator=repo_dir)

    def test_register_project_force_updates_existing_record(self) -> None:
        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as repo_dir,
        ):
            workspace_root = pathlib.Path(workspace_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            initial = workspace.register_project(workspace_root, repo_locator=repo_dir)

            updated = workspace.register_project(
                workspace_root, repo_locator=repo_dir, force=True
            )
            self.assertTrue(updated.existed)
            self.assertEqual(updated.project_id, initial.project_id)
            self.assertEqual(updated.record_path, initial.record_path)


if __name__ == "__main__":
    unittest.main()
