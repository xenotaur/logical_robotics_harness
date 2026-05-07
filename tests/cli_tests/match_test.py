import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class MatchCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def test_lrh_match_executions_found_returns_0(self) -> None:
        prompt_id = "PROMPT(AD_HOC:FOUND)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(f"Run this. {prompt_id}\n", encoding="utf-8")
            record = project_root / "project/executions/AD_HOC/found.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(
                f"---\nprompt_id: {prompt_id}\n"
                "work_item: AD_HOC\nstatus: landed\n---\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
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
        self.assertIn("exact: 1 execution record found", completed.stdout)
        self.assertIn("status=landed", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_lrh_match_executions_no_prompt_id_returns_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = pathlib.Path(temp_dir) / "prompt.md"
            prompt_file.write_text("No ID here.\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
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
        self.assertIn("No prompt IDs found", completed.stdout)

    def test_lrh_match_executions_ambiguous_returns_2(self) -> None:
        prompt_id = "PROMPT(AD_HOC:DUP)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(prompt_id, encoding="utf-8")
            for name in ("a.md", "b.md"):
                record = project_root / "project/executions/AD_HOC" / name
                record.parent.mkdir(parents=True, exist_ok=True)
                record.write_text(
                    f"---\nprompt_id: {prompt_id}\n"
                    "work_item: AD_HOC\nstatus: landed\n---\n",
                    encoding="utf-8",
                )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
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
        self.assertIn("multiple execution records found", completed.stdout)
        self.assertIn("human review required", completed.stdout)

    def test_lrh_match_executions_missing_prompt_file_returns_2(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = pathlib.Path(temp_dir) / "missing.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("error: unable to read prompt file", completed.stderr)

    def test_lrh_match_executions_non_utf8_prompt_file_returns_2(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = pathlib.Path(temp_dir) / "prompt.md"
            prompt_file.write_bytes(b"\xff\xfe\x00\x00")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("error: unable to read prompt file", completed.stderr)

    def test_lrh_match_executions_respects_output_root(self) -> None:
        prompt_id = "PROMPT(AD_HOC:CUSTOM)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(prompt_id, encoding="utf-8")
            record = project_root / "custom/executions/AD_HOC/custom.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(
                f"---\nprompt_id: {prompt_id}\n"
                "work_item: AD_HOC\nstatus: landed\n---\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "match",
                    "executions",
                    str(prompt_file),
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
        self.assertIn("custom/executions/AD_HOC/custom.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
