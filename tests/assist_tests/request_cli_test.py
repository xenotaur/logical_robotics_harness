import contextlib
import io
import os
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh.assist import request_cli


class TestRequestCli(unittest.TestCase):
    def test_parser_help_mentions_ci_request_templates(self) -> None:
        parser = request_cli.build_parser(prog="lrh request")
        help_text = parser.format_help()

        self.assertIn("ci_assess_status", help_text)
        self.assertIn("ci_implement_workflow", help_text)

    def test_template_dir_flag_uses_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            template_dir = root / "templates"
            request_dir = template_dir / "request"
            request_dir.mkdir(parents=True)
            (request_dir / "improve_coverage.md").write_text(
                "cli {{MODULE_NAME}}\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "improve_coverage",
                        "src/lrh/example.py",
                        "--template-dir",
                        str(template_dir),
                    ],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "cli example\n")
        self.assertEqual(stderr.getvalue(), "")

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

    def test_output_write_error_returns_handled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_item = root / "WI-EXAMPLE.md"
            style_file = root / "STYLE.md"
            out_dir = root / "prompt.md"
            out_dir.mkdir()
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
                    "- Run tests.\n\n"
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
                        str(out_dir),
                        "--style-file",
                        str(style_file),
                    ],
                    prog="lrh request",
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("error:", stderr.getvalue())
            self.assertIn("Is a directory", stderr.getvalue())
            self.assertEqual("", stdout.getvalue())

    def test_review_response_requires_target_url(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = request_cli.run_request_cli(
                ["review_response"], prog="lrh request"
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("review_response requires a target PR URL", stderr.getvalue())
        self.assertEqual("", stdout.getvalue())

    def test_review_response_fetch_error_returns_nonzero(self) -> None:
        import unittest.mock as mock

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            side_effect=OSError("github api failed"),
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    ["review_response", "https://github.com/octo/repo/pull/7"],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("github api failed", stderr.getvalue())
        self.assertEqual("", stdout.getvalue())

    def test_review_response_no_unresolved_threads_prints_nothing_to_resolve(
        self,
    ) -> None:
        import unittest.mock as mock

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            return_value={
                "data": {
                    "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
                }
            },
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    ["review_response", "https://github.com/octo/repo/pull/7"],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "Nothing to resolve: no unresolved review threads found for octo/repo#7\n",
        )

    def test_review_response_force_prints_full_prompt_with_no_unresolved_threads(
        self,
    ) -> None:
        import unittest.mock as mock

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            return_value={
                "data": {
                    "repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}
                }
            },
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "review_response",
                        "https://github.com/octo/repo/pull/7",
                        "--force",
                    ],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("----PR Comments Follow", stdout.getvalue())
        self.assertIn("PR: octo/repo#7", stdout.getvalue())

    def test_review_response_missing_pull_request_is_error(self) -> None:
        import unittest.mock as mock

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            side_effect=ValueError(
                "error: pull request not found or inaccessible: octo/repo#999"
            ),
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    ["review_response", "https://github.com/octo/repo/pull/999"],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("pull request not found or inaccessible", stderr.getvalue())
        self.assertEqual("", stdout.getvalue())

    def test_templates_list_includes_package_templates(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = request_cli.run_request_cli(
                ["templates", "list"],
                prog="lrh request",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(
            "review_response\tpackage\tpackage fallback\t"
            "lrh.assist.templates/request/review_response.md",
            stdout.getvalue(),
        )

    def test_templates_list_includes_override_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = pathlib.Path(temp_dir)
            template_path = template_root / "request" / "custom.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("custom\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "templates",
                        "--template-dir",
                        str(template_root),
                        "list",
                    ],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(
            f"custom\texplicit\tfilesystem override\t{template_path}",
            stdout.getvalue(),
        )

    def test_templates_where_reports_explicit_override_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = pathlib.Path(temp_dir)
            template_path = template_root / "request" / "review_response.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("override\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    [
                        "templates",
                        "--template-dir",
                        str(template_root),
                        "where",
                        "request/review_response.md",
                    ],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "request/review_response.md\texplicit\tfilesystem override\t"
            f"{template_path}\n",
        )

    def test_templates_where_reports_environment_override_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = pathlib.Path(temp_dir)
            template_path = template_root / "request" / "review_response.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("env\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with unittest.mock.patch.dict(
                os.environ,
                {"LRH_TEMPLATE_DIR": str(template_root)},
                clear=True,
            ):
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    exit_code = request_cli.run_request_cli(
                        ["templates", "where", "review_response"],
                        prog="lrh request",
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "request/review_response.md\tenvironment\tfilesystem override\t"
            f"{template_path}\n",
        )

    def test_templates_where_reports_project_local_override_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            (project_root / ".git").mkdir()
            template_path = (
                project_root / ".lrh" / "templates" / "request" / "review_response.md"
            )
            template_path.parent.mkdir(parents=True)
            template_path.write_text("project\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            old_cwd = pathlib.Path.cwd()

            try:
                os.chdir(project_root)
                with unittest.mock.patch.dict(os.environ, {}, clear=True):
                    with (
                        contextlib.redirect_stdout(stdout),
                        contextlib.redirect_stderr(stderr),
                    ):
                        exit_code = request_cli.run_request_cli(
                            ["templates", "where", "review_response"],
                            prog="lrh request",
                        )
            finally:
                os.chdir(old_cwd)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "request/review_response.md\tproject\tfilesystem override\t"
            f"{template_path}\n",
        )

    def test_templates_where_reports_user_override_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_home = root / "config"
            template_path = (
                config_home / "lrh" / "templates" / "request" / "review_response.md"
            )
            template_path.parent.mkdir(parents=True)
            template_path.write_text("user\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with unittest.mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(config_home)},
                clear=True,
            ):
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    exit_code = request_cli.run_request_cli(
                        ["templates", "where", "review_response"],
                        prog="lrh request",
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "request/review_response.md\tuser\tfilesystem override\t"
            f"{template_path}\n",
        )

    def test_templates_where_reports_package_fallback_source(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = request_cli.run_request_cli(
                    ["templates", "where", "review_response"],
                    prog="lrh request",
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stdout.getvalue(),
            "request/review_response.md\tpackage\tpackage fallback\t"
            "lrh.assist.templates/request/review_response.md\n",
        )

    def test_templates_where_missing_template_is_clear(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = request_cli.run_request_cli(
                ["templates", "where", "does_not_exist"],
                prog="lrh request",
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn(
            "Template not found: request/does_not_exist.md", stderr.getvalue()
        )

    def test_templates_where_rejects_unsafe_logical_name(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = request_cli.run_request_cli(
                ["templates", "where", "../review_response"],
                prog="lrh request",
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Unsafe template logical name", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
