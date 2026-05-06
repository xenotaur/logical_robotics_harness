import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class PromptCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def test_lrh_prompt_label_emits_prompt_id(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "lrh.cli.main",
                "prompt",
                "label",
                "--slug",
                "create-installed-prompt-cli",
                "--project-root",
                "/tmp/client-repo",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn(
            "prompt_id: PROMPT(AD_HOC:CREATE_INSTALLED_PROMPT_CLI)", completed.stdout
        )
        self.assertIn(
            "execution_dir: /tmp/client-repo/project/executions/AD_HOC",
            completed.stdout,
        )

    def test_lrh_prompt_record_execution_dry_run(self) -> None:
        prompt_id = (
            "PROMPT(AD_HOC:CREATE_INSTALLED_PROMPT_CLI)[2026-04-29T22:05:00-04:00]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "record-execution",
                    "--prompt-id",
                    prompt_id,
                    "--slug",
                    "create-installed-prompt-cli",
                    "--project-root",
                    temp_dir,
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertRegex(
            completed.stdout, r"output_file: .*/project/executions/AD_HOC/\d{4}_"
        )
        self.assertIn("# Summary", completed.stdout)

    def test_lrh_prompt_help_includes_check_execution(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "lrh.cli.main", "prompt", "--help"],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=self._repo_root(),
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("check-execution", completed.stdout)

    def test_lrh_prompt_check_execution_not_found_returns_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    "PROMPT(AD_HOC:MISSING)[2026-05-01T17:40:00-04:00]",
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 1, msg=completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertIn("No execution records found", completed.stderr)

    def test_lrh_prompt_check_execution_found_returns_0(self) -> None:
        prompt_id = "PROMPT(AD_HOC:FOUND)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            record = pathlib.Path(temp_dir) / "project/executions/2026_05_01_A.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(
                f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    prompt_id,
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("status=landed", completed.stdout)

    def test_lrh_prompt_check_execution_found_with_quoted_prompt_id(self) -> None:
        prompt_id = "PROMPT(AD_HOC:QUOTED)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            record = pathlib.Path(temp_dir) / "project/executions/AD_HOC/quoted.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(
                f'---\nprompt_id: "{prompt_id}"\nstatus: landed\n---\n',
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    prompt_id,
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("status=landed", completed.stdout)

    def test_lrh_prompt_check_execution_ignores_non_utf8_markdown_file(self) -> None:
        prompt_id = "PROMPT(AD_HOC:NON_UTF8)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            record = pathlib.Path(temp_dir) / "project/executions/AD_HOC/bad.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_bytes(b"\xff\xfe\x00\x00")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    prompt_id,
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 1, msg=completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_lrh_prompt_check_execution_ambiguous_returns_2(self) -> None:
        prompt_id = "PROMPT(AD_HOC:DUP)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            for rel_path, status in (
                ("project/executions/2026_05_01_A.md", "landed"),
                ("project/executions/AD_HOC/2026_05_01_B.md", "in_progress"),
            ):
                record = pathlib.Path(temp_dir) / rel_path
                record.parent.mkdir(parents=True, exist_ok=True)
                record.write_text(
                    f"---\nprompt_id: {prompt_id}\nstatus: {status}\n---\n",
                    encoding="utf-8",
                )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    prompt_id,
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 2, msg=completed.stderr)
        self.assertIn("status=landed", completed.stdout)
        self.assertIn("status=in_progress", completed.stdout)
        self.assertIn("human review required", completed.stderr)

    def test_lrh_prompt_check_execution_respects_output_root(self) -> None:
        prompt_id = "PROMPT(AD_HOC:CUSTOM_ROOT)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            record = pathlib.Path(temp_dir) / "custom/executions/AD_HOC/A.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(
                f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "prompt",
                    "check-execution",
                    "--prompt-id",
                    prompt_id,
                    "--project-root",
                    temp_dir,
                    "--output-root",
                    "custom/executions",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("custom/executions/AD_HOC/A.md", completed.stdout)
        self.assertIn("status=landed", completed.stdout)

    def test_lrh_prompt_check_execution_project_root_from_outside_repo(self) -> None:
        prompt_id = "PROMPT(AD_HOC:OUTSIDE)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as project_dir:
            with tempfile.TemporaryDirectory() as outside_cwd:
                record = pathlib.Path(project_dir) / "project/executions/AD_HOC/A.md"
                record.parent.mkdir(parents=True, exist_ok=True)
                record.write_text(
                    f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                    encoding="utf-8",
                )
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lrh.cli.main",
                        "prompt",
                        "check-execution",
                        "--prompt-id",
                        prompt_id,
                        "--project-root",
                        project_dir,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy(),
                    cwd=outside_cwd,
                )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)


if __name__ == "__main__":
    unittest.main()
