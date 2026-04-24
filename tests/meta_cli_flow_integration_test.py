import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest


def _canonical(path: pathlib.Path) -> pathlib.Path:
    return path.resolve()


class TestMetaCliFlowIntegration(unittest.TestCase):
    def _isolated_env(self, root: pathlib.Path) -> dict[str, str]:
        env = os.environ.copy()
        src_path = pathlib.Path("src").resolve()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_path) if not existing else f"{src_path}{os.pathsep}{existing}"
        )

        fake_home = root / "fake-home"
        xdg_config_home = root / "xdg" / "config"
        xdg_state_home = root / "xdg" / "state"
        xdg_cache_home = root / "xdg" / "cache"

        for path in (fake_home, xdg_config_home, xdg_state_home, xdg_cache_home):
            path.mkdir(parents=True, exist_ok=True)

        env["HOME"] = str(fake_home)
        env["XDG_CONFIG_HOME"] = str(xdg_config_home)
        env["XDG_STATE_HOME"] = str(xdg_state_home)
        env["XDG_CACHE_HOME"] = str(xdg_cache_home)

        env.pop("LRH_CONFIG", None)
        env.pop("LRH_WORKSPACE", None)
        return env

    def _run_lrh(
        self,
        args: list[str],
        *,
        cwd: pathlib.Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
        )

    def test_meta_command_flow_across_workspace_modes(self) -> None:
        modes = ("local", "global", "hybrid")
        for mode in modes:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    root = pathlib.Path(tmp_dir)
                    env = self._isolated_env(root)

                    workspace_root = root / "workspace"
                    workspace_root.mkdir(parents=True)

                    fake_repo = root / "fake-repo"
                    (fake_repo / "project").mkdir(parents=True)

                    if mode == "global":
                        init_args = ["meta", "init", "--mode", "global"]
                        command_cwd = root
                    else:
                        init_args = [
                            "meta",
                            "init",
                            "--mode",
                            mode,
                            str(workspace_root),
                        ]
                        command_cwd = workspace_root

                    init_result = self._run_lrh(init_args, cwd=root, env=env)
                    self.assertEqual(init_result.returncode, 0, msg=init_result.stderr)

                    first_list = self._run_lrh(["meta", "list"], cwd=command_cwd, env=env)
                    self.assertEqual(first_list.returncode, 0, msg=first_list.stderr)
                    self.assertIn("No registered projects", first_list.stdout)

                    register_result = self._run_lrh(
                        ["meta", "register", str(fake_repo)],
                        cwd=command_cwd,
                        env=env,
                    )
                    self.assertEqual(
                        register_result.returncode,
                        0,
                        msg=register_result.stderr,
                    )
                    project_id_match = re.search(
                        r"^project_id=(proj-[a-f0-9]{16})$",
                        register_result.stdout,
                        flags=re.MULTILINE,
                    )
                    self.assertIsNotNone(project_id_match)
                    project_id = project_id_match.group(1)
                    self.assertIn("setup_state=lrh_project_present", register_result.stdout)

                    second_list = self._run_lrh(
                        ["meta", "list"],
                        cwd=command_cwd,
                        env=env,
                    )
                    self.assertEqual(second_list.returncode, 0, msg=second_list.stderr)
                    self.assertIn("[1] fake-repo", second_list.stdout)
                    self.assertIn(f"project_id: {project_id}", second_list.stdout)
                    self.assertIn("setup_state: lrh_project_present", second_list.stdout)

                    fake_xdg_config = _canonical(root / "xdg" / "config" / "lrh")
                    fake_xdg_state = _canonical(root / "xdg" / "state" / "lrh")
                    fake_xdg_cache = _canonical(root / "xdg" / "cache" / "lrh")

                    if mode == "global":
                        expected_projects_dir = fake_xdg_state / "projects"
                        self.assertTrue((fake_xdg_config / "config.toml").exists())
                        self.assertTrue((fake_xdg_state / "private" / "state").exists())
                        self.assertTrue((fake_xdg_cache / "cache").exists())
                    elif mode == "local":
                        expected_projects_dir = _canonical(workspace_root / "projects")
                        self.assertTrue((workspace_root / ".lrh" / "config.toml").exists())
                        self.assertTrue((workspace_root / "private" / "state").exists())
                        self.assertTrue((workspace_root / "private" / "cache").exists())
                        self.assertFalse((fake_xdg_config / "config.toml").exists())
                    else:
                        expected_projects_dir = _canonical(workspace_root / "projects")
                        self.assertTrue((workspace_root / ".lrh" / "config.toml").exists())
                        self.assertTrue((fake_xdg_config / "config.toml").exists())
                        self.assertTrue((fake_xdg_state / "private" / "state").exists())
                        self.assertTrue((fake_xdg_cache / "cache").exists())
                        self.assertFalse((workspace_root / "private").exists())

                    record_path = expected_projects_dir / "fake-repo" / "project.toml"
                    self.assertTrue(record_path.exists())

                    parsed = tomllib.loads(record_path.read_text(encoding="utf-8"))
                    self.assertEqual(parsed["identity"]["project_id"], project_id)
                    self.assertEqual(parsed["project"]["setup_state"], "lrh_project_present")

                    for checked_path in (
                        record_path,
                        expected_projects_dir,
                        fake_xdg_config,
                        fake_xdg_state,
                        fake_xdg_cache,
                    ):
                        self.assertTrue(_canonical(checked_path).is_relative_to(root))


if __name__ == "__main__":
    unittest.main()
