import pathlib
import tempfile
import unittest

from lrh.assist import work_item_prompt_core


class TestWorkItemPromptCore(unittest.TestCase):
    def _write_work_item(
        self, root: pathlib.Path, *, status: str = "proposed"
    ) -> pathlib.Path:
        path = root / "WI-EXAMPLE.md"
        path.write_text(
            (
                "---\n"
                "id: WI-EXAMPLE\n"
                "title: Example item\n"
                "type: deliverable\n"
                f"status: {status}\n"
                "blocked: false\n"
                "acceptance:\n"
                "  - acceptance from frontmatter\n"
                "---\n\n"
                "## Summary\n\n"
                "One-line summary.\n\n"
                "## Problem\n\n"
                "Current behavior is incomplete.\n\n"
                "## Scope\n\n"
                "- Implement targeted behavior\n"
                "- Keep the diff narrow\n\n"
                "## Out of Scope\n\n"
                "- No broad refactors\n\n"
                "## Required Changes\n\n"
                "- Add implementation\n"
                "- Add focused tests\n"
                "  only where needed for this work item\n\n"
                "## Likely Files\n\n"
                "- `src/lrh/example.py`\n"
                "- `tests/example_test.py`\n\n"
                "## Validation\n\n"
                "- Run `scripts/test`\n\n"
                "## Acceptance Criteria\n\n"
                "- Feature works\n"
            ),
            encoding="utf-8",
        )
        return path

    def test_pipeline_generates_expected_sections_for_ready_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_item_path = self._write_work_item(pathlib.Path(temp_dir))

            prompt = work_item_prompt_core.generate_codex_cloud_prompt(
                prompt_id="PROMPT(AD_HOC:TEST)[2026-04-24T20:05:00-04:00]",
                work_item_path=work_item_path,
                style_guide_path="STYLE.md",
            )

            self.assertIn("# ROLE", prompt)
            self.assertIn("# STRICT SCOPE", prompt)
            self.assertIn("# REQUIRED CHANGES", prompt)
            self.assertIn("# DO NOT", prompt)
            self.assertIn("# VALIDATION", prompt)
            self.assertIn("# SUCCESS CRITERIA", prompt)
            self.assertIn("Run `scripts/test`", prompt)
            self.assertIn("Prompt ID: `PROMPT(AD_HOC:TEST)", prompt)
            self.assertIn(
                "Add focused tests only where needed for this work item", prompt
            )

    def test_readiness_blocks_resolved_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_item_path = self._write_work_item(
                pathlib.Path(temp_dir), status="resolved"
            )

            prompt = work_item_prompt_core.generate_codex_cloud_prompt(
                prompt_id="PROMPT(AD_HOC:TEST)[2026-04-24T20:05:00-04:00]",
                work_item_path=work_item_path,
                style_guide_path="STYLE.md",
            )

            self.assertIn("# Work Item Not Ready for Codex Implementation", prompt)
            self.assertIn("status 'resolved' is not implementation-ready", prompt)

    def test_parse_requires_boolean_blocked_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_item_path = pathlib.Path(temp_dir) / "WI-EXAMPLE.md"
            work_item_path.write_text(
                (
                    "---\n"
                    "id: WI-EXAMPLE\n"
                    "title: Example item\n"
                    "type: deliverable\n"
                    "status: proposed\n"
                    'blocked: "false"\n'
                    "---\n\n"
                    "## Summary\n\n"
                    "Body.\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "work item frontmatter field 'blocked' must be a bool"
            ):
                work_item_prompt_core.parse_work_item_markdown(work_item_path)


if __name__ == "__main__":
    unittest.main()
