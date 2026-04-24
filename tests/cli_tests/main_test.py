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

    def test_lrh_meta_help_includes_workspace_guidance(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "meta", "--help"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Workspace resolution precedence", output)
        self.assertIn("LRH_CONFIG", output)
        self.assertIn("LRH_WORKSPACE", output)
        self.assertIn("~/.config/lrh/config.toml", output)

    def test_lrh_meta_init_help_includes_mode_defaults(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "meta", "init", "--help"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Default mode is hybrid", output)
        self.assertIn("--mode {hybrid,global,local}", output)
        self.assertIn("~/.local/state/lrh/", output)

    def test_lrh_help_meta_alias_routes_to_meta_help(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "help", "meta"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Manage LRH meta workspaces", stdout.getvalue())

    def test_lrh_help_meta_init_alias_routes_to_meta_init_help(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch("sys.argv", ["lrh", "help", "meta", "init"]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Initialize LRH meta workspace", stdout.getvalue())
