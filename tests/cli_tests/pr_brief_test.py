import json
import pathlib
import tempfile
import unittest
from unittest import mock

from lrh.cli import pr_brief
from tests import testing_support
from tests.pr_brief_tests import sample_data


class PrBriefRenderCliTest(unittest.TestCase):
    def test_render_writes_briefing_beside_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            data_path = pathlib.Path(temp) / "data.json"
            data_path.write_text(
                json.dumps(sample_data.sample_data()), encoding="utf-8"
            )
            with testing_support.capture_output() as captured:
                code = pr_brief.run_pr_brief_cli(
                    ["render", str(data_path)], prog="lrh pr-brief"
                )
            self.assertEqual(code, 0)
            out_path = pathlib.Path(temp) / "briefing.html"
            self.assertTrue(out_path.is_file())
            self.assertIn("Widgets PR 7 Briefing", out_path.read_text(encoding="utf-8"))
            self.assertIn("0 warning(s)", captured.stdout.getvalue())

    def test_render_check_reports_errors_and_writes_nothing(self) -> None:
        data = sample_data.sample_data()
        data["briefing"]["review_notes"][0]["severity"] = "urgent"
        with tempfile.TemporaryDirectory() as temp:
            data_path = pathlib.Path(temp) / "data.json"
            data_path.write_text(json.dumps(data), encoding="utf-8")
            with testing_support.capture_output() as captured:
                code = pr_brief.run_pr_brief_cli(
                    ["render", str(data_path)], prog="lrh pr-brief"
                )
            self.assertEqual(code, 1)
            self.assertIn("review_notes[0].severity", captured.stderr.getvalue())
            self.assertFalse((pathlib.Path(temp) / "briefing.html").exists())

    def test_render_check_only_validates(self) -> None:
        data = sample_data.sample_data()
        data["briefing"]["headline_summary"] = ""
        with tempfile.TemporaryDirectory() as temp:
            data_path = pathlib.Path(temp) / "data.json"
            data_path.write_text(json.dumps(data), encoding="utf-8")
            with testing_support.capture_output() as captured:
                code = pr_brief.run_pr_brief_cli(
                    ["render", str(data_path), "--check"], prog="lrh pr-brief"
                )
            self.assertEqual(code, 0)
            self.assertIn("ok: 1 warning(s)", captured.stdout.getvalue())
            self.assertFalse((pathlib.Path(temp) / "briefing.html").exists())

    def test_render_rejects_unreadable_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            data_path = pathlib.Path(temp) / "data.json"
            data_path.write_text("{not json", encoding="utf-8")
            with testing_support.suppress_output():
                code = pr_brief.run_pr_brief_cli(
                    ["render", str(data_path)], prog="lrh pr-brief"
                )
            self.assertEqual(code, 2)


class PrBriefGatherCliTest(unittest.TestCase):
    def test_gather_refuses_to_overwrite_authored_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            (pathlib.Path(temp) / "data.json").write_text("{}", encoding="utf-8")
            with (
                mock.patch("lrh.cli.pr_brief.gather.gather_briefing_data") as gather,
                testing_support.capture_output() as captured,
            ):
                code = pr_brief.run_pr_brief_cli(
                    ["gather", "example/widgets", "7", "--out", temp],
                    prog="lrh pr-brief",
                )
            self.assertEqual(code, 1)
            gather.assert_not_called()
            self.assertIn("--force", captured.stderr.getvalue())

    def test_gather_writes_data_and_diff(self) -> None:
        data = sample_data.sample_data()
        with tempfile.TemporaryDirectory() as temp:
            with (
                mock.patch(
                    "lrh.cli.pr_brief.gather.gather_briefing_data",
                    return_value=(data, "diff text\n"),
                ),
                testing_support.capture_output() as captured,
            ):
                code = pr_brief.run_pr_brief_cli(
                    [
                        "gather",
                        "https://github.com/example/widgets/pull/7",
                        "--out",
                        temp,
                    ],
                    prog="lrh pr-brief",
                )
            self.assertEqual(code, 0)
            written = json.loads(
                (pathlib.Path(temp) / "data.json").read_text(encoding="utf-8")
            )
            self.assertEqual(written["pr"]["number"], 7)
            self.assertEqual(
                (pathlib.Path(temp) / "pr.diff").read_text(encoding="utf-8"),
                "diff text\n",
            )
            self.assertIn(
                "trial merge: 1 conflicting file(s)", captured.stdout.getvalue()
            )

    def test_gather_rejects_repo_dir_that_is_not_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with testing_support.capture_output() as captured:
                code = pr_brief.run_pr_brief_cli(
                    [
                        "gather",
                        "example/widgets",
                        "7",
                        "--out",
                        str(pathlib.Path(temp) / "out"),
                        "--repo-dir",
                        str(pathlib.Path(temp) / "missing"),
                    ],
                    prog="lrh pr-brief",
                )
            self.assertEqual(code, 2)
            self.assertIn("not a directory", captured.stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
