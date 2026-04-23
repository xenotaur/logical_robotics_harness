import argparse
import pathlib
import tempfile
import unittest

from lrh.assist import request_service


class TestGenerateRequest(unittest.TestCase):
    def test_codex_prompt_from_work_item_transforms_work_item_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            work_item_file = temp_path / "work_item.md"
            style_file = temp_path / "STYLE.md"

            work_item_file.write_text(
                "\n".join(
                    [
                        "# WI-TEST",
                        "",
                        "- **Risk level:** Low",
                        "- **Execution suitability:** Codex-suitable",
                        "",
                        "## Problem",
                        "Fix request transformation execution.",
                        "",
                        "## Scope",
                        "- Update request pipeline execution path.",
                        "- Keep changes minimal.",
                        "",
                        "## Out of Scope",
                        "- Template redesign.",
                        "",
                        "## Validation",
                        "- scripts/test",
                        "- scripts/validate",
                        "",
                        "## Acceptance criteria",
                        "- Output differs from request template.",
                    ]
                ),
                encoding="utf-8",
            )
            style_file.write_text("style rules", encoding="utf-8")

            args = argparse.Namespace(
                template_name="codex_prompt_from_work_item",
                target=None,
                target_option=None,
                repo_name=None,
                project_goal=None,
                background_file=None,
                background_text=None,
                project_type=None,
                bootstrap_mode="minimal",
                scope=None,
                audit_file=None,
                work_item_file=str(work_item_file),
                style_file=str(style_file),
                patch_file=None,
            )

            rendered, _ = request_service.generate_request(args)

            self.assertIn("# ROLE", rendered)
            self.assertIn("Fix request transformation execution.", rendered)
            self.assertIn("- scripts/test", rendered)
            self.assertNotIn("{{WORK_ITEM}}", rendered)
            self.assertNotIn("Codex Implementation Prompt from Work Item", rendered)


if __name__ == "__main__":
    unittest.main()
