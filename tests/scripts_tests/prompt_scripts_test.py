import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


class PromptScriptTests(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _label_script(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "prompts" / "label-prompt"

    def _record_script(self) -> pathlib.Path:
        return self._repo_root() / "scripts" / "prompts" / "record-execution"

    def test_label_prompt_help_succeeds(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(self._label_script()), "--help"],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("Generate a prompt ID", completed.stdout)

    def test_label_prompt_emits_prompt_id_and_suggested_path(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(self._label_script()), "--slug", "example-task"],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("prompt_id: PROMPT(AD_HOC:EXAMPLE_TASK)", completed.stdout)
        self.assertIn("execution_dir: project/executions/AD_HOC", completed.stdout)
        self.assertRegex(
            completed.stdout,
            r"suggested_execution_file: project/executions/AD_HOC/\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_EXAMPLE_TASK\.md",
        )

    def test_label_prompt_rejects_unsafe_work_item(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self._label_script()),
                "--work-item",
                "../escape",
                "--slug",
                "example-task",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("work-item must match", completed.stderr)

    def test_record_execution_dry_run_prints_content_without_writing(self) -> None:
        prompt_id = "PROMPT(AD_HOC:EXAMPLE_TASK)[2026-04-24T00:00:00-04:00]"
        completed = subprocess.run(
            [
                sys.executable,
                str(self._record_script()),
                "--prompt-id",
                prompt_id,
                "--slug",
                "example-task",
                "--status",
                "planned",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertRegex(
            completed.stdout,
            r"output_file: .*/project/executions/AD_HOC/\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_EXAMPLE_TASK\.md",
        )
        self.assertIn(f"prompt_id: {prompt_id}", completed.stdout)
        self.assertIn("status: planned", completed.stdout)
        self.assertIn("# Summary", completed.stdout)

    def test_record_execution_writes_file_with_expected_front_matter(self) -> None:
        prompt_id = "PROMPT(WI-META-CLI-MVP:REGISTER_IMPLEMENTATION)[2026-04-24T16:24:13-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = pathlib.Path(temp_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self._record_script()),
                    "--prompt-id",
                    prompt_id,
                    "--work-item",
                    "WI-META-CLI-MVP",
                    "--slug",
                    "register-implementation",
                    "--status",
                    "planned",
                    "--output-root",
                    str(output_root),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            match = re.search(r"wrote: (.+\.md)", completed.stdout)
            self.assertIsNotNone(match)
            output_file = pathlib.Path(match.group(1))
            self.assertTrue(output_file.exists())

            content = output_file.read_text(encoding="utf-8")
            self.assertIn("work_item: WI-META-CLI-MVP", content)
            self.assertIn(f"prompt_id: {prompt_id}", content)
            self.assertIn("status: planned", content)

    def test_record_execution_defaults_to_ad_hoc_when_work_item_not_provided(self) -> None:
        prompt_id = "PROMPT(AD_HOC:REGISTER_AUDIT)[2026-04-24T16:24:13-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = pathlib.Path(temp_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self._record_script()),
                    "--prompt-id",
                    prompt_id,
                    "--slug",
                    "register-audit",
                    "--output-root",
                    str(output_root),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            ad_hoc_dir = output_root / "AD_HOC"
            self.assertTrue(ad_hoc_dir.exists())
            files = list(ad_hoc_dir.glob("*.md"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            self.assertIn("work_item: AD_HOC", content)

    def test_record_execution_rejects_unsafe_work_item(self) -> None:
        prompt_id = "PROMPT(AD_HOC:REGISTER_AUDIT)[2026-04-24T16:24:13-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = pathlib.Path(temp_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self._record_script()),
                    "--prompt-id",
                    prompt_id,
                    "--work-item",
                    "../escape",
                    "--slug",
                    "register-audit",
                    "--output-root",
                    str(output_root),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("work-item must match", completed.stderr)
            self.assertFalse((output_root / "escape").exists())


if __name__ == "__main__":
    unittest.main()
