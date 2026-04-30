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


if __name__ == "__main__":
    unittest.main()
