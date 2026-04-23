import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from lrh.meta import workspace


def _canonical(path: pathlib.Path) -> pathlib.Path:
    return path.resolve()


class TestMetaWorkspaceResolution(unittest.TestCase):
    def test_flags_override_environment_and_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            first = root / "first"
            second = root / "second"
            workspace.init_workspace(
                first,
                spec=workspace.MetaWorkspaceSpec(workspace_name="First"),
            )
            workspace.init_workspace(
                second,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Second"),
            )

            env = {"LRH_WORKSPACE": str(first)}
            resolved = workspace.resolve_meta_workspace(
                cwd=second,
                options=workspace.MetaWorkspaceResolveOptions(workspace_path=second),
                environ=env,
            )

            self.assertEqual(resolved.workspace_root, _canonical(second))
            self.assertEqual(resolved.resolution_source, "flag(--workspace)")

    def test_lrh_config_is_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            config_home = root / "cfg"
            state_home = root / "state"
            cache_home = root / "cache"
            config_path = config_home / "lrh" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        'schema_version = "0.1"',
                        "",
                        "[workspace]",
                        'mode = "global"',
                        "",
                        "[paths]",
                        'projects_dir = "../state/lrh/projects"',
                        'state_dir = "../state/lrh"',
                        'cache_dir = "../cache/lrh"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "LRH_CONFIG": str(config_path),
                "XDG_STATE_HOME": str(state_home),
                "XDG_CACHE_HOME": str(cache_home),
            }

            resolved = workspace.resolve_meta_workspace(cwd=root, environ=env)

            self.assertEqual(resolved.mode, "global")
            self.assertEqual(resolved.config_path, _canonical(config_path))
            self.assertEqual(resolved.resolution_source, "env(LRH_CONFIG)")

    def test_lrh_workspace_is_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            local_workspace_root = root / "local"
            workspace.init_workspace(
                local_workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Local"),
            )

            resolved = workspace.resolve_meta_workspace(
                cwd=root,
                environ={"LRH_WORKSPACE": str(local_workspace_root)},
            )
            self.assertEqual(resolved.workspace_root, _canonical(local_workspace_root))
            self.assertEqual(resolved.resolution_source, "env(LRH_WORKSPACE)")

    def test_local_workspace_discovery_from_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace_root = root / "ws"
            nested = workspace_root / "a" / "b" / "c"
            nested.mkdir(parents=True)
            workspace.init_workspace(
                workspace_root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Nested"),
            )

            resolved = workspace.resolve_meta_workspace(cwd=nested, environ={})
            self.assertEqual(resolved.workspace_root, _canonical(workspace_root))
            self.assertEqual(resolved.resolution_source, "local_discovery")

    def test_global_xdg_defaults_are_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            config_path = xdg_config / "lrh" / "config.toml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        'schema_version = "0.1"',
                        "",
                        "[workspace]",
                        'mode = "global"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
            }

            resolved = workspace.resolve_meta_workspace(cwd=root, environ=env)

            self.assertEqual(resolved.mode, "global")
            self.assertEqual(resolved.config_path, _canonical(config_path))
            self.assertEqual(resolved.projects_dir, _canonical(xdg_state / "lrh" / "projects"))
            self.assertEqual(resolved.state_dir, _canonical(xdg_state / "lrh"))
            self.assertEqual(resolved.cache_dir, _canonical(xdg_cache / "lrh"))

    def test_mode_global_uses_defaults_without_config_file(self) -> None:
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

            resolved = workspace.resolve_meta_workspace(
                cwd=root,
                options=workspace.MetaWorkspaceResolveOptions(mode="global"),
                environ=env,
            )

            self.assertEqual(resolved.mode, "global")
            self.assertEqual(
                resolved.config_path,
                _canonical(xdg_config / "lrh" / "config.toml"),
            )
            self.assertEqual(resolved.projects_dir, _canonical(xdg_state / "lrh" / "projects"))
            self.assertEqual(resolved.state_dir, _canonical(xdg_state / "lrh"))
            self.assertEqual(resolved.cache_dir, _canonical(xdg_cache / "lrh"))
            self.assertEqual(
                resolved.resolution_source,
                "flag(--mode=global)+built_in_defaults",
            )


class TestMetaWorkspaceResolutionCliIntegration(unittest.TestCase):
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

    def test_meta_register_uses_global_workspace_when_not_in_workspace_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            repo = root / "demo-repo"
            (repo / "project").mkdir(parents=True)

            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            config_path = xdg_config / "lrh" / "config.toml"
            config_path.parent.mkdir(parents=True)
            (xdg_state / "lrh" / "projects").mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        'schema_version = "0.1"',
                        "",
                        "[workspace]",
                        'mode = "global"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
            }

            register_result = self._run_lrh(
                ["meta", "register", str(repo)],
                cwd=repo,
                env_overrides=env,
            )
            self.assertEqual(register_result.returncode, 0)

            list_result = self._run_lrh(["meta", "list"], cwd=repo, env_overrides=env)
            self.assertEqual(list_result.returncode, 0)
            self.assertIn("[1] demo-repo", list_result.stdout)

    def test_meta_list_shows_resolution_error_without_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            xdg_config = root / "xdg-config"
            xdg_state = root / "xdg-state"
            xdg_cache = root / "xdg-cache"
            env = {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_STATE_HOME": str(xdg_state),
                "XDG_CACHE_HOME": str(xdg_cache),
                "LRH_CONFIG": "",
                "LRH_WORKSPACE": "",
            }

            result = self._run_lrh(["meta", "list"], cwd=root, env_overrides=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No LRH meta workspace could be resolved", result.stdout)
            self.assertIn("lrh meta init --mode local", result.stdout)

    def test_meta_list_missing_local_projects_dir_suggests_mode_local_init(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            workspace.init_workspace(
                root,
                spec=workspace.MetaWorkspaceSpec(workspace_name="Local"),
            )
            (root / "projects").rmdir()

            result = self._run_lrh(["meta", "list"], cwd=root, env_overrides={})

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing projects directory", result.stdout)
            self.assertIn("lrh meta init --mode local", result.stdout)


if __name__ == "__main__":
    unittest.main()
