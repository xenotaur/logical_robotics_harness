import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lrh.meta import workspace


class TestMetaListRuntime(unittest.TestCase):
    def test_list_registered_projects_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )

            records = workspace.list_registered_projects(root)

            self.assertEqual(records, ())
            output = workspace.format_project_records(records)
            self.assertIn("No registered projects", output)

    def test_list_registered_projects_multiple_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            self._write_project_record(
                root,
                registry_name="alpha",
                short_name="alpha",
                display_name="Alpha Project",
                project_id="proj-alpha-001",
                repo_locator="https://github.com/example/alpha.git",
                project_dir="project",
                setup_state="lrh_project_present",
            )
            self._write_project_record(
                root,
                registry_name="beta",
                short_name="beta",
                display_name="Beta Project",
                project_id="proj-beta-001",
                repo_locator="https://github.com/example/beta.git",
                project_dir=".",
                setup_state="not_set_up",
            )

            records = workspace.list_registered_projects(root)

            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].registry_name, "alpha")
            self.assertEqual(records[1].registry_name, "beta")

            output = workspace.format_project_records(records)
            self.assertIn("short_name: alpha", output)
            self.assertIn("display_name: Beta Project", output)
            self.assertIn("project_id: proj-alpha-001", output)
            self.assertIn("repo_locator: https://github.com/example/beta.git", output)
            self.assertIn("project_dir: .", output)
            self.assertIn("setup_state: not_set_up", output)

    def test_list_registered_projects_with_missing_fields_shows_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            self._write_project_record(
                root,
                registry_name="gamma",
                short_name="",
                display_name="",
                project_id="",
                repo_locator="",
                project_dir="",
                setup_state="",
            )

            records = workspace.list_registered_projects(root)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].short_name, "")
            output = workspace.format_project_records(records)
            self.assertIn("short_name: ", output)
            self.assertIn("setup_state: ", output)

    def test_list_registered_projects_fails_for_malformed_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            record_dir = root / "projects" / "broken"
            record_dir.mkdir(parents=True)
            (record_dir / "project.toml").write_text("[project\n", encoding="utf-8")

            with self.assertRaises(workspace.MetaRegistryError):
                workspace.list_registered_projects(root)

    def test_list_registered_projects_fails_for_non_utf8_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            record_dir = root / "projects" / "binary"
            record_dir.mkdir(parents=True)
            (record_dir / "project.toml").write_bytes(b"\xff\xfe\x00\x00")

            with self.assertRaises(workspace.MetaRegistryError) as err_ctx:
                workspace.list_registered_projects(root)

            self.assertIn("not valid UTF-8", str(err_ctx.exception))

    def test_list_registered_projects_fails_for_read_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Demo Workspace"),
            )
            self._write_project_record(
                root,
                registry_name="read-error",
                short_name="demo",
                display_name="Demo Project",
                project_id="proj-demo-001",
                repo_locator="https://github.com/example/demo.git",
                project_dir="project",
                setup_state="lrh_project_present",
            )

            with mock.patch.object(
                pathlib.Path,
                "read_text",
                side_effect=OSError("permission denied"),
            ):
                with self.assertRaises(workspace.MetaRegistryError) as err_ctx:
                    workspace.list_registered_projects(root)

            self.assertIn("unable to read project record file", str(err_ctx.exception))

    def _write_project_record(
        self,
        root: pathlib.Path,
        *,
        registry_name: str,
        short_name: str,
        display_name: str,
        project_id: str,
        repo_locator: str,
        project_dir: str,
        setup_state: str,
    ) -> None:
        record_dir = root / "projects" / registry_name
        record_dir.mkdir(parents=True, exist_ok=True)
        (record_dir / "project.toml").write_text(
            "\n".join(
                [
                    'schema_version = "0.1"',
                    "",
                    "[project]",
                    f'short_name = "{short_name}"',
                    f'display_name = "{display_name}"',
                    f'setup_state = "{setup_state}"',
                    "",
                    "[identity]",
                    f'project_id = "{project_id}"',
                    "",
                    "[locators]",
                    f'repo_locator = "{repo_locator}"',
                    f'project_dir = "{project_dir}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )


class TestMetaListCli(unittest.TestCase):
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

    def test_lrh_meta_list_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="CLI Workspace"),
            )
            record_dir = root / "projects" / "demo"
            record_dir.mkdir(parents=True)
            (record_dir / "project.toml").write_text(
                "\n".join(
                    [
                        'schema_version = "0.1"',
                        "",
                        "[project]",
                        'short_name = "demo"',
                        'display_name = "Demo Project"',
                        'setup_state = "lrh_project_present"',
                        "",
                        "[identity]",
                        'project_id = "proj-demo-001"',
                        "",
                        "[locators]",
                        'repo_locator = "https://example.com/demo.git"',
                        'project_dir = "project"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self._run_lrh(["meta", "list"], root)

            self.assertEqual(result.returncode, 0)
            self.assertIn("[1] demo", result.stdout)
            self.assertIn("project_id: proj-demo-001", result.stdout)


if __name__ == "__main__":
    unittest.main()
