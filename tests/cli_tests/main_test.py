import unittest
import unittest.mock

from lrh.cli import main as cli_main
from tests import testing_support


class TestLrhMainCli(unittest.TestCase):
    def test_lrh_help_alias_prints_top_level_help(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "help"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertIn(
            "Logical Robotics Harness command-line interface.",
            captured.stdout.getvalue(),
        )
        self.assertIn("validate", captured.stdout.getvalue())
        self.assertIn("meta", captured.stdout.getvalue())

    def test_lrh_meta_help_includes_workspace_guidance(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "meta", "--help"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        output = captured.stdout.getvalue()
        self.assertIn("Workspace resolution precedence", output)
        self.assertIn("LRH_CONFIG", output)
        self.assertIn("LRH_WORKSPACE", output)
        self.assertIn("~/.config/lrh/config.toml", output)

    def test_lrh_meta_init_help_includes_mode_defaults(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "meta", "init", "--help"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        output = captured.stdout.getvalue()
        self.assertIn("Default mode is hybrid", output)
        self.assertIn("--mode {hybrid,global,local}", output)
        self.assertIn("~/.local/state/lrh/", output)

    def test_lrh_meta_register_help_includes_locator_semantics(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "meta", "register", "--help"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        output = captured.stdout.getvalue()
        self.assertIn("repo_locator = repository/ref locator", output)
        self.assertRegex(output, r"project_dir\s*=\s*relative path")
        self.assertIn(
            "https://github.com/xenotaur/taurworks/tree/master/project",
            output,
        )

    def test_lrh_help_meta_alias_routes_to_meta_help(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "help", "meta"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertIn("Manage LRH meta workspaces", captured.stdout.getvalue())

    def test_lrh_help_meta_init_alias_routes_to_meta_init_help(self) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "help", "meta", "init"]):
            with testing_support.capture_output() as captured:
                with self.assertRaises(SystemExit) as err_ctx:
                    cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertIn("Initialize LRH meta workspace", captured.stdout.getvalue())

    def test_lrh_dashdash_version_prints_package_version(self) -> None:
        expected_version = "9.9.9"

        with unittest.mock.patch("sys.argv", ["lrh", "--version"]):
            with unittest.mock.patch(
                "lrh.version.get_installed_version", return_value=expected_version
            ):
                with testing_support.capture_output() as captured:
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertEqual(captured.stdout.getvalue().strip(), f"lrh {expected_version}")

    def test_lrh_version_subcommand_prints_package_version(self) -> None:
        expected_version = "9.9.9"

        with unittest.mock.patch("sys.argv", ["lrh", "version"]):
            with unittest.mock.patch(
                "lrh.version.get_installed_version", return_value=expected_version
            ):
                with testing_support.capture_output() as captured:
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertEqual(captured.stdout.getvalue().strip(), f"lrh {expected_version}")

    def test_lrh_dashdash_version_prints_unknown_when_metadata_unavailable(
        self,
    ) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "--version"]):
            with unittest.mock.patch(
                "lrh.version.get_installed_version", return_value=None
            ):
                with testing_support.capture_output() as captured:
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertEqual(captured.stdout.getvalue().strip(), "lrh unknown")

    def test_lrh_version_subcommand_prints_unknown_when_metadata_unavailable(
        self,
    ) -> None:
        with unittest.mock.patch("sys.argv", ["lrh", "version"]):
            with unittest.mock.patch(
                "lrh.version.get_installed_version", return_value=None
            ):
                with testing_support.capture_output() as captured:
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
        self.assertEqual(captured.stderr.getvalue(), "")
        self.assertEqual(captured.stdout.getvalue().strip(), "lrh unknown")
