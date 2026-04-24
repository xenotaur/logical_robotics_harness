import argparse
import re
import unittest

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
