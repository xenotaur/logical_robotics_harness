import subprocess
import tempfile
import unittest
from pathlib import Path


class TestLrhRequestCli(unittest.TestCase):
    def _run_lrh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            return subprocess.run(
                ["lrh", *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

    def test_lrh_request_help(self) -> None:
        result = self._run_lrh(["request", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("lrh request", result.stdout)

    def test_lrh_request_improve_coverage(self) -> None:
        result = self._run_lrh(
            ["request", "improve_coverage", "src/lrh/analysis/llm_extractor.py"]
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("TARGET MODULE:", result.stdout)
        self.assertIn("src/lrh/analysis/llm_extractor.py", result.stdout)

    def test_lrh_request_invalid_arguments(self) -> None:
        result = self._run_lrh(["request", "assessment", "--scope", "work_item"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires --target", result.stderr)

    def test_lrh_request_codex_prompt_from_work_item_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            style_file = root / "STYLE.md"
            out_file = root / "prompt.md"
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "example-implementation",
                    "--out",
                    str(out_file),
                    "--style-file",
                    str(style_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertTrue(out_file.is_file())
            self.assertIn(
                "PROMPT(AD_HOC:EXAMPLE_IMPLEMENTATION)",
                out_file.read_text(encoding="utf-8"),
            )

    def test_lrh_request_codex_prompt_from_work_item_invalid_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            out_file = root / "prompt.md"
            work_item.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    "blocked: false\n"
                    "---\n\n"
                    "## Problem\n\n"
                    "Need a focused CLI integration.\n\n"
                    "## Scope\n\n"
                    "- Add CLI adapter.\n\n"
                    "## Required Changes\n\n"
                    "- Wire command entrypoint.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Output prompt renders.\n"
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "lrh",
                    "request",
                    "codex-prompt-from-work-item",
                    "--work-item",
                    str(work_item),
                    "--slug",
                    "!!!",
                    "--out",
                    str(out_file),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "--slug must include at least one letter or number", result.stderr
            )
            self.assertEqual(result.stdout, "")
            self.assertFalse(out_file.exists())
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
