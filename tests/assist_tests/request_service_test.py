import argparse
import os
import pathlib
import re
import tempfile
import unittest
from contextlib import contextmanager

from lrh.assist import request_service


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

    def test_missing_work_item_gives_clear_error(self) -> None:
        with self._temp_project() as root:
            self._write_style(root)
            with self.assertRaisesRegex(
                FileNotFoundError,
                "No work item matched target 'WI-MISSING'",
            ):
                request_service.build_variables(self._build_args(target="WI-MISSING"))

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
        )

    def test_codex_prompt_uses_paths_without_inlining_full_style_guide(self) -> None:
        rendered, variables = request_service.generate_request(self._args())

        self.assertIn("Read and follow `STYLE.md`", rendered)
        self.assertIn(
            "Implement only the approved work item at "
            "`project/work_items/proposed/WI-INTERPRETATION-VALIDATION.md`",
            rendered,
        )
        self.assertNotIn(variables["STYLE_GUIDE_CONTENT"], rendered)
        self.assertNotRegex(rendered, re.compile(r"\{\{[A-Z0-9_]+\}\}"))


if __name__ == "__main__":
    unittest.main()
