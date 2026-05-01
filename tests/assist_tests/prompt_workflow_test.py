import datetime
import pathlib
import tempfile
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
        self.assertIn(
            "execution_id: 2026_04_29_22_05_00_CREATE_INSTALLED_PROMPT_CLI",
            content,
        )
        self.assertIn("status: in_progress", content)
        self.assertIn("# Validation", content)

    def test_find_matching_execution_records_finds_flat_and_grouped(self) -> None:
        prompt_id = "PROMPT(AD_HOC:CHECK_EXEC)[2026-05-01T17:40:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            flat_path = project_root / "project/executions/2026_05_01_A.md"
            grouped_path = project_root / "project/executions/AD_HOC/2026_05_01_B.md"
            flat_path.parent.mkdir(parents=True, exist_ok=True)
            grouped_path.parent.mkdir(parents=True, exist_ok=True)
            flat_path.write_text(
                "---\nprompt_id: " + prompt_id + "\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            grouped_path.write_text(
                "---\nprompt_id: " + prompt_id + "\nstatus: in_progress\n---\n",
                encoding="utf-8",
            )
            matches = prompt_workflow.find_matching_execution_records(
                str(project_root), prompt_id, "project/executions"
            )
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][0].as_posix(), flat_path.as_posix())
        self.assertEqual(matches[1][0].as_posix(), grouped_path.as_posix())

    def test_find_matching_execution_records_returns_empty_for_unknown_prompt_id(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            record_path = project_root / "project/executions/AD_HOC/2026_05_01_A.md"
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(
                "---\nprompt_id: PROMPT(AD_HOC:OTHER)[2026-05-01T17:40:00-04:00]\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            matches = prompt_workflow.find_matching_execution_records(
                str(project_root),
                "PROMPT(AD_HOC:MISSING)[2026-05-01T17:40:00-04:00]",
                "project/executions",
            )
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
