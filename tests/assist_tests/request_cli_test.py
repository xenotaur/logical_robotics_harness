import contextlib
import io
import pathlib
import tempfile
import unittest

from lrh.assist import request_cli


class TestRequestCli(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
