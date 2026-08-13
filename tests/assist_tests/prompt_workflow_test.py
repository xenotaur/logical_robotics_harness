import contextlib
import datetime
import io
import json
import pathlib
import tempfile
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
        #
        # Deliberately does NOT vary the process's local timezone (no
        # os.environ["TZ"]/time.tzset()): time.tzset is POSIX-only and
        # raises AttributeError on Windows, which this package supports
        # (pyproject.toml declares OS Independent).
        #
        # The mock must distinguish "the fixed code's call shape"
        # (`datetime.datetime.now(datetime.timezone.utc)`, no further
        # conversion) from "the removed buggy code's call shape" (the
        # same call, then a *separate* bare `.astimezone()` with no
        # argument, which converts to the system's local timezone) --
        # not just return the same fixed value regardless of which
        # happens, which was this test's original mistake: `now()`
        # forwarded its `tz` argument straight into
        # `fixed_instant.astimezone(tz)`, so on a UTC-configured host
        # (common in CI) the removed bug's trailing bare `.astimezone()`
        # call would *also* have been a no-op, making the test pass
        # against the exact behavior it was meant to catch. `astimezone`
        # is overridden separately so a no-argument call -- the buggy
        # code's exact shape -- returns a deliberately different,
        # deterministic value regardless of the host's real system
        # timezone, while `now()` itself always returns the correct
        # fixed instant.
        class _FrozenDatetime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                # Constructed via `cls(...)`, not the plain
                # `datetime.datetime(...)` constructor -- the returned
                # object must actually be a `_FrozenDatetime` instance for
                # the `astimezone` override below to apply to it at all.
                # (A first version of this fix built the fixed instant
                # with the plain constructor before patching and returned
                # that same object from every call; since it was never
                # actually an instance of this subclass, calling
                # `.astimezone()` on it silently fell through to the real
                # unpatched method instead of the override below --
                # verified directly: it returned a real, host-timezone-
                # shifted value instead of the deliberately-wrong sentinel,
                # meaning the trap would not have fired.)
                return cls(2026, 3, 4, 5, 6, 7, tzinfo=datetime.timezone.utc)

            def astimezone(self, tz=None):
                if tz is None:
                    return datetime.datetime(
                        2020, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
                    )
                return super().astimezone(tz)

        with tempfile.TemporaryDirectory() as temp_dir:
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
            output = buffer.getvalue()

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

    def test_record_session_alias_cli_writes_index_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = prompt_workflow.run_prompt_cli(
                    [
                        "record-session-alias",
                        "--host-id",
                        "cli-host-1",
                        "--child-id",
                        "cli-child-1",
                        "--pr",
                        "https://github.com/x/y/pull/5",
                        "--project-root",
                        temp_dir,
                    ]
                )
            output = buffer.getvalue()
            self.assertEqual(exit_code, 0)
            index_path = pathlib.Path(temp_dir) / "project" / "sessions" / "index.jsonl"
            self.assertIn(index_path.as_posix(), output)
            data = json.loads(index_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(data["host_id"], "cli-host-1")
            self.assertEqual(data["child_ids"], ["cli-child-1"])
            self.assertEqual(data["prs"], ["https://github.com/x/y/pull/5"])

    def test_record_session_alias_cli_requires_host_id(self) -> None:
        buffer = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(buffer):
                prompt_workflow.run_prompt_cli(["record-session-alias"])


class WriteSessionTranscriptFieldTest(unittest.TestCase):
    def test_replaces_existing_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "r.md"
            path.write_text(
                "---\n"
                "execution_id: R\n"
                "commit: abc123\n"
                "session_transcript: pending\n"
                "---\n\n# Summary\n"
            )
            prompt_workflow.write_session_transcript_field(path, "host-1")
            self.assertIn("session_transcript: claude-app:host-1", path.read_text())

    def test_inserts_after_commit_when_field_is_missing(self) -> None:
        """Regression: a record with no session_transcript: field at all
        must still get the field written -- not silently left unchanged
        while the caller believes it succeeded."""

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "r.md"
            original = "---\nexecution_id: R\ncommit: abc123\n---\n\n# Summary\n"
            path.write_text(original)
            prompt_workflow.write_session_transcript_field(path, "host-1")
            result = path.read_text()
            self.assertNotEqual(result, original)
            self.assertIn("session_transcript: claude-app:host-1", result)
            # Inserted directly after commit:, not appended anywhere else.
            self.assertIn(
                "commit: abc123\nsession_transcript: claude-app:host-1", result
            )

    def test_raises_when_neither_field_nor_anchor_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "r.md"
            original = "---\nexecution_id: R\n---\n\n# Summary\n"
            path.write_text(original)
            with self.assertRaises(prompt_workflow.SessionTranscriptWriteError):
                prompt_workflow.write_session_transcript_field(path, "host-1")
            # Must not silently succeed -- and must not have written
            # anything either, since the raise happens before the file write.
            self.assertEqual(path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
