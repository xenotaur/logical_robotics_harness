import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from lrh.meta import workspace


class TestMetaInspectRuntime(unittest.TestCase):
    def test_inspect_registered_project_by_short_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "demo-repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo),
                    short_name="demo",
                ),
            )

            local_workspace = workspace.resolve_meta_workspace(cwd=root)
            inspect_result = workspace.inspect_registered_project_in_workspace(
                local_workspace,
                selector="demo",
            )
            output = workspace.format_project_inspect(inspect_result)

            self.assertIn("Workspace:", output)
            self.assertIn("mode: local", output)
            self.assertIn("Project Record:", output)
            self.assertIn("short_name: demo", output)
            self.assertIn(f"repo_locator: {repo}", output)
            self.assertIn("project_dir: project", output)
            self.assertIn("Derived:", output)
            self.assertIn("repo_path_exists: true", output)
            self.assertIn("project_path_exists: true", output)

    def test_inspect_project_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            local_workspace = workspace.resolve_meta_workspace(cwd=root)
            with self.assertRaises(workspace.MetaRegistryError) as err_ctx:
                workspace.inspect_registered_project_in_workspace(
                    local_workspace,
                    selector="missing",
                )

            self.assertIn(
                "no registered project matched selector",
                str(err_ctx.exception),
            )

    def test_inspect_project_reports_missing_resolved_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "ghost-repo"
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo),
                    short_name="ghost",
                ),
            )

            local_workspace = workspace.resolve_meta_workspace(cwd=root)
            inspect_result = workspace.inspect_registered_project_in_workspace(
                local_workspace,
                selector="ghost",
            )
            output = workspace.format_project_inspect(inspect_result)

            self.assertIn("repo_path_exists: false", output)
            self.assertIn("project_path_exists: false", output)


class TestMetaInspectCli(unittest.TestCase):
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

    def test_lrh_meta_inspect_cli_renders_record_and_workspace_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "demo-repo"
            (repo / "project").mkdir(parents=True)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )
            workspace.register_project(
                root,
                spec=workspace.MetaRegisterSpec(
                    repo_locator=str(repo),
                    short_name="demo",
                ),
            )

            result = self._run_lrh(["meta", "inspect", "demo"], root)

            self.assertEqual(result.returncode, 0)
            self.assertIn("Workspace:", result.stdout)
            self.assertIn("resolution_source: local_discovery", result.stdout)
            self.assertIn("Project Record:", result.stdout)
            self.assertIn("short_name: demo", result.stdout)
            self.assertIn("Derived:", result.stdout)

    def test_lrh_meta_inspect_cli_project_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )

            result = self._run_lrh(["meta", "inspect", "missing"], root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "error: no registered project matched selector",
                result.stdout,
            )

    def test_lrh_meta_inspect_cli_fails_for_malformed_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )
            record_dir = root / "projects" / "broken"
            record_dir.mkdir(parents=True)
            (record_dir / "project.toml").write_text("[project\n", encoding="utf-8")

            result = self._run_lrh(["meta", "inspect", "broken"], root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("error: invalid TOML", result.stdout)


if __name__ == "__main__":
    unittest.main()
