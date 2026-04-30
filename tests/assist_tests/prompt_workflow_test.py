import datetime
import pathlib
import unittest

from lrh import prompt_workflow


class PromptWorkflowTest(unittest.TestCase):
    def test_build_prompt_label_keeps_required_shape(self) -> None:
        now = datetime.datetime.fromisoformat("2026-04-29T22:05:00-04:00")
        prompt_id = prompt_workflow.build_prompt_label(
            now=now,
            work_item="WI-TEST",
            slug="create-installed-prompt-cli",
        )
        self.assertEqual(
            prompt_id,
            "PROMPT(WI-TEST:CREATE_INSTALLED_PROMPT_CLI)[2026-04-29T22:05:00-04:00]",
        )

    def test_suggested_execution_path_renders_expected_file_name(self) -> None:
        now = datetime.datetime.fromisoformat("2026-04-29T22:05:00-04:00")
        path = prompt_workflow.suggested_execution_path(
            now=now,
            output_root=pathlib.Path("/tmp/project/executions"),
            work_item="WI-TEST",
            slug="create-installed-prompt-cli",
        )
        self.assertEqual(
            path.as_posix(),
            "/tmp/project/executions/WI-TEST/2026_04_29_22_05_00_CREATE_INSTALLED_PROMPT_CLI.md",
        )

    def test_render_execution_content_includes_front_matter(self) -> None:
        content = prompt_workflow.render_execution_content(
            execution_id="2026_04_29_22_05_00_CREATE_INSTALLED_PROMPT_CLI",
            prompt_id="PROMPT(WI-TEST:CREATE_INSTALLED_PROMPT_CLI)[2026-04-29T22:05:00-04:00]",
            work_item="WI-TEST",
            status="in_progress",
            rerun_of="",
            pr="",
            commit="",
            created_at="2026-04-29T22:05:00-04:00",
        )
        self.assertIn("execution_id: 2026_04_29_22_05_00_CREATE_INSTALLED_PROMPT_CLI", content)
        self.assertIn("status: in_progress", content)
        self.assertIn("# Validation", content)


if __name__ == "__main__":
    unittest.main()
