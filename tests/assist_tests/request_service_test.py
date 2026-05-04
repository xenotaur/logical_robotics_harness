import argparse
import os
import pathlib
import re
import tempfile
import unittest
from contextlib import contextmanager
from unittest import mock

from lrh.assist import request_service, request_templates


class TestBuildVariables(unittest.TestCase):
    def _build_args(self, **overrides: str | None) -> argparse.Namespace:
        defaults = {
            "template_name": "codex_prompt_from_work_item",
            "target": None,
            "target_option": None,
            "scope": None,
            "repo_name": None,
            "project_goal": None,
            "background_file": None,
            "background_text": None,
            "project_type": None,
            "bootstrap_mode": "minimal",
            "audit_file": None,
            "work_item_file": (
                "project/work_items/proposed/WI-INTERPRETATION-VALIDATION.md"
            ),
            "style_file": "STYLE.md",
            "patch_file": None,
            "show_vars": False,
            "prompt_id": None,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_build_variables_exposes_path_and_content_variants(self) -> None:
        args = self._build_args()

        variables = request_service.build_variables(args)

        self.assertEqual(variables["STYLE_GUIDE_PATH"], "STYLE.md")
        self.assertEqual(
            variables["WORK_ITEM_PATH"],
            "project/work_items/proposed/WI-INTERPRETATION-VALIDATION.md",
        )
        self.assertEqual(
            variables["STYLE_GUIDE_CONTENT"],
            variables["STYLE_GUIDE_CONTEXT"],
        )
        self.assertEqual(variables["WORK_ITEM_CONTENT"], variables["WORK_ITEM"])
        self.assertIn("LRH STYLE GUIDE", variables["STYLE_GUIDE_CONTENT"])
        self.assertIn("WI-INTERPRETATION-VALIDATION", variables["WORK_ITEM_CONTENT"])


class TestRequestTemplateOverrides(unittest.TestCase):
    def _args(self, template_name: str = "improve_coverage") -> argparse.Namespace:
        return argparse.Namespace(
            template_name=template_name,
            target="src/lrh/example.py",
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text=None,
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file=None,
            style_file=None,
            patch_file=None,
            show_vars=False,
            prompt_id=None,
            force=False,
            template_dir=None,
        )

    def test_package_template_renders_when_no_overrides_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir) / "home"
            with (
                mock.patch.dict(os.environ, {}, clear=True),
                mock.patch.object(pathlib.Path, "home", return_value=home),
            ):
                rendered, _ = request_service.generate_request(self._args())

        self.assertIn("PR Request to Improve Coverage", rendered)
        self.assertIn("src/lrh/example.py", rendered)

    def test_project_local_override_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            template_dir = project_root / ".lrh" / "templates" / "request"
            template_dir.mkdir(parents=True)
            (template_dir / "improve_coverage.md").write_text(
                "project {{TARGET_MODULE_GHA}}\n",
                encoding="utf-8",
            )

            rendered, _ = request_service.generate_request(
                self._args(),
                project_root=project_root,
            )

        self.assertEqual(rendered, "project src/lrh/example.py\n")

    def test_environment_override_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            env_dir = root / "env_templates"
            template_dir = env_dir / "request"
            template_dir.mkdir(parents=True)
            (template_dir / "improve_coverage.md").write_text(
                "environment {{MODULE_NAME}}\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"LRH_TEMPLATE_DIR": str(env_dir)}):
                rendered, _ = request_service.generate_request(self._args())

        self.assertEqual(rendered, "environment example\n")

    def test_explicit_template_dir_override_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_dir = pathlib.Path(temp_dir) / "explicit_templates"
            template_dir = explicit_dir / "request"
            template_dir.mkdir(parents=True)
            (template_dir / "improve_coverage.md").write_text(
                "explicit {{SUGGESTED_TEST_PATH}}\n",
                encoding="utf-8",
            )
            args = self._args()
            args.template_dir = str(explicit_dir)

            rendered, _ = request_service.generate_request(args)

        self.assertEqual(rendered, "explicit tests/example.py/example_test.py\n")

    def test_package_fallback_works_when_override_template_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_dir = pathlib.Path(temp_dir) / "explicit_templates"
            template_dir = explicit_dir / "request"
            template_dir.mkdir(parents=True)
            (template_dir / "other.md").write_text("other\n", encoding="utf-8")
            args = self._args()
            args.template_dir = str(explicit_dir)

            rendered, _ = request_service.generate_request(args)

        self.assertIn("PR Request to Improve Coverage", rendered)
        self.assertIn("src/lrh/example.py", rendered)

    def test_missing_template_has_clear_error(self) -> None:
        with self.assertRaisesRegex(
            FileNotFoundError,
            "Template not found: request/does_not_exist.md",
        ):
            request_service.generate_request(self._args("does_not_exist"))


class TestCodexPromptFromWorkItemResolution(unittest.TestCase):
    def _build_args(self, **overrides: str | None) -> argparse.Namespace:
        defaults = {
            "template_name": "codex_prompt_from_work_item",
            "target": None,
            "target_option": None,
            "scope": None,
            "repo_name": None,
            "project_goal": None,
            "background_file": None,
            "background_text": None,
            "project_type": None,
            "bootstrap_mode": "minimal",
            "audit_file": None,
            "work_item_file": None,
            "style_file": None,
            "patch_file": None,
            "show_vars": False,
            "prompt_id": None,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    @contextmanager
    def _temp_project(self) -> pathlib.Path:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            for bucket in ("proposed", "active", "resolved", "abandoned"):
                (root / "project" / "work_items" / bucket).mkdir(parents=True)
            (root / ".git").mkdir()
            old_cwd = pathlib.Path.cwd()
            try:
                os.chdir(root)
                yield root
            finally:
                os.chdir(old_cwd)

    def _write_style(
        self, root: pathlib.Path, *, name: str = "STYLE.md"
    ) -> pathlib.Path:
        style_path = root / name
        style_path.write_text("# Style\n\nUse tests.\n", encoding="utf-8")
        return style_path

    def _write_work_item(
        self,
        root: pathlib.Path,
        *,
        bucket: str,
        filename: str,
        work_item_id: str,
    ) -> pathlib.Path:
        path = root / "project" / "work_items" / bucket / filename
        path.write_text(
            (
                f"---\nid: {work_item_id}\ntitle: Example\n"
                "status: proposed\n---\n\nBody.\n"
            ),
            encoding="utf-8",
        )
        return path

    def test_positional_id_resolves_by_frontmatter_id(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="proposed",
                filename="different-name.md",
                work_item_id="WI-EXAMPLE-1",
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-EXAMPLE-1")
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/proposed/different-name.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "frontmatter_id")
            self.assertEqual(variables["STYLE_GUIDE_PATH"], "STYLE.md")

    def test_positional_stem_resolves(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="active",
                filename="WI-STEM-MATCH.md",
                work_item_id="WI-OTHER",
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-STEM-MATCH")
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/active/WI-STEM-MATCH.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "filename_stem")

    def test_positional_direct_file_path_resolves(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            work_item_path = self._write_work_item(
                root,
                bucket="resolved",
                filename="WI-DIRECT.md",
                work_item_id="WI-DIRECT",
            )

            variables = request_service.build_variables(
                self._build_args(target=str(work_item_path))
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/resolved/WI-DIRECT.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "target_path")

    def test_repo_root_relative_path_resolves_from_subdirectory(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="active",
                filename="WI-ROOT-REL.md",
                work_item_id="WI-ROOT-REL",
            )
            (root / "nested" / "deeper").mkdir(parents=True)
            old_cwd = pathlib.Path.cwd()
            try:
                os.chdir(root / "nested" / "deeper")
                variables = request_service.build_variables(
                    self._build_args(target="project/work_items/active/WI-ROOT-REL.md")
                )
            finally:
                os.chdir(old_cwd)

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/active/WI-ROOT-REL.md",
            )
            self.assertEqual(
                variables["WORK_ITEM_RESOLUTION"],
                "repo_root_relative_path",
            )

    def test_explicit_work_item_file_still_works(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            work_item_path = self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-EXPLICIT.md",
                work_item_id="WI-EXPLICIT",
            )

            variables = request_service.build_variables(
                self._build_args(work_item_file=str(work_item_path))
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/proposed/WI-EXPLICIT.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "explicit_flag")

    def test_explicit_work_item_file_takes_precedence(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            explicit_path = self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-EXPLICIT.md",
                work_item_id="WI-EXPLICIT",
            )
            self._write_work_item(
                root,
                bucket="active",
                filename="WI-TARGET.md",
                work_item_id="WI-TARGET",
            )

            variables = request_service.build_variables(
                self._build_args(
                    target="WI-TARGET",
                    work_item_file=str(explicit_path),
                )
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/proposed/WI-EXPLICIT.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "explicit_flag")

    def test_style_file_defaults_to_style_md(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-STYLE-DEFAULT.md",
                work_item_id="WI-STYLE-DEFAULT",
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-STYLE-DEFAULT")
            )

            self.assertEqual(variables["STYLE_GUIDE_PATH"], "STYLE.md")

    def test_explicit_style_file_overrides_default(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            alt_style = self._write_style(root, name="ALT_STYLE.md")
            self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-STYLE-EXPLICIT.md",
                work_item_id="WI-STYLE-EXPLICIT",
            )

            variables = request_service.build_variables(
                self._build_args(
                    target="WI-STYLE-EXPLICIT",
                    style_file=str(alt_style),
                )
            )

            self.assertEqual(variables["STYLE_GUIDE_PATH"], "ALT_STYLE.md")

    def test_missing_explicit_style_file_gives_flag_specific_error(self) -> None:
        with self._temp_project() as root:
            self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-STYLE-MISSING.md",
                work_item_id="WI-STYLE-MISSING",
            )
            with self.assertRaisesRegex(
                FileNotFoundError,
                r"error: --style-file does not exist: .*MISSING_STYLE\.md",
            ):
                request_service.build_variables(
                    self._build_args(
                        target="WI-STYLE-MISSING",
                        style_file=str(root / "MISSING_STYLE.md"),
                    )
                )

    def test_missing_work_item_gives_clear_error(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            with self.assertRaisesRegex(
                FileNotFoundError,
                "No work item matched target 'WI-MISSING'",
            ):
                request_service.build_variables(self._build_args(target="WI-MISSING"))

    def test_flat_work_item_file_resolves_by_frontmatter_id(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            flat_path = root / "project" / "work_items" / "WI-FLAT-0001.md"
            flat_path.write_text(
                "---\nid: WI-FLAT-0001\ntitle: Flat\nstatus: proposed\n---\n",
                encoding="utf-8",
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-FLAT-0001")
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"], "project/work_items/WI-FLAT-0001.md"
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "frontmatter_id")

    def test_nested_work_item_file_resolves_by_h1_id(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            nested_dir = root / "project" / "work_items" / "active" / "nested"
            nested_dir.mkdir(parents=True, exist_ok=True)
            nested_path = nested_dir / "work_item.md"
            nested_path.write_text(
                "# WI-NESTED-H1: Nested work item\n\nBody.\n", encoding="utf-8"
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-NESTED-H1")
            )

            self.assertEqual(
                variables["WORK_ITEM_PATH"],
                "project/work_items/active/nested/work_item.md",
            )
            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "h1_id")

    def test_nested_work_item_h1_resolves_after_leading_text(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            nested_dir = root / "project" / "work_items" / "active" / "nested"
            nested_dir.mkdir(parents=True, exist_ok=True)
            nested_path = nested_dir / "work_item.md"
            nested_path.write_text(
                "Intro text.\n\n# WI-leading_text-001: Nested work item\n",
                encoding="utf-8",
            )

            variables = request_service.build_variables(
                self._build_args(target="WI-leading_text-001")
            )

            self.assertEqual(variables["WORK_ITEM_RESOLUTION"], "h1_id")

    def test_ambiguous_match_gives_clear_error(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-DUP-A.md",
                work_item_id="WI-DUP",
            )
            self._write_work_item(
                root,
                bucket="active",
                filename="WI-DUP-B.md",
                work_item_id="WI-DUP",
            )
            with self.assertRaisesRegex(
                FileNotFoundError,
                "Pass --work-item-file explicitly",
            ):
                request_service.build_variables(self._build_args(target="WI-DUP"))

    def test_missing_path_like_target_fails_fast(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            self._write_work_item(
                root,
                bucket="proposed",
                filename="WI-EXAMPLE.md",
                work_item_id="WI-OTHER-ID",
            )
            with self.assertRaisesRegex(
                FileNotFoundError,
                "target looks like a work-item path but does not exist",
            ):
                request_service.build_variables(
                    self._build_args(target="project/work_items/active/WI-EXAMPLE.md")
                )


class TestCodexPromptFromWorkItemTemplate(unittest.TestCase):
    def _args(self) -> argparse.Namespace:
        return argparse.Namespace(
            template_name="codex_prompt_from_work_item",
            target=None,
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text="Short background context.",
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file="project/work_items/proposed/WI-INTERPRETATION-VALIDATION.md",
            style_file="STYLE.md",
            patch_file=None,
            show_vars=False,
            prompt_id=None,
            force=False,
        )

    def test_codex_prompt_renders_final_codex_cloud_prompt(self) -> None:
        rendered, variables = request_service.generate_request(self._args())

        self.assertIn("# ROLE", rendered)
        self.assertIn("# AUTHORITATIVE REFERENCES", rendered)
        self.assertIn("If `AGENTS.md` exists, read and follow it.", rendered)
        self.assertIn("If `STYLE.md` exists, read and follow it.", rendered)
        self.assertIn("If `PROMPTS.md` exists, follow its prompt-ID", rendered)
        self.assertIn(
            "Prefer `lrh prompt record-execution` if LRH is installed.", rendered
        )
        self.assertNotIn("scripts/prompts/record-execution", rendered)
        self.assertIn(
            "Approved work item: "
            "`project/work_items/proposed/WI-INTERPRETATION-VALIDATION.md`",
            rendered,
        )
        self.assertRegex(
            rendered,
            re.compile(
                "Prompt ID: `PROMPT\\("
                "WI-INTERPRETATION-VALIDATION:CODEX_PROMPT_FROM_WORK_ITEM\\)\\["
            ),
        )
        self.assertNotIn(variables["STYLE_GUIDE_CONTENT"], rendered)
        self.assertNotRegex(rendered, re.compile(r"\{\{[A-Z0-9_]+\}\}"))

    def test_explicit_prompt_id_is_used_when_provided(self) -> None:
        args = self._args()
        args.prompt_id = "PROMPT(AD_HOC:EXPLICIT)[2026-04-25T00:00:00+00:00]"

        rendered, _ = request_service.generate_request(args)

        self.assertIn(
            "Prompt ID: `PROMPT(AD_HOC:EXPLICIT)[2026-04-25T00:00:00+00:00]`",
            rendered,
        )

    def test_codex_prompt_uses_project_local_template_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            template_dir = project_root / ".lrh" / "templates" / "request"
            template_dir.mkdir(parents=True)
            (template_dir / "codex_prompt_from_work_item.md").write_text(
                "override {{WORK_ITEM_PATH}} {{STYLE_GUIDE_PATH}}\n",
                encoding="utf-8",
            )

            rendered, _ = request_service.generate_request(
                self._args(),
                project_root=project_root,
            )

        self.assertEqual(
            rendered,
            "override project/work_items/proposed/"
            "WI-INTERPRETATION-VALIDATION.md STYLE.md\n",
        )


class TestReviewResponseTemplate(unittest.TestCase):
    def test_review_response_renders_repair_prompt_with_unresolved_threads(
        self,
    ) -> None:
        args = argparse.Namespace(
            template_name="review_response",
            target="https://github.com/octo/repo/pull/7",
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text=None,
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file=None,
            style_file=None,
            patch_file=None,
            show_vars=False,
            prompt_id=None,
        )

        from unittest import mock

        threads_payload = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "path": "src/lrh/assist/request_service.py",
                                    "line": 101,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "author": {"login": "reviewer"},
                                                "body": "Please add a test.",
                                                "url": "https://github.com/octo/repo/pull/7#discussion_r1",
                                            }
                                        ]
                                    },
                                },
                                {
                                    "isResolved": True,
                                    "isOutdated": False,
                                    "comments": {"nodes": []},
                                },
                            ]
                        }
                    }
                }
            }
        }

        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            return_value=threads_payload,
        ):
            rendered, variables = request_service.generate_request(args)

        review_response_template = request_templates.load_template_text(
            "review_response"
        )
        expected_prefix = review_response_template.split(
            "{{UNRESOLVED_THREADS}}", maxsplit=1
        )[0].rstrip("\n")
        self.assertTrue(rendered.startswith(expected_prefix))
        self.assertIn("----PR Comments Follow—————————————————————", rendered)
        self.assertIn("PR: octo/repo#7", rendered)
        self.assertIn("src/lrh/assist/request_service.py:L101", rendered)
        self.assertIn("Please add a test.", rendered)
        self.assertIn("author: reviewer", rendered)
        self.assertIn(
            "url: https://github.com/octo/repo/pull/7#discussion_r1",
            rendered,
        )
        self.assertNotIn("# PR Review Response Request", rendered)
        self.assertNotIn(
            "Draft concise, technical responses for each unresolved thread",
            rendered,
        )
        self.assertEqual(variables["REVIEW_URL"], "https://github.com/octo/repo/pull/7")
        self.assertEqual(variables["REPO_NAME"], "octo/repo")

    def test_review_response_no_unresolved_threads_returns_nothing_to_resolve(
        self,
    ) -> None:
        args = argparse.Namespace(
            template_name="review_response",
            target="https://github.com/octo/repo/pull/7",
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text=None,
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file=None,
            style_file=None,
            patch_file=None,
            show_vars=False,
            prompt_id=None,
            force=False,
        )

        from unittest import mock

        threads_payload = {
            "data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}
        }

        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            return_value=threads_payload,
        ):
            rendered, _ = request_service.generate_request(args)

        self.assertEqual(
            rendered,
            "Nothing to resolve: no unresolved review threads found for octo/repo#7",
        )

    def test_review_response_force_renders_prompt_when_no_unresolved_threads(
        self,
    ) -> None:
        args = argparse.Namespace(
            template_name="review_response",
            target="https://github.com/octo/repo/pull/7",
            target_option=None,
            scope=None,
            repo_name=None,
            project_goal=None,
            background_file=None,
            background_text=None,
            project_type=None,
            bootstrap_mode="minimal",
            audit_file=None,
            work_item_file=None,
            style_file=None,
            patch_file=None,
            show_vars=False,
            prompt_id=None,
            force=True,
        )

        from unittest import mock

        threads_payload = {
            "data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}
        }

        with mock.patch(
            "lrh.assist.request_service.pull_reviews.get_pull_review_threads",
            return_value=threads_payload,
        ):
            rendered, _ = request_service.generate_request(args)

        self.assertIn("----PR Comments Follow", rendered)
        self.assertIn("PR: octo/repo#7", rendered)


if __name__ == "__main__":
    unittest.main()
