import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from lrh.meta import workspace


def _canonical(path: pathlib.Path) -> pathlib.Path:
    return path.resolve()


class TestMetaWhereCli(unittest.TestCase):
    def _run_lrh(
        self,
        args: list[str],
        *,
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
            cwd=cwd,
            env=env,
        )

    def test_meta_where_reports_global_workspace(self) -> None:
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
            workspace.init_global_workspace(
                spec=workspace.MetaWorkspaceSpec(workspace_name="Global"),
                environ=env,
            )

            result = self._run_lrh(["meta", "where"], cwd=root, env_overrides=env)

            self.assertEqual(result.returncode, 0)
            self.assertIn("Active LRH meta workspace", result.stdout)
            self.assertIn("mode: global", result.stdout)
            self.assertIn("resolution source: global_discovery", result.stdout)
            self.assertIn(
                f"projects: {_canonical(xdg_state / 'lrh' / 'projects')}",
                result.stdout,
            )
            self.assertNotIn("workspace root:", result.stdout)

    def test_meta_where_reports_local_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Local"),
            )
            nested = workspace_root / "nested" / "dir"
            nested.mkdir(parents=True)

            result = self._run_lrh(["meta", "where"], cwd=nested)

            self.assertEqual(result.returncode, 0)
            self.assertIn("mode: local", result.stdout)
            self.assertIn("resolution source: local_discovery", result.stdout)
            self.assertIn(
                f"workspace root: {_canonical(workspace_root)}",
                result.stdout,
            )
            self.assertIn(
                f"config: {_canonical(workspace_root / '.lrh' / 'config.toml')}",
                result.stdout,
            )

    def test_meta_where_workspace_flag_reports_hybrid_workspace_mode(self) -> None:
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
            workspace.init_hybrid_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Hybrid"),
                environ=env,
            )

            result = self._run_lrh(
                ["meta", "where", "--workspace", str(workspace_root)],
                cwd=root,
                env_overrides=env,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("mode: hybrid", result.stdout)
            self.assertIn("resolution source: flag(--workspace)", result.stdout)
            self.assertIn(
                f"catalog root: {_canonical(workspace_root)}",
                result.stdout,
            )

    def test_meta_where_json_contains_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Local"),
            )

            result = self._run_lrh(["meta", "where", "--json"], cwd=workspace_root)

            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertEqual(data["mode"], "local")
            self.assertEqual(data["resolution_source"], "local_discovery")
            self.assertEqual(
                data["config_path"],
                str(_canonical(workspace_root / ".lrh" / "config.toml")),
            )
            self.assertEqual(
                data["projects_dir"], str(_canonical(workspace_root / "projects"))
            )
            self.assertEqual(
                data["state_dir"],
                str(_canonical(workspace_root / "private" / "state")),
            )
            self.assertEqual(
                data["cache_dir"],
                str(_canonical(workspace_root / "private" / "cache")),
            )
            self.assertEqual(data["workspace_root"], str(_canonical(workspace_root)))

    def test_meta_where_failure_message_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            env = {
                "XDG_CONFIG_HOME": str(root / "cfg"),
                "XDG_STATE_HOME": str(root / "state"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "LRH_CONFIG": "",
                "LRH_WORKSPACE": "",
            }

            result = self._run_lrh(["meta", "where"], cwd=root, env_overrides=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No LRH meta workspace could be resolved", result.stdout)
            self.assertIn("--config / --workspace / --mode", result.stdout)
            self.assertIn("lrh meta init --mode global", result.stdout)
            self.assertIn("lrh meta init --mode local", result.stdout)

    def test_meta_where_does_not_mutate_workspace_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Local"),
            )
            tracked_paths = [
                workspace_root / ".lrh" / "config.toml",
                workspace_root / "projects",
                workspace_root / "private" / "state",
                workspace_root / "private" / "cache",
            ]
            before = {path: path.stat().st_mtime_ns for path in tracked_paths}

            result = self._run_lrh(["meta", "where"], cwd=workspace_root)

            self.assertEqual(result.returncode, 0)
            after = {path: path.stat().st_mtime_ns for path in tracked_paths}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
