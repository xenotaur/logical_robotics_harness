import os
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest


class CondaWorktreeEnvScriptTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _script_path(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "conda-worktree-env"

    def _write_fake_conda(
        self,
        temp_dir: pathlib.Path,
        log_path: pathlib.Path,
        env_list_lines: list[str],
        pip_show_exit_code: int,
        create_exit_code: int,
    ) -> pathlib.Path:
        fake_conda = temp_dir / "conda"
        env_list_output = "\n".join(env_list_lines) + "\n" if env_list_lines else ""
        fake_conda.write_text(
            textwrap.dedent(f"""\
                #!/bin/bash
                echo "$@" >> {log_path}
                if [[ "$1" == "env" && "$2" == "list" ]]; then
                  cat <<'ENVLIST'
                {env_list_output}ENVLIST
                  exit 0
                fi
                if [[ "$1" == "create" ]]; then
                  exit {create_exit_code}
                fi
                if [[ "$1" == "run" ]]; then
                  for arg in "$@"; do
                    if [[ "$arg" == "show" ]]; then
                      exit {pip_show_exit_code}
                    fi
                  done
                fi
                exit 0
                """),
            encoding="utf-8",
        )
        fake_conda.chmod(fake_conda.stat().st_mode | stat.S_IXUSR)
        return fake_conda

    def _run(
        self,
        args: list[str],
        env_list_lines: list[str],
        pip_show_exit_code: int = 1,
        create_exit_code: int = 0,
    ) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
        # pip_show_exit_code defaults to 1 (not installed), matching the
        # common real-world case: `pip show -q <pkg>` exits nonzero when
        # the package isn't present, which is what the script's stale-
        # editable-install check should usually observe.
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = pathlib.Path(temp_dir_str)
            log_path = temp_dir / "conda.log"
            log_path.write_text("", encoding="utf-8")
            self._write_fake_conda(
                temp_dir=temp_dir,
                log_path=log_path,
                env_list_lines=env_list_lines,
                pip_show_exit_code=pip_show_exit_code,
                create_exit_code=create_exit_code,
            )
            env = os.environ.copy()
            env["PATH"] = f"{temp_dir}:{env['PATH']}"

            result = subprocess.run(
                [str(self._script_path()), *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=self._repo_root(),
                env=env,
            )
            log_lines = (
                log_path.read_text(encoding="utf-8").splitlines()
                if log_path.exists()
                else []
            )
            return result, log_lines

    def test_new_env_name_creates_then_installs(self) -> None:
        # Default pip_show_exit_code=1: no stale 'logical-robotics-harness'
        # install present, so the uninstall itself must NOT run -- only the
        # existence check and scripts/develop.
        result, log_lines = self._run(
            ["LrhTestEnvNew"],
            env_list_lines=["# conda environments:", "#", "base   *  /opt/conda"],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        create_lines = [line for line in log_lines if line.startswith("create ")]
        remove_lines = [line for line in log_lines if line.startswith("env remove")]
        run_lines = [line for line in log_lines if line.startswith("run ")]

        self.assertEqual(len(create_lines), 1)
        self.assertEqual(len(remove_lines), 0)
        self.assertIn("-n LrhTestEnvNew", create_lines[0])
        self.assertIn("python=3.11", create_lines[0])
        # The stale-package existence check and scripts/develop go through
        # `conda run` -- assert both happened, in order, after create; no
        # uninstall since the fake package show reports it isn't installed.
        self.assertEqual(len(run_lines), 2)
        self.assertIn("-n LrhTestEnvNew", run_lines[0])
        self.assertIn("pip show", run_lines[0])
        self.assertIn("logical-robotics-harness", run_lines[0])
        self.assertNotIn("pip uninstall", " ".join(run_lines))
        self.assertIn("-n LrhTestEnvNew", run_lines[1])
        self.assertIn("scripts/develop", run_lines[1])
        create_index = log_lines.index(create_lines[0])
        run_indices = [log_lines.index(line) for line in run_lines]
        self.assertTrue(all(idx > create_index for idx in run_indices))

    def test_stale_install_present_gets_uninstalled(self) -> None:
        result, log_lines = self._run(
            ["LrhTestEnvStale"],
            env_list_lines=["# conda environments:", "#", "base   *  /opt/conda"],
            pip_show_exit_code=0,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        run_lines = [line for line in log_lines if line.startswith("run ")]

        self.assertEqual(len(run_lines), 3)
        self.assertIn("pip show", run_lines[0])
        self.assertIn("pip uninstall", run_lines[1])
        self.assertIn("logical-robotics-harness", run_lines[1])
        self.assertIn("scripts/develop", run_lines[2])

    def test_existing_env_name_reuses_without_create_or_remove(self) -> None:
        result, log_lines = self._run(
            ["LrhTestEnvExisting"],
            env_list_lines=["LrhTestEnvExisting   /opt/conda/envs/LrhTestEnvExisting"],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(
            "Reusing existing environment 'LrhTestEnvExisting'.", result.stdout
        )
        create_lines = [line for line in log_lines if line.startswith("create ")]
        remove_lines = [line for line in log_lines if line.startswith("env remove")]
        run_lines = [line for line in log_lines if line.startswith("run ")]

        self.assertEqual(len(create_lines), 0)
        self.assertEqual(len(remove_lines), 0)
        self.assertEqual(len(run_lines), 2)
        self.assertIn("pip show", run_lines[0])
        self.assertIn("scripts/develop", run_lines[1])

    def test_recreate_removes_before_creating(self) -> None:
        result, log_lines = self._run(
            ["LrhTestEnvRecreate", "--recreate"],
            env_list_lines=["LrhTestEnvRecreate   /opt/conda/envs/LrhTestEnvRecreate"],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        remove_lines = [line for line in log_lines if line.startswith("env remove")]
        create_lines = [line for line in log_lines if line.startswith("create ")]

        self.assertEqual(len(remove_lines), 1)
        self.assertEqual(len(create_lines), 1)
        self.assertIn("-n LrhTestEnvRecreate", remove_lines[0])
        self.assertLess(
            log_lines.index(remove_lines[0]),
            log_lines.index(create_lines[0]),
            msg="--recreate must remove the existing environment before creating it",
        )

    def test_env_name_with_regex_metacharacters_is_matched_literally(self) -> None:
        # Regression test: an environment literally named "fooXbar" must not
        # be treated as satisfying a request for "foo.bar", even though
        # "foo.bar" is a valid basic-regex pattern matching "fooXbar".
        result, log_lines = self._run(
            ["foo.bar"],
            env_list_lines=["fooXbar   /opt/conda/envs/fooXbar"],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        create_lines = [line for line in log_lines if line.startswith("create ")]
        self.assertEqual(
            len(create_lines),
            1,
            msg="foo.bar must be created fresh, not mistaken for the unrelated fooXbar",
        )
        self.assertIn("-n foo.bar", create_lines[0])

    def test_python_flag_rejects_option_like_value(self) -> None:
        result, log_lines = self._run(
            ["LrhTestEnvBadPython", "--python", "--dry-run"],
            env_list_lines=[],
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a value", result.stderr)
        self.assertEqual(
            log_lines,
            [],
            msg="no conda subcommand should run when --python's value is rejected",
        )

    def test_dry_run_prints_commands_without_invoking_conda(self) -> None:
        result, log_lines = self._run(
            ["LrhTestEnvDryRun", "--dry-run"],
            env_list_lines=[],
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("conda create -n LrhTestEnvDryRun", result.stdout)
        self.assertIn("skipped under --dry-run", result.stdout)
        self.assertEqual(
            log_lines,
            [],
            msg="--dry-run must not actually invoke the fake conda executable, "
            "including for the environment-existence check",
        )

    def test_conda_create_failure_aborts_before_develop_runs(self) -> None:
        # Under `set -euo pipefail`, a nonzero `conda create` exit must abort
        # the script immediately -- no stale-install check or
        # scripts/develop invocation should follow.
        result, log_lines = self._run(
            ["LrhTestEnvFailingCreate"],
            env_list_lines=[],
            create_exit_code=1,
        )

        self.assertNotEqual(result.returncode, 0)
        run_lines = [line for line in log_lines if line.startswith("run ")]
        self.assertEqual(
            run_lines,
            [],
            msg="a failed conda create must abort before any conda run call",
        )


if __name__ == "__main__":
    unittest.main()
