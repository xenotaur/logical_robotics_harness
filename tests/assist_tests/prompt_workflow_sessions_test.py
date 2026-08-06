import json
import pathlib
import tempfile
import unittest
import unittest.mock

from lrh import prompt_workflow_sessions


class SessionIndexTest(unittest.TestCase):
    def test_missing_index_loads_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(records, {})

    def test_first_observation_writes_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="4c3d03d6-abcd-1234-abcd-1234567890ab",
                child_id="child-1",
                title="Implement Stage 1",
                pr="https://github.com/x/y/pull/1",
                branch="feat/x",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            self.assertEqual(
                path,
                pathlib.Path(tmp) / "project" / "sessions" / "index.jsonl",
            )
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["host_id"], "4c3d03d6-abcd-1234-abcd-1234567890ab")
            self.assertEqual(data["child_ids"], ["child-1"])
            self.assertEqual(data["title"], "Implement Stage 1")
            self.assertEqual(data["prs"], ["https://github.com/x/y/pull/1"])
            self.assertEqual(data["branch"], "feat/x")
            self.assertEqual(data["written_branches"], [])
            self.assertEqual(data["updated_at"], "2026-08-06T00:00:00+00:00")

    def test_second_observation_merges_child_ids_and_prs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-a",
                child_id="child-1",
                pr="https://github.com/x/y/pull/1",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            path = prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-a",
                child_id="child-2",
                pr="https://github.com/x/y/pull/2",
                updated_at="2026-08-06T01:00:00+00:00",
            )
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(len(records), 1)
            record = records["host-a"]
            self.assertEqual(record.child_ids, ("child-1", "child-2"))
            self.assertEqual(
                record.prs,
                (
                    "https://github.com/x/y/pull/1",
                    "https://github.com/x/y/pull/2",
                ),
            )
            self.assertEqual(record.updated_at, "2026-08-06T01:00:00+00:00")
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1, "same host_id must not duplicate a row")

    def test_no_child_id_leaves_alias_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-cross-session",
                pr="https://github.com/x/y/pull/9",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(records["host-cross-session"].child_ids, ())

    def test_title_and_branch_latest_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-b",
                title="Old title",
                branch="old-branch",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-b",
                title="New title",
                branch="new-branch",
                updated_at="2026-08-06T01:00:00+00:00",
            )
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(records["host-b"].title, "New title")
            self.assertEqual(records["host-b"].branch, "new-branch")

    def test_omitted_title_keeps_previous_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-c",
                title="Kept title",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-c",
                child_id="child-only",
                updated_at="2026-08-06T01:00:00+00:00",
            )
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(records["host-c"].title, "Kept title")
            self.assertEqual(records["host-c"].child_ids, ("child-only",))

    def test_written_branches_union_and_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-d",
                written_branches=["branch-b", "branch-a"],
                updated_at="2026-08-06T00:00:00+00:00",
            )
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-d",
                written_branches=["branch-c"],
                updated_at="2026-08-06T01:00:00+00:00",
            )
            records = prompt_workflow_sessions.load_session_index(tmp)
            self.assertEqual(
                records["host-d"].written_branches,
                ("branch-a", "branch-b", "branch-c"),
            )

    def test_index_is_sorted_by_host_id_for_stable_diffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp, host_id="zeta", updated_at="2026-08-06T00:00:00+00:00"
            )
            path = prompt_workflow_sessions.record_session_observation(
                tmp, host_id="alpha", updated_at="2026-08-06T00:00:01+00:00"
            )
            lines = path.read_text(encoding="utf-8").splitlines()
            host_ids = [json.loads(line)["host_id"] for line in lines]
            self.assertEqual(host_ids, ["alpha", "zeta"])

    def test_written_branches_key_is_snake_case(self) -> None:
        # Regression: docs/docstrings must never drift to the proposal's
        # own camelCase writtenBranches[] vocabulary -- the actual JSON key
        # and CLI flag are snake_case.
        with tempfile.TemporaryDirectory() as tmp:
            path = prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-e",
                written_branches=["b"],
                updated_at="2026-08-06T00:00:00+00:00",
            )
            data = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            self.assertIn("written_branches", data)
            self.assertNotIn("writtenBranches", data)

    def test_interrupted_write_never_truncates_existing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-first",
                child_id="child-first",
                updated_at="2026-08-06T00:00:00+00:00",
            )
            path = prompt_workflow_sessions.index_path(tmp)
            original_content = path.read_text(encoding="utf-8")

            with unittest.mock.patch(
                "lrh.prompt_workflow_sessions.os.replace",
                side_effect=OSError("simulated interruption"),
            ):
                with self.assertRaises(OSError):
                    prompt_workflow_sessions.record_session_observation(
                        tmp,
                        host_id="host-second",
                        child_id="child-second",
                        updated_at="2026-08-06T01:00:00+00:00",
                    )

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                original_content,
                "a failed replace must leave the previous complete index intact",
            )
            leftover_temp_files = [
                p
                for p in pathlib.Path(tmp, "project", "sessions").iterdir()
                if p.name != "index.jsonl"
            ]
            self.assertEqual(
                leftover_temp_files,
                [],
                "the temp file must be cleaned up even when the replace fails",
            )

    def test_empty_host_id_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                prompt_workflow_sessions.record_session_observation(
                    tmp, host_id="", updated_at="2026-08-06T00:00:00+00:00"
                )


if __name__ == "__main__":
    unittest.main()
