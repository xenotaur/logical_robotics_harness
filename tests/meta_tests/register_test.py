import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest

from lrh.meta import workspace


class TestMetaRegisterRuntime(unittest.TestCase):
    def test_register_project_writes_record_with_stable_project_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "client-repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(repo_locator=str(repo)),
            )

            self.assertTrue(result.record_path.exists())
            record = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["locators"]["repo_locator"], str(repo))
            self.assertEqual(record["locators"]["project_dir"], "project")
            self.assertEqual(record["project"]["setup_state"], "lrh_project_present")
            self.assertTrue(record["identity"]["project_id"].startswith("proj-"))

            second = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo),
                    directory_name="client-repo-duplicate",
                ),
                force=True,
            )
            second_record = tomllib.loads(
                second.record_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                second_record["identity"]["project_id"],
                record["identity"]["project_id"],
            )

    def test_register_project_duplicate_detected_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "client-repo"
            repo.mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(repo_locator=str(repo)),
            )

            with self.assertRaises(workspace.MetaRegistryError):
                workspace.register_project(
                    root,
                    spec=workspace.MetaRegisterSpec(
                        repo_locator=str(repo),
                        directory_name="another",
                    ),
                )

    def test_register_project_detects_setup_state_not_set_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "plain-repo"
            repo.mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(repo_locator=str(repo)),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["project"]["setup_state"], "not_set_up")

    def test_register_project_accepts_metadata_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "acme-repo"
            repo.mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo),
                    project_dir="custom_project",
                    directory_name="acme",
                    short_name="ac",
                    display_name="Acme Program",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["project"]["short_name"], "ac")
            self.assertEqual(parsed["project"]["display_name"], "Acme Program")
            self.assertEqual(parsed["locators"]["project_dir"], "custom_project")

    def test_register_project_infers_repo_identity_for_github_tree_project(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=(
                        "https://github.com/xenotaur/logical_robotics_harness/"
                        "tree/main/project"
                    ),
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(result.directory_name, "logical_robotics_harness")
            self.assertEqual(
                parsed["project"]["short_name"],
                "logical_robotics_harness",
            )
            self.assertEqual(
                parsed["project"]["display_name"],
                "Logical Robotics Harness",
            )
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/xenotaur/logical_robotics_harness/tree/main",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "project")

    def test_register_project_normalizes_github_tree_locator_with_project_subpath(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://github.com/xenotaur/taurworks/tree/master/project",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["registry"]["directory_name"], "taurworks")
            self.assertEqual(parsed["project"]["short_name"], "taurworks")
            self.assertEqual(parsed["project"]["display_name"], "Taurworks")
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/xenotaur/taurworks/tree/master",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "project")

    def test_register_project_normalization_preserves_query_and_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=(
                        "https://github.com/xenotaur/taurworks/tree/master/project"
                        "?tab=readme#overview"
                    ),
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/xenotaur/taurworks/tree/master?tab=readme#overview",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "project")

    def test_register_project_github_tree_urls_do_not_collapse_to_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            first = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=(
                        "https://github.com/xenotaur/logical_robotics_harness/"
                        "tree/main/project"
                    ),
                ),
            )
            second = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://github.com/xenotaur/taurworks/tree/master/project",
                ),
            )

            self.assertNotEqual(first.directory_name, "project")
            self.assertNotEqual(second.directory_name, "project")
            self.assertNotEqual(first.directory_name, second.directory_name)
            self.assertTrue((root / "projects" / first.directory_name).exists())
            self.assertTrue((root / "projects" / second.directory_name).exists())

    def test_register_project_infers_project_dir_from_github_tree_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://github.com/example/widgets/tree/main/docs/project",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/example/widgets/tree/main",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "docs/project")
            self.assertEqual(parsed["project"]["short_name"], "widgets")

    def test_register_project_generic_url_uses_conservative_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://example.com/project",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(result.directory_name, "project")
            self.assertEqual(parsed["project"]["short_name"], "project")
            self.assertEqual(parsed["project"]["display_name"], "Project")
            self.assertEqual(parsed["project"]["setup_state"], "not_checked")

    def test_register_project_github_tree_locator_uses_not_checked_setup_state(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://github.com/xenotaur/taurworks/tree/master",
                    project_dir="project",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/xenotaur/taurworks/tree/master",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "project")
            self.assertEqual(parsed["project"]["setup_state"], "not_checked")

    def test_register_project_github_overrides_are_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            result = workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator="https://github.com/example/acme/tree/main/project",
                    project_dir="custom_dir",
                    directory_name="override-dir",
                    short_name="override-short",
                    display_name="Override Display",
                ),
            )

            parsed = tomllib.loads(result.record_path.read_text(encoding="utf-8"))
            self.assertEqual(result.directory_name, "override-dir")
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/example/acme/tree/main/project",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "custom_dir")
            self.assertEqual(parsed["project"]["short_name"], "override-short")
            self.assertEqual(parsed["project"]["display_name"], "Override Display")


class TestMetaRegisterCli(unittest.TestCase):
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

    def test_lrh_meta_register_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "demo-repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )

            result = self._run_lrh(["meta", "register", str(repo)], root)

            self.assertEqual(result.returncode, 0)
            self.assertIn("Registered project", result.stdout)
            self.assertIn("setup_state=lrh_project_present", result.stdout)
            self.assertTrue((root / "projects" / "demo-repo" / "project.toml").exists())

    def test_lrh_meta_register_cli_normalizes_github_tree_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )

            result = self._run_lrh(
                [
                    "meta",
                    "register",
                    "https://github.com/xenotaur/taurworks/tree/master/project",
                ],
                root,
            )

            self.assertEqual(result.returncode, 0)
            record_path = root / "projects" / "taurworks" / "project.toml"
            parsed = tomllib.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["locators"]["repo_locator"],
                "https://github.com/xenotaur/taurworks/tree/master",
            )
            self.assertEqual(parsed["locators"]["project_dir"], "project")

    def test_lrh_meta_register_cli_duplicate_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "dup-repo"
            repo.mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )

            first = self._run_lrh(["meta", "register", str(repo)], root)
            second = self._run_lrh(
                [
                    "meta",
                    "register",
                    str(repo),
                    "--directory-name",
                    "dup-repo-copy",
                ],
                root,
            )
            forced = self._run_lrh(
                [
                    "meta",
                    "register",
                    str(repo),
                    "--directory-name",
                    "dup-repo-copy",
                    "--force",
                ],
                root,
            )

            self.assertEqual(first.returncode, 0)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("duplicate registration detected", second.stdout)
            self.assertEqual(forced.returncode, 0)


if __name__ == "__main__":
    unittest.main()
