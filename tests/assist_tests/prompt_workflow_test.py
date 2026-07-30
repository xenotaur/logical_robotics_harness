import contextlib
import datetime
import io
import os
import pathlib
import tempfile
import time
import unittest
import unittest.mock

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
                "---\nprompt_id: PROMPT(AD_HOC:OTHER)"
                "[2026-05-01T17:40:00-04:00]\nstatus: landed\n---\n",
                encoding="utf-8",
            )
            matches = prompt_workflow.find_matching_execution_records(
                str(project_root),
                "PROMPT(AD_HOC:MISSING)[2026-05-01T17:40:00-04:00]",
                "project/executions",
            )
        self.assertEqual(matches, [])

    def test_label_timestamp_is_utc_regardless_of_local_timezone(self) -> None:
        # Regression test for prompt_workflow.py:299: `now` must be a UTC
        # instant with no local-timezone conversion, or filename/prompt-ID
        # timestamps stop sorting chronologically across machines/DST.
        #
        # Freezes the clock to a known instant so this asserts the actual
        # offset-free filename/execution_id segment (the value the
        # original bug corrupted), not just the prompt_id's ISO offset --
        # a prompt_id-only check could pass even if the filename timestamp
        # regressed to local time while prompt_id stayed correct, since
        # they're formatted independently (isoformat vs strftime).
        fixed_instant = datetime.datetime(
            2026, 3, 4, 5, 6, 7, tzinfo=datetime.timezone.utc
        )

        class _FrozenDatetime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return fixed_instant
                return fixed_instant.astimezone(tz)

        original_tz = os.environ.get("TZ")
        try:
            outputs = []
            with tempfile.TemporaryDirectory() as temp_dir:
                for tz in ("America/New_York", "Asia/Kolkata"):
                    os.environ["TZ"] = tz
                    time.tzset()
                    buffer = io.StringIO()
                    with unittest.mock.patch(
                        "lrh.prompt_workflow.datetime.datetime", _FrozenDatetime
                    ):
                        with contextlib.redirect_stdout(buffer):
                            prompt_workflow.run_prompt_cli(
                                [
                                    "label",
                                    "--slug",
                                    "utc-timestamp-test",
                                    "--project-root",
                                    temp_dir,
                                ]
                            )
                    outputs.append(buffer.getvalue())
        finally:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            time.tzset()

        # Both TZ settings must produce byte-identical output -- proving
        # the filename/execution_id/prompt_id are unaffected by local
        # timezone -- and the filename segment must match the fixed
        # instant's UTC wall-clock value, not a timezone-shifted one.
        self.assertEqual(outputs[0], outputs[1])
        for output in outputs:
            self.assertIn(
                "AD_HOC/2026_03_04_05_06_07_UTC_TIMESTAMP_TEST.md",
                output,
            )
            self.assertIn("[2026-03-04T05:06:07+00:00]", output)

    def test_parse_front_matter_fields_requires_closing_delimiter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "missing_close.md"
            path.write_text(
                "---\nprompt_id: PROMPT(AD_HOC:BODY_REF)[2026-05-01T17:40:00-04:00]\n"
                "status: landed\n"
                "Body references prompt_id:"
                " PROMPT(AD_HOC:BODY_REF)[2026-05-01T17:40:00-04:00]\n",
                encoding="utf-8",
            )
            fields = prompt_workflow.parse_front_matter_fields(path)
        self.assertEqual(fields, {})


if __name__ == "__main__":
    unittest.main()
