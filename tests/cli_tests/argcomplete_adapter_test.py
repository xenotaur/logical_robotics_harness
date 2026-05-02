import argparse
import contextlib
import sys
import types
import unittest
import unittest.mock

from lrh.cli import argcomplete_adapter
from lrh.cli import main as cli_main


class TestArgcompleteAdapter(unittest.TestCase):

    def test_enable_completion_noops_without_argcomplete(self) -> None:
        parser = argparse.ArgumentParser(prog="lrh")

        with unittest.mock.patch.dict(sys.modules, {"argcomplete": None}):
            argcomplete_adapter.enable_completion(parser)

    def test_enable_completion_calls_autocomplete_when_available(self) -> None:
        parser = argparse.ArgumentParser(prog="lrh")
        fake_argcomplete = types.SimpleNamespace(
            autocomplete=unittest.mock.Mock(),
        )

        with unittest.mock.patch.dict(sys.modules, {"argcomplete": fake_argcomplete}):
            argcomplete_adapter.enable_completion(parser)

        fake_argcomplete.autocomplete.assert_called_once_with(parser)

    def test_main_cli_constructs_when_argcomplete_missing(self) -> None:
        with unittest.mock.patch.dict(sys.modules, {"argcomplete": None}):
            with unittest.mock.patch("sys.argv", ["lrh", "--help"]):
                with contextlib.redirect_stdout(sys.stdout), contextlib.redirect_stderr(sys.stderr):
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)
