import pathlib
import tempfile
import unittest

from lrh import prompt_workflow_records, prompt_workflow_search


class PromptWorkflowSearchTest(unittest.TestCase):
    def _write_record(
        self,
        project_root: pathlib.Path,
        rel_path: str,
        *,
        prompt_id: str,
        work_item: str = "AD_HOC",
        status: str = "landed",
        body: str = "",
    ) -> pathlib.Path:
        path = project_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f"execution_id: {path.stem.upper()}\n"
            f"prompt_id: {prompt_id}\n"
            f"work_item: {work_item}\n"
            f"status: {status}\n"
            "---\n\n"
            f"{body}",
            encoding="utf-8",
        )
        return path

    def test_query_matches_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            record_path = self._write_record(
                project_root,
                "project/executions/AD_HOC/found.md",
                prompt_id="PROMPT(AD_HOC:SEARCH_TOPIC)[2026-05-06T12:31:00-04:00]",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records,
                "search_topic",
            )

        self.assertEqual(result.match_count, 1)
        self.assertEqual(result.matches[0].record.path, record_path)
        self.assertIn("frontmatter.prompt_id", result.matches[0].contexts[0])

    def test_query_matches_body_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/body.md",
                prompt_id="PROMPT(AD_HOC:BODY)[2026-05-06T12:31:00-04:00]",
                body="# Summary\n\nValidated snapshot rendering behavior.\n",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records,
                "snapshot rendering",
            )

        self.assertEqual(result.match_count, 1)
        self.assertIn("body:4", result.matches[0].contexts[0])

    def test_no_match_returns_empty_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/record.md",
                prompt_id="PROMPT(AD_HOC:OTHER)[2026-05-06T12:31:00-04:00]",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records,
                "missing",
            )

        self.assertEqual(result.match_count, 0)
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "No execution records matched",
            prompt_workflow_search.format_text_result(result),
        )

    def test_search_is_case_insensitive_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/case.md",
                prompt_id="PROMPT(AD_HOC:CASE)[2026-05-06T12:31:00-04:00]",
                body="Mixed Case Topic\n",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records, "case topic"
            )

        self.assertEqual(result.match_count, 1)

    def test_case_sensitive_search_requires_exact_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/case.md",
                prompt_id="PROMPT(AD_HOC:CASE)[2026-05-06T12:31:00-04:00]",
                body="Mixed Case Topic\n",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            missing = prompt_workflow_search.search_execution_records(
                records,
                "case topic",
                case_sensitive=True,
            )
            found = prompt_workflow_search.search_execution_records(
                records,
                "Case Topic",
                case_sensitive=True,
            )

        self.assertEqual(missing.match_count, 0)
        self.assertEqual(found.match_count, 1)

    def test_status_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/planned.md",
                prompt_id="PROMPT(AD_HOC:PLAN)[2026-05-06T12:31:00-04:00]",
                status="planned",
                body="shared keyword\n",
            )
            self._write_record(
                project_root,
                "project/executions/AD_HOC/landed.md",
                prompt_id="PROMPT(AD_HOC:LAND)[2026-05-06T12:32:00-04:00]",
                status="landed",
                body="shared keyword\n",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records,
                "shared keyword",
                status="planned",
            )

        self.assertEqual(result.match_count, 1)
        self.assertEqual(result.matches[0].record.status, "planned")

    def test_work_item_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/ad_hoc.md",
                prompt_id="PROMPT(AD_HOC:ITEM)[2026-05-06T12:31:00-04:00]",
                work_item="AD_HOC",
                body="filter keyword\n",
            )
            self._write_record(
                project_root,
                "project/executions/WI-SEARCH/item.md",
                prompt_id="PROMPT(WI-SEARCH:ITEM)[2026-05-06T12:32:00-04:00]",
                work_item="WI-SEARCH",
                body="filter keyword\n",
            )
            records = prompt_workflow_records.load_execution_records(project_root)

            result = prompt_workflow_search.search_execution_records(
                records,
                "filter keyword",
                work_item="WI-SEARCH",
            )

        self.assertEqual(result.match_count, 1)
        self.assertEqual(result.matches[0].record.work_item, "WI-SEARCH")

    def test_result_ordering_is_deterministic_by_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            z_path = self._write_record(
                project_root,
                "project/executions/AD_HOC/z.md",
                prompt_id="PROMPT(AD_HOC:ZED)[2026-05-06T12:31:00-04:00]",
                body="ordering keyword\n",
            )
            a_path = self._write_record(
                project_root,
                "project/executions/AD_HOC/a.md",
                prompt_id="PROMPT(AD_HOC:ALPHA)[2026-05-06T12:32:00-04:00]",
                body="ordering keyword\n",
            )
            records = [
                prompt_workflow_records.parse_execution_record(z_path),
                prompt_workflow_records.parse_execution_record(a_path),
            ]

            result = prompt_workflow_search.search_execution_records(
                [record for record in records if record is not None],
                "ordering keyword",
            )

        self.assertEqual(
            [match.record.path for match in result.matches],
            [a_path, z_path],
        )


if __name__ == "__main__":
    unittest.main()
