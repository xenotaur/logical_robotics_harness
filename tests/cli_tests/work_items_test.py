import contextlib
import io
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh.cli import main as cli_main


class WorkItemsCliTest(unittest.TestCase):
    def test_check_nonzero_when_changes_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            file_path = root / "project/work_items/WI-CLI-1.md"
            file_path.parent.mkdir(parents=True)
            file_path.write_text("# WI-CLI-1", encoding="utf-8")

            stdout = io.StringIO()
            with unittest.mock.patch(
                "sys.argv",
                [
                    "lrh",
                    "work-items",
                    "organize",
                    "--project-root",
                    str(root),
                    "--check",
                ],
            ):
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as err:
                        cli_main.main()
            self.assertEqual(err.exception.code, 1)
