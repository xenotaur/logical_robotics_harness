import contextlib
import io
import pathlib
import tempfile
import unittest

from lrh.assist import request_cli


class TestRequestCli(unittest.TestCase):
    def test_codex_prompt_from_work_item_command_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
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
                    "Need a small focused change.\n\n"
                    "## Scope\n\n"
                    "- Make one narrow CLI integration.\n\n"
                    "## Required Changes\n\n"
                    "- Add request command wiring.\n\n"
                    "## Validation\n\n"
                    "- Run `python -m unittest`.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Command writes output file.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
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
                    prog="lrh request",
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue(out_file.is_file())
            rendered = out_file.read_text(encoding="utf-8")
            self.assertIn("Prompt ID: `PROMPT(AD_HOC:EXAMPLE_IMPLEMENTATION)", rendered)
            self.assertIn("Approved work item:", rendered)

    def test_malformed_work_item_returns_handled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            bad_work_item = root / "WI-BAD.md"
            style_file = root / "STYLE.md"
            bad_work_item.write_text(
                (
                    "---\n"
                    "id: WI-BAD\n"
                    "status: proposed\n"
                    "type: operation\n"
                    "---\n\n"
                    "## Summary\n\n"
                    "Missing title in frontmatter should fail validation.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "codex_prompt_from_work_item",
                        "--work-item-file",
                        str(bad_work_item),
                        "--style-file",
                        str(style_file),
                    ],
                    prog="lrh request",
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("work item frontmatter field 'title'", stderr.getvalue())
            self.assertEqual("", stdout.getvalue())

    def test_invalid_slug_returns_handled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
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
                    "Body.\n\n"
                    "## Scope\n\n"
                    "- Scope.\n\n"
                    "## Required Changes\n\n"
                    "- Changes.\n\n"
                    "## Validation\n\n"
                    "- Run tests.\n\n"
                    "## Acceptance Criteria\n\n"
                    "- Works.\n"
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "codex-prompt-from-work-item",
                        "--work-item",
                        str(work_item),
                        "--slug",
                        "!!!",
                        "--out",
                        str(out_file),
                    ],
                    prog="lrh request",
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "--slug must include at least one letter or number",
                stderr.getvalue(),
            )
            self.assertEqual("", stdout.getvalue())
            self.assertFalse(out_file.exists())

    def test_non_boolean_blocked_field_returns_handled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            bad_work_item = root / "WI-BAD-BLOCKED.md"
            style_file = root / "STYLE.md"
            bad_work_item.write_text(
                (
                    "---\n"
                    "id: WI-BAD-BLOCKED\n"
                    "title: Example\n"
                    "status: proposed\n"
                    "type: operation\n"
                    'blocked: "false"\n'
                    "---\n\n"
                    "## Summary\n\n"
                    "Body.\n"
                ),
                encoding="utf-8",
            )
            style_file.write_text("# Style\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "codex_prompt_from_work_item",
                        "--work-item-file",
                        str(bad_work_item),
                        "--style-file",
                        str(style_file),
                    ],
                    prog="lrh request",
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "work item frontmatter field 'blocked' must be a bool",
                stderr.getvalue(),
            )
            self.assertEqual("", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
