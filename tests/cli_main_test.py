import contextlib
import io
import unittest
import unittest.mock

from lrh.cli import main as cli_main


class TestLrhMainCli(unittest.TestCase):
    def test_lrh_help_alias_prints_top_level_help(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "help"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(
            "Logical Robotics Harness command-line interface.", stdout.getvalue()
        )
        self.assertIn("validate", stdout.getvalue())
        self.assertIn("meta", stdout.getvalue())
