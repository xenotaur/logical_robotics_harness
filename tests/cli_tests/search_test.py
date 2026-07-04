import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


class SearchCliTest(unittest.TestCase):
    def _repo_root(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def _write_record(
        self,
        project_root: pathlib.Path,
        rel_path: str,
        *,
        prompt_id: str = "PROMPT(AD_HOC:SEARCH)[2026-05-06T12:31:00-04:00]",
        work_item: str = "AD_HOC",
        status: str = "landed",
        body: str = "Searchable validation summary.\n",
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

    def test_lrh_search_executions_returns_text_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(project_root, "project/executions/AD_HOC/search.md")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "search",
                    "executions",
                    "validation summary",
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("matches: 1", completed.stdout)
        self.assertIn("project/executions/AD_HOC/search.md", completed.stdout)
        self.assertIn(
            "mode: exploratory substring search; "
            "not authoritative for soft idempotence decisions",
            completed.stdout,
        )
        self.assertEqual(completed.stderr, "")

    def test_lrh_search_executions_empty_query_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(project_root, "project/executions/AD_HOC/search.md")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "search",
                    "executions",
                    "",
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 2, msg=completed.stderr)
        self.assertIn("error: query must not be empty", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_lrh_search_executions_no_match_returns_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(project_root, "project/executions/AD_HOC/search.md")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "search",
                    "executions",
                    "missing",
                    "--project-root",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 1, msg=completed.stderr)
        self.assertIn("No execution records matched", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_lrh_search_executions_supports_filters_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/ad_hoc.md",
                status="landed",
                work_item="AD_HOC",
                body="shared cli keyword\n",
            )
            self._write_record(
                project_root,
                "project/executions/WI-SEARCH/planned.md",
                prompt_id="PROMPT(WI-SEARCH:SEARCH)[2026-05-06T12:32:00-04:00]",
                status="planned",
                work_item="WI-SEARCH",
                body="shared cli keyword\n",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "search",
                    "executions",
                    "shared cli keyword",
                    "--project-root",
                    temp_dir,
                    "--status",
                    "planned",
                    "--work-item",
                    "WI-SEARCH",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["match_count"], 1)
        self.assertFalse(payload["authoritative_for_idempotence"])
        self.assertEqual(payload["records"][0]["status"], "planned")
        self.assertEqual(payload["records"][0]["work_item"], "WI-SEARCH")

    def test_lrh_search_executions_respects_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "custom/executions/AD_HOC/search.md",
                body="custom output root\n",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lrh.cli.main",
                    "search",
                    "executions",
                    "custom output root",
                    "--project-root",
                    temp_dir,
                    "--output-root",
                    "custom/executions",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                cwd=self._repo_root(),
            )

        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("custom/executions/AD_HOC/search.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
