import pathlib
import tempfile
import unittest

from lrh import prompt_workflow_queries, prompt_workflow_records


class PromptWorkflowRecordsTest(unittest.TestCase):
    def test_parse_execution_record_maps_frontmatter_and_body(self) -> None:
        prompt_id = "PROMPT(AD_HOC:PARSE)[2026-05-06T12:30:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "record.md"
            path.write_text(
                "---\n"
                "execution_id: 2026_05_06_123000_PARSE\n"
                f"prompt_id: {prompt_id}\n"
                "work_item: AD_HOC\n"
                "status: landed\n"
                "rerun_of: \n"
                "pr: 12\n"
                "commit: abc123\n"
                "created_at: 2026-05-06T12:30:00-04:00\n"
                "tags: [prompt, execution]\n"
                "---\n\n"
                "# Summary\n\nParsed body text.\n",
                encoding="utf-8",
            )
            record = prompt_workflow_records.parse_execution_record(path)

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.path, path)
        self.assertEqual(record.execution_id, "2026_05_06_123000_PARSE")
        self.assertEqual(record.prompt_id, prompt_id)
        self.assertEqual(record.work_item, "AD_HOC")
        self.assertEqual(record.status, "landed")
        self.assertEqual(record.rerun_of, "")
        self.assertEqual(record.pr, "12")
        self.assertEqual(record.commit, "abc123")
        self.assertEqual(record.created_at, "2026-05-06T12:30:00-04:00")
        self.assertEqual(record.frontmatter["tags"], ["prompt", "execution"])
        self.assertIn("Parsed body text.", record.body)

    def test_load_execution_records_finds_nested_markdown_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            first = project_root / "project/executions/AD_HOC/first.md"
            second = project_root / "project/executions/WI-TEST/nested/second.md"
            ignored = project_root / "project/executions/WI-TEST/notes.txt"
            for path in (first, second, ignored):
                path.parent.mkdir(parents=True, exist_ok=True)
            first.write_text(
                "---\nprompt_id: PROMPT(AD_HOC:FIRST)[2026-05-06T12:00:00-04:00]\n"
                "status: landed\n---\n",
                encoding="utf-8",
            )
            second.write_text(
                "---\nprompt_id: PROMPT(WI-TEST:SECOND)[2026-05-06T12:10:00-04:00]\n"
                "status: in_progress\n---\n",
                encoding="utf-8",
            )
            ignored.write_text("not markdown", encoding="utf-8")

            records = prompt_workflow_records.load_execution_records(project_root)

        self.assertEqual([record.path for record in records], [first, second])

    def test_check_execution_returns_exact_prompt_id_match_only(self) -> None:
        prompt_id = "PROMPT(AD_HOC:EXACT)[2026-05-06T12:00:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            exact = project_root / "project/executions/AD_HOC/exact.md"
            other = project_root / "project/executions/AD_HOC/other.md"
            exact.parent.mkdir(parents=True, exist_ok=True)
            exact.write_text(
                f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            other.write_text(
                "---\nprompt_id: PROMPT(AD_HOC:OTHER)[2026-05-06T12:00:00-04:00]\n"
                "status: landed\n---\n",
                encoding="utf-8",
            )

            result = prompt_workflow_queries.check_execution(project_root, prompt_id)

        self.assertEqual(result.prompt_id, prompt_id)
        self.assertEqual(result.match_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.records[0].path, exact)

    def test_check_execution_no_match_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = prompt_workflow_queries.check_execution(
                temp_dir,
                "PROMPT(AD_HOC:MISSING)[2026-05-06T12:00:00-04:00]",
            )

        self.assertEqual(result.records, [])
        self.assertEqual(result.match_count, 0)
        self.assertEqual(result.exit_code, 1)

    def test_check_execution_records_filters_loaded_records(self) -> None:
        prompt_id = "PROMPT(AD_HOC:LOADED)[2026-05-06T12:00:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            exact = project_root / "project/executions/AD_HOC/exact.md"
            other = project_root / "project/executions/AD_HOC/other.md"
            exact.parent.mkdir(parents=True, exist_ok=True)
            exact.write_text(
                f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            other.write_text(
                "---\nprompt_id: PROMPT(AD_HOC:OTHER)[2026-05-06T12:00:00-04:00]\n"
                "status: landed\n---\n",
                encoding="utf-8",
            )

            records = prompt_workflow_records.load_execution_records(project_root)
            result = prompt_workflow_queries.check_execution_records(
                records=records,
                prompt_id=prompt_id,
            )

        self.assertEqual(result.records[0].path, exact)
        self.assertEqual(result.match_count, 1)
        self.assertEqual(result.exit_code, 0)

    def test_check_execution_multiple_match_exit_code(self) -> None:
        prompt_id = "PROMPT(AD_HOC:DUP)[2026-05-06T12:00:00-04:00]"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            for rel_path in (
                "project/executions/AD_HOC/first.md",
                "project/executions/AD_HOC/nested/second.md",
            ):
                path = project_root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"---\nprompt_id: {prompt_id}\nstatus: landed\n---\n",
                    encoding="utf-8",
                )

            result = prompt_workflow_queries.check_execution(project_root, prompt_id)

        self.assertEqual(result.match_count, 2)
        self.assertEqual(result.exit_code, 2)


if __name__ == "__main__":
    unittest.main()
