import contextlib
import io
import unittest
import unittest.mock

from lrh.cli import main as cli_main


class LrhBranchesCliTest(unittest.TestCase):
    def test_lrh_branches_help(self) -> None:
        stdout = io.StringIO()
        with unittest.mock.patch("sys.argv", ["lrh", "branches", "--help"]):
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as ctx:
                    cli_main.main()
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("survey", stdout.getvalue())

    def test_lrh_branches_survey_help_documents_report_only_contract(self) -> None:
        stdout = io.StringIO()
        with unittest.mock.patch("sys.argv", ["lrh", "branches", "survey", "--help"]):
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as ctx:
                    cli_main.main()
        self.assertEqual(ctx.exception.code, 0)
        output = " ".join(stdout.getvalue().split())
        self.assertIn("never executes them itself", output)
        self.assertIn("--write-delete-commands", output)
        self.assertIn("--format", output)

    def test_lrh_branches_survey_requires_subcommand(self) -> None:
        stderr = io.StringIO()
        with unittest.mock.patch("sys.argv", ["lrh", "branches"]):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as ctx:
                    cli_main.main()
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
