import argparse
import contextlib
import pathlib
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
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as err_ctx:
                        cli_main.main()

        self.assertEqual(err_ctx.exception.code, 0)

    def test_request_template_completer_delegates_to_completion_sources(self) -> None:
        parsed_args = argparse.Namespace(template_name="")
        with unittest.mock.patch(
            "lrh.cli.argcomplete_adapter.completion_sources.request_template_names",
            return_value=["one"],
        ) as mock_provider:
            result = argcomplete_adapter.request_template_completer(
                "o", parsed_args, action=object(), parser=object()
            )
        self.assertEqual(result, ["one"])
        mock_provider.assert_called_once_with(prefix="o")

    def test_codex_work_item_target_completer_returns_empty_for_other_templates(
        self,
    ) -> None:
        parsed_args = argparse.Namespace(template_name="improve_coverage")
        self.assertEqual(
            argcomplete_adapter.codex_work_item_target_completer("WI-", parsed_args),
            [],
        )

    def test_codex_work_item_target_completer_delegates_when_repo_found(self) -> None:
        parsed_args = argparse.Namespace(template_name="codex_prompt_from_work_item")
        with (
            unittest.mock.patch(
                "lrh.cli.argcomplete_adapter.request_variables.find_repo_root",
                return_value=pathlib.Path("/repo"),
            ) as mock_find_root,
            unittest.mock.patch(
                "lrh.cli.argcomplete_adapter.completion_sources.work_item_ids",
                return_value=["WI-RELEASE-TAG-CI"],
            ) as mock_provider,
        ):
            result = argcomplete_adapter.codex_work_item_target_completer(
                "WI-R", parsed_args
            )
        self.assertEqual(result, ["WI-RELEASE-TAG-CI"])
        mock_find_root.assert_called_once_with()
        mock_provider.assert_called_once()
