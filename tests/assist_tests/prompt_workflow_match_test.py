import pathlib
import tempfile
import unittest

from lrh import prompt_workflow_match


class PromptWorkflowMatchTest(unittest.TestCase):
    def _write_record(
        self,
        project_root: pathlib.Path,
        rel_path: str,
        prompt_id: str,
        status: str = "landed",
    ) -> pathlib.Path:
        path = project_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nprompt_id: {prompt_id}\nwork_item: AD_HOC\nstatus: {status}\n---\n",
            encoding="utf-8",
        )
        return path

    def test_extract_prompt_ids_preserves_order_and_deduplicates(self) -> None:
        first = "PROMPT(AD_HOC:FIRST)[2026-05-06T12:31:00-04:00]"
        second = "PROMPT(WI-TEST:SECOND_TASK)[2026-05-06T13:31:00+00:00]"

        prompt_ids = prompt_workflow_match.extract_prompt_ids(
            f"before {first}\nrepeat {first}\nthen {second}\n"
        )

        self.assertEqual(prompt_ids, [first, second])

    def test_extract_prompt_ids_ignores_partial_or_lowercase_shapes(self) -> None:
        prompt_ids = prompt_workflow_match.extract_prompt_ids(
            "PROMPT(AD_HOC:missing)[2026-05-06T12:31:00-04:00]\n"
            "PROMPT(AD_HOC:VALID_BUT_NO_TIMESTAMP)\n"
        )

        self.assertEqual(prompt_ids, [])

    def test_match_prompt_file_no_prompt_id_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text("No prompt ID here.\n", encoding="utf-8")

            result = prompt_workflow_match.match_prompt_file_to_executions(
                prompt_file,
                project_root=project_root,
            )

        self.assertEqual(result.prompt_ids, [])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "No prompt IDs found", prompt_workflow_match.format_text_result(result)
        )

    def test_match_prompt_file_single_exact_match(self) -> None:
        prompt_id = "PROMPT(AD_HOC:FOUND)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(prompt_id, encoding="utf-8")
            record_path = self._write_record(
                project_root,
                "project/executions/AD_HOC/found.md",
                prompt_id,
            )

            result = prompt_workflow_match.match_prompt_file_to_executions(
                prompt_file,
                project_root=project_root,
            )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.matches[0].match_count, 1)
        self.assertEqual(result.matches[0].check_result.records[0].path, record_path)

    def test_match_prompt_file_no_exact_match(self) -> None:
        prompt_id = "PROMPT(AD_HOC:MISSING)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(prompt_id, encoding="utf-8")

            result = prompt_workflow_match.match_prompt_file_to_executions(
                prompt_file,
                project_root=project_root,
            )

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.matches[0].match_count, 0)
        self.assertIn(
            "no execution records found",
            prompt_workflow_match.format_text_result(result),
        )

    def test_match_prompt_file_multiple_prompt_ids(self) -> None:
        first = "PROMPT(AD_HOC:FIRST)[2026-05-06T12:31:00-04:00]"
        second = "PROMPT(AD_HOC:SECOND)[2026-05-06T12:32:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "package.md"
            prompt_file.write_text(f"{first}\n{second}\n", encoding="utf-8")
            self._write_record(
                project_root, "project/executions/AD_HOC/first.md", first
            )

            result = prompt_workflow_match.match_prompt_file_to_executions(
                prompt_file,
                project_root=project_root,
            )

        self.assertEqual(result.prompt_ids, [first, second])
        self.assertEqual([match.match_count for match in result.matches], [1, 0])
        self.assertEqual(result.exit_code, 1)

    def test_match_prompt_file_ambiguous_duplicate_records(self) -> None:
        prompt_id = "PROMPT(AD_HOC:DUP)[2026-05-06T12:31:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            prompt_file = project_root / "prompt.md"
            prompt_file.write_text(prompt_id, encoding="utf-8")
            self._write_record(
                project_root, "project/executions/AD_HOC/a.md", prompt_id
            )
            self._write_record(
                project_root, "project/executions/AD_HOC/b.md", prompt_id
            )

            result = prompt_workflow_match.match_prompt_file_to_executions(
                prompt_file,
                project_root=project_root,
            )

        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.matches[0].match_count, 2)
        self.assertIn(
            "human review required", prompt_workflow_match.format_text_result(result)
        )


if __name__ == "__main__":
    unittest.main()
