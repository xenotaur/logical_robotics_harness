import json
import os
import pathlib
import tempfile
import unittest
import unittest.mock
import zipfile

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


class ArchiveRootTest(unittest.TestCase):
    def test_override_wins(self) -> None:
        with unittest.mock.patch.dict(
            "os.environ", {"LRH_SESSION_ARCHIVE_ROOT": "/env/root"}
        ):
            self.assertEqual(
                prompt_workflow_sessions.resolve_archive_root("/override/root"),
                pathlib.Path("/override/root"),
            )

    def test_env_var_used_when_no_override(self) -> None:
        with unittest.mock.patch.dict(
            "os.environ", {"LRH_SESSION_ARCHIVE_ROOT": "/env/root"}
        ):
            self.assertEqual(
                prompt_workflow_sessions.resolve_archive_root(),
                pathlib.Path("/env/root"),
            )

    def test_default_used_when_neither_set(self) -> None:
        with unittest.mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                prompt_workflow_sessions.resolve_archive_root(),
                prompt_workflow_sessions.default_archive_root(),
            )


class DiscoverTranscriptsTest(unittest.TestCase):
    def test_finds_nested_jsonl_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "proj-a").mkdir()
            (root / "proj-a" / "s1.jsonl").write_text("{}\n")
            (root / "proj-b").mkdir()
            (root / "proj-b" / "s2.jsonl").write_text("{}\n")
            (root / "proj-a" / "not-jsonl.txt").write_text("x")
            found = prompt_workflow_sessions.discover_transcripts(root)
            self.assertEqual(
                sorted(item.path.name for item in found), ["s1.jsonl", "s2.jsonl"]
            )
            self.assertEqual(
                sorted((item.slug, str(item.relative_path)) for item in found),
                [
                    ("proj-a", "s1.jsonl"),
                    ("proj-b", "s2.jsonl"),
                ],
            )

    def test_top_level_symlinked_transcripts_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            root = tmp_path / "claude-projects"
            project_dir = root / "proj-a"
            outside_dir = tmp_path / "outside"
            project_dir.mkdir(parents=True)
            outside_dir.mkdir()
            external_file = outside_dir / "external.jsonl"
            external_file.write_text("{}\n")
            (project_dir / "safe.jsonl").write_text("{}\n")
            (project_dir / "linked.jsonl").symlink_to(external_file)

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                [(item.slug, str(item.relative_path)) for item in found],
                [("proj-a", "safe.jsonl")],
            )

    def test_symlinked_project_directories_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            root = tmp_path / "claude-projects"
            project_dir = root / "proj-a"
            outside_dir = tmp_path / "outside-project"
            project_dir.mkdir(parents=True)
            outside_dir.mkdir()
            (project_dir / "safe.jsonl").write_text("{}\n")
            (outside_dir / "external.jsonl").write_text("{}\n")
            (root / "linked-project").symlink_to(outside_dir, target_is_directory=True)

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                [(item.slug, str(item.relative_path)) for item in found],
                [("proj-a", "safe.jsonl")],
            )

    def test_missing_root_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            found = prompt_workflow_sessions.discover_transcripts(
                pathlib.Path(tmp) / "does-not-exist"
            )
            self.assertEqual(found, [])

    def test_discovers_nested_files_under_owning_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            session_dir = project_dir / "child-1"
            (session_dir / "subagents").mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text("{}\n")
            (session_dir / "subagents" / "sub.jsonl").write_text("{}\n")
            (session_dir / "subagents" / "sub.meta.json").write_text("{}\n")

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                sorted((item.slug, str(item.relative_path)) for item in found),
                [
                    ("proj-a", "child-1.jsonl"),
                    ("proj-a", "child-1/subagents/sub.jsonl"),
                    (
                        "proj-a",
                        "child-1/subagents/sub.meta.json",
                    ),
                ],
            )

    def test_nested_cross_bucket_uses_owning_top_level_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            owner_dir = root / "live-proj"
            stale_dir = root / "stale-proj"
            (owner_dir).mkdir()
            nested_dir = stale_dir / "child-1" / "tool-results"
            nested_dir.mkdir(parents=True)
            (owner_dir / "child-1.jsonl").write_text("{}\n")
            (nested_dir / "result.txt").write_text("result\n")

            found = prompt_workflow_sessions.discover_transcripts(root)

            nested = [
                item
                for item in found
                if item.relative_path == pathlib.Path("child-1/tool-results/result.txt")
            ]
            self.assertEqual(len(nested), 1)
            self.assertEqual(nested[0].slug, "live-proj")
            self.assertEqual(nested[0].path, nested_dir / "result.txt")

    def test_uuid_orphaned_session_id_directory_is_kept_but_memory_is_excluded(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            orphan_session_id = "f1e9c968-4f52-45a3-a851-8d28d2eb775d"
            orphan_dir = project_dir / orphan_session_id / "subagents"
            memory_dir = project_dir / "memory"
            cache_dir = project_dir / "cache123"
            orphan_dir.mkdir(parents=True)
            memory_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)
            (orphan_dir / "sub.jsonl").write_text("{}\n")
            (memory_dir / "not-a-session.jsonl").write_text("{}\n")
            (cache_dir / "not-a-session.jsonl").write_text("{}\n")

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                [(item.slug, str(item.relative_path)) for item in found],
                [("proj-a", f"{orphan_session_id}/subagents/sub.jsonl")],
            )

    def test_hex_like_non_session_directory_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            cache_dir = project_dir / "12345678"
            cache_dir.mkdir(parents=True)
            (cache_dir / "not-a-session.jsonl").write_text("{}\n")

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(found, [])

    def test_nested_symlinked_files_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            session_dir = project_dir / "child-1" / "tool-results"
            external_dir = root / "outside"
            session_dir.mkdir(parents=True)
            external_dir.mkdir()
            (project_dir / "child-1.jsonl").write_text("{}\n")
            external_file = external_dir / "secret.txt"
            external_file.write_text("secret\n")
            (session_dir / "leak.txt").symlink_to(external_file)
            (session_dir / "result.txt").write_text("result\n")

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                sorted((item.slug, str(item.relative_path)) for item in found),
                [
                    ("proj-a", "child-1.jsonl"),
                    ("proj-a", "child-1/tool-results/result.txt"),
                ],
            )

    def test_nested_symlinked_directories_are_not_descended(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            session_dir = project_dir / "child-1"
            external_dir = root / "outside"
            (session_dir / "tool-results").mkdir(parents=True)
            external_dir.mkdir()
            (project_dir / "child-1.jsonl").write_text("{}\n")
            (session_dir / "tool-results" / "result.txt").write_text("result\n")
            (external_dir / "secret.txt").write_text("secret\n")
            (session_dir / "linked-dir").symlink_to(
                external_dir, target_is_directory=True
            )

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                sorted((item.slug, str(item.relative_path)) for item in found),
                [
                    ("proj-a", "child-1.jsonl"),
                    ("proj-a", "child-1/tool-results/result.txt"),
                ],
            )

    def test_symlinked_session_directories_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_dir = root / "proj-a"
            outside_dir = root / "outside-session"
            project_dir.mkdir()
            outside_dir.mkdir()
            (project_dir / "child-1.jsonl").write_text("{}\n")
            (outside_dir / "secret.txt").write_text("secret\n")
            (project_dir / "child-1").symlink_to(outside_dir, target_is_directory=True)

            found = prompt_workflow_sessions.discover_transcripts(root)

            self.assertEqual(
                [(item.slug, str(item.relative_path)) for item in found],
                [("proj-a", "child-1.jsonl")],
            )


class MirrorTranscriptTest(unittest.TestCase):
    def test_first_mirror_copies_bytes_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b'{"sessionId": "a"}\n')
            result = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertTrue(result.copied)
            self.assertEqual(result.dest.read_bytes(), source.read_bytes())
            self.assertEqual(
                result.dest, archive_root / "raw" / "proj" / "source.jsonl"
            )

    def test_unchanged_source_is_not_recopied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b'{"sessionId": "a"}\n')
            prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            second = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertFalse(second.copied)

    def test_grown_source_is_recopied_completely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b'{"sessionId": "a"}\n')
            first = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertTrue(first.copied)
            # Simulate the source growing while the session stays active --
            # mtime must also advance for the growth to be detected on
            # filesystems with coarse mtime resolution.
            source.write_bytes(b'{"sessionId": "a"}\n{"sessionId": "b"}\n')
            os.utime(source, (source.stat().st_mtime + 5, source.stat().st_mtime + 5))
            second = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertTrue(second.copied)
            self.assertEqual(second.dest.read_bytes(), source.read_bytes())

    def test_archived_copy_never_shrinks(self) -> None:
        """A source that is smaller than the already-archived copy (should
        never happen for an append-only transcript, but is the safety
        property the append-safety requirement actually guarantees) must
        never cause the archived copy to shrink."""

        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b'{"sessionId": "a"}\n{"sessionId": "b"}\n')
            first = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            archived_content = first.dest.read_bytes()
            # A shorter "source" now, with an older mtime than the archived
            # copy -- neither condition alone should trigger a re-copy.
            source.write_bytes(b'{"sessionId": "a"}\n')
            os.utime(source, (1, 1))
            second = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertFalse(second.copied)
            self.assertEqual(second.dest.read_bytes(), archived_content)

    def test_shrunk_source_with_newer_mtime_still_never_shrinks_archive(
        self,
    ) -> None:
        """Regression: a source that is smaller but has a *newer* mtime than
        the archived copy (a rewrite, truncation, or restore-from-backup)
        must still never shrink the archive -- mtime alone must not be able
        to defeat the size floor."""

        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b"x" * 80)
            first = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertEqual(first.dest.stat().st_size, 80)
            source.write_bytes(b"x" * 8)
            os.utime(
                source,
                (source.stat().st_mtime + 100, source.stat().st_mtime + 100),
            )
            second = prompt_workflow_sessions.mirror_transcript(
                source, archive_root, project_slug="proj"
            )
            self.assertFalse(second.copied)
            self.assertEqual(second.dest.stat().st_size, 80)

    def test_relative_path_preserves_nested_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            source = pathlib.Path(tmp) / "source.meta.json"
            source.write_bytes(b'{"sidecar": true}\n')

            result = prompt_workflow_sessions.mirror_transcript(
                source,
                archive_root,
                project_slug="proj",
                relative_path=pathlib.Path("child-1") / "subagents" / source.name,
            )

            self.assertTrue(result.copied)
            self.assertEqual(
                result.dest,
                archive_root / "raw" / "proj" / "child-1" / "subagents" / source.name,
            )
            self.assertEqual(result.dest.read_bytes(), source.read_bytes())

    def test_unsafe_relative_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = pathlib.Path(tmp) / "source.jsonl"
            source.write_bytes(b"{}\n")

            with self.assertRaises(ValueError):
                prompt_workflow_sessions.mirror_transcript(
                    source,
                    pathlib.Path(tmp) / "archive",
                    project_slug="proj",
                    relative_path=pathlib.Path("..") / "escape.jsonl",
                )


class CollectChildIdAliasesTest(unittest.TestCase):
    def test_collects_every_distinct_line_level_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "f1e9c968.jsonl"
            path.write_text(
                '{"sessionId": "aff3efd3"}\n'
                '{"sessionId": "aff3efd3"}\n'
                '{"sessionId": "f1e9c968"}\n'
            )
            aliases = prompt_workflow_sessions.collect_child_id_aliases(path)
            self.assertEqual(aliases, {"aff3efd3", "f1e9c968"})

    def test_malformed_lines_are_skipped_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "f.jsonl"
            path.write_text('{"sessionId": "a"}\nnot json\n\n{"sessionId": "b"}\n')
            aliases = prompt_workflow_sessions.collect_child_id_aliases(path)
            self.assertEqual(aliases, {"a", "b"})

    def test_missing_file_returns_empty_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            aliases = prompt_workflow_sessions.collect_child_id_aliases(
                pathlib.Path(tmp) / "missing.jsonl"
            )
            self.assertEqual(aliases, set())


def _write_export_zip(
    path: pathlib.Path,
    metadata: dict,
    *,
    include_logs: bool = True,
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        archive.writestr("transcript.jsonl", '{"sessionId": "unused"}\n')
        if include_logs:
            archive.writestr("logs/main.log", "log content")


class HarvestExportMetadataTest(unittest.TestCase):
    def test_extracts_only_identity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = pathlib.Path(tmp) / "export.zip"
            _write_export_zip(
                zip_path,
                {
                    "sessionId": "local_abc",
                    "cliSessionId": "def",
                    "prNumber": 1,
                    "prs": [{"url": "https://example.com/pull/1"}],
                    "branch": "feat/x",
                    "title": "A title",
                    "cwd": "/should/not/appear",
                    "model": "should-not-appear",
                },
            )
            metadata = prompt_workflow_sessions.harvest_export_metadata(zip_path)
            self.assertEqual(
                metadata,
                {
                    "sessionId": "local_abc",
                    "cliSessionId": "def",
                    "prNumber": 1,
                    "prs": [{"url": "https://example.com/pull/1"}],
                    "branch": "feat/x",
                    "title": "A title",
                },
            )
            self.assertNotIn("cwd", metadata)
            self.assertNotIn("model", metadata)

    def test_missing_metadata_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = pathlib.Path(tmp) / "export.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("transcript.jsonl", "{}\n")
            with self.assertRaises(prompt_workflow_sessions.ExportMetadataError):
                prompt_workflow_sessions.harvest_export_metadata(zip_path)

    def test_bad_zip_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = pathlib.Path(tmp) / "export.zip"
            zip_path.write_bytes(b"not a zip file")
            with self.assertRaises(prompt_workflow_sessions.ExportMetadataError):
                prompt_workflow_sessions.harvest_export_metadata(zip_path)

    def test_never_lists_or_extracts_logs(self) -> None:
        """Verified by construction: only metadata.json is opened, so a
        zip whose logs/ entry would raise if read still harvests cleanly."""

        with tempfile.TemporaryDirectory() as tmp:
            zip_path = pathlib.Path(tmp) / "export.zip"
            _write_export_zip(zip_path, {"sessionId": "local_a"})
            metadata = prompt_workflow_sessions.harvest_export_metadata(zip_path)
            self.assertEqual(metadata, {"sessionId": "local_a"})


class SessionKeyFromMetadataTest(unittest.TestCase):
    def test_strips_local_prefix(self) -> None:
        self.assertEqual(
            prompt_workflow_sessions.session_key_from_metadata(
                {"sessionId": "local_abc-123"}
            ),
            "abc-123",
        )

    def test_missing_session_id_returns_none(self) -> None:
        self.assertIsNone(prompt_workflow_sessions.session_key_from_metadata({}))


class ExportPrUrlsTest(unittest.TestCase):
    def test_extracts_all_urls(self) -> None:
        urls = prompt_workflow_sessions.export_pr_urls(
            {
                "prs": [
                    {"url": "https://example.com/pull/1"},
                    {"url": "https://example.com/pull/2"},
                ]
            }
        )
        self.assertEqual(
            urls, ["https://example.com/pull/1", "https://example.com/pull/2"]
        )

    def test_missing_prs_returns_empty(self) -> None:
        self.assertEqual(prompt_workflow_sessions.export_pr_urls({}), [])

    def test_malformed_entries_skipped(self) -> None:
        urls = prompt_workflow_sessions.export_pr_urls(
            {"prs": ["not-a-dict", {"no_url": True}, {"url": "https://x/pull/9"}]}
        )
        self.assertEqual(urls, ["https://x/pull/9"])


class PersistExportMetadataTest(unittest.TestCase):
    def test_writes_sorted_json_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_root = pathlib.Path(tmp) / "archive"
            dest = prompt_workflow_sessions.persist_export_metadata(
                archive_root, "abc-123", {"sessionId": "local_abc-123"}
            )
            self.assertEqual(
                dest, archive_root / "exports" / "abc-123" / "metadata.json"
            )
            self.assertEqual(
                json.loads(dest.read_text()), {"sessionId": "local_abc-123"}
            )


class SyncExportTest(unittest.TestCase):
    def test_full_harvest_populates_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"
            zip_path = pathlib.Path(tmp) / "session-export-1.zip"
            _write_export_zip(
                zip_path,
                {
                    "sessionId": "local_host-1",
                    "cliSessionId": "child-1",
                    "prs": [
                        {"url": "https://example.com/pull/1"},
                        {"url": "https://example.com/pull/2"},
                    ],
                    "branch": "feat/x",
                    "title": "Title",
                },
            )
            record = prompt_workflow_sessions.sync_export(
                project_root,
                archive_root,
                zip_path,
                updated_at="2026-08-07T00:00:00+00:00",
            )
            self.assertIsNotNone(record)
            self.assertEqual(record.host_id, "host-1")
            self.assertEqual(record.child_ids, ("child-1",))
            self.assertEqual(
                record.prs,
                ("https://example.com/pull/1", "https://example.com/pull/2"),
            )
            self.assertEqual(record.branch, "feat/x")
            self.assertEqual(record.title, "Title")
            # The sanitized metadata copy is persisted for Stage 3 recovery.
            self.assertTrue(
                (archive_root / "exports" / "host-1" / "metadata.json").exists()
            )

    def test_no_host_id_persists_metadata_but_skips_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"
            zip_path = pathlib.Path(tmp) / "session-export-1.zip"
            _write_export_zip(zip_path, {"cliSessionId": "child-1"})
            record = prompt_workflow_sessions.sync_export(
                project_root,
                archive_root,
                zip_path,
                updated_at="2026-08-07T00:00:00+00:00",
            )
            self.assertIsNone(record)
            self.assertFalse(prompt_workflow_sessions.index_path(project_root).exists())
            # Still persisted under the zip's own stem so the harvest is not
            # silently lost even without a resolvable host id.
            self.assertTrue(
                (
                    archive_root / "exports" / "session-export-1" / "metadata.json"
                ).exists()
            )


class ProjectSlugForPathTest(unittest.TestCase):
    def test_slashes_and_dots_become_hyphens_underscore_preserved(self) -> None:
        # Verified against real ~/.claude/projects/ directory names: `/`
        # and `.` are both replaced with `-`, but `_` is preserved as-is
        # (e.g. a `replication_vector` repo keeps its underscore intact,
        # while a `.claude/worktrees/...` segment becomes
        # `-claude-worktrees-...`).
        slug = prompt_workflow_sessions.project_slug_for_path("/a/b_c/d.e")
        self.assertNotIn("/", slug)
        self.assertIn("_", slug)
        self.assertTrue(slug.startswith("-a-b_c-d-e"))


class DiscoverSessionsForProjectTest(unittest.TestCase):
    def test_lists_transcripts_and_resolves_known_host_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            slug = prompt_workflow_sessions.project_slug_for_path(project_root)
            project_dir = claude_projects_root / slug
            project_dir.mkdir(parents=True)
            (project_dir / "child-1.jsonl").write_text('{"sessionId": "child-1"}\n')

            prompt_workflow_sessions.record_session_observation(
                project_root,
                host_id="host-1",
                child_id="child-1",
                updated_at="2026-08-07T00:00:00+00:00",
            )

            sessions = prompt_workflow_sessions.discover_sessions_for_project(
                project_root, claude_projects_root
            )
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].child_id, "child-1")
            self.assertEqual(sessions[0].host_id, "host-1")

    def test_unresolved_session_has_none_host_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "proj"
            claude_projects_root = pathlib.Path(tmp) / "claude-projects"
            slug = prompt_workflow_sessions.project_slug_for_path(project_root)
            project_dir = claude_projects_root / slug
            project_dir.mkdir(parents=True)
            (project_dir / "unknown.jsonl").write_text("{}\n")

            sessions = prompt_workflow_sessions.discover_sessions_for_project(
                project_root, claude_projects_root
            )
            self.assertEqual(len(sessions), 1)
            self.assertIsNone(sessions[0].host_id)

    def test_missing_project_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sessions = prompt_workflow_sessions.discover_sessions_for_project(
                pathlib.Path(tmp) / "proj", pathlib.Path(tmp) / "claude-projects"
            )
            self.assertEqual(sessions, [])


class ReconcileChildIdAliasesTest(unittest.TestCase):
    def test_adds_new_alias_for_already_known_host(self) -> None:
        """The PR #435 case: a transcript named after one child id contains
        an in-file sessionId belonging to no filename anywhere. Once either
        alias is already linked to a host, the other must be folded in."""

        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-1",
                child_id="f1e9c968",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            jsonl_path = pathlib.Path(tmp) / "f1e9c968.jsonl"
            jsonl_path.write_text(
                '{"sessionId": "aff3efd3"}\n{"sessionId": "f1e9c968"}\n'
            )
            result = prompt_workflow_sessions.reconcile_child_id_aliases(
                tmp, jsonl_path, updated_at="2026-08-07T01:00:00+00:00"
            )
            self.assertEqual(result, ("host-1", frozenset({"aff3efd3"})))
            record = prompt_workflow_sessions.load_session_index(tmp)["host-1"]
            self.assertEqual(record.child_ids, ("aff3efd3", "f1e9c968"))

    def test_no_known_alias_is_a_noop(self) -> None:
        """Raw JSONL alone cannot establish a *new* host id -- with no
        alias already in the index, this must not guess or invent one."""

        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = pathlib.Path(tmp) / "unknown.jsonl"
            jsonl_path.write_text('{"sessionId": "unknown-child"}\n')
            result = prompt_workflow_sessions.reconcile_child_id_aliases(
                tmp, jsonl_path, updated_at="2026-08-07T00:00:00+00:00"
            )
            self.assertIsNone(result)
            self.assertEqual(prompt_workflow_sessions.load_session_index(tmp), {})

    def test_ambiguous_across_two_hosts_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-1",
                child_id="child-a",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-2",
                child_id="child-b",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            jsonl_path = pathlib.Path(tmp) / "mixed.jsonl"
            jsonl_path.write_text(
                '{"sessionId": "child-a"}\n{"sessionId": "child-b"}\n'
            )
            result = prompt_workflow_sessions.reconcile_child_id_aliases(
                tmp, jsonl_path, updated_at="2026-08-07T01:00:00+00:00"
            )
            self.assertIsNone(result)

    def test_already_fully_known_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-1",
                child_id="only-child",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            jsonl_path = pathlib.Path(tmp) / "only-child.jsonl"
            jsonl_path.write_text('{"sessionId": "only-child"}\n')
            result = prompt_workflow_sessions.reconcile_child_id_aliases(
                tmp, jsonl_path, updated_at="2026-08-07T01:00:00+00:00"
            )
            self.assertIsNone(result)

    def test_empty_transcript_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jsonl_path = pathlib.Path(tmp) / "empty.jsonl"
            jsonl_path.write_text("")
            result = prompt_workflow_sessions.reconcile_child_id_aliases(
                tmp, jsonl_path, updated_at="2026-08-07T00:00:00+00:00"
            )
            self.assertIsNone(result)


class ResolveHostIdForChildTest(unittest.TestCase):
    def test_resolves_known_child_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-1",
                child_id="child-1",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            self.assertEqual(
                prompt_workflow_sessions.resolve_host_id_for_child(tmp, "child-1"),
                "host-1",
            )

    def test_unknown_child_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(prompt_workflow_sessions.LinkLookupError):
                prompt_workflow_sessions.resolve_host_id_for_child(tmp, "nope")

    def test_ambiguous_child_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-1",
                child_id="shared-child",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            prompt_workflow_sessions.record_session_observation(
                tmp,
                host_id="host-2",
                child_id="shared-child",
                updated_at="2026-08-07T00:00:00+00:00",
            )
            with self.assertRaises(prompt_workflow_sessions.LinkLookupError):
                prompt_workflow_sessions.resolve_host_id_for_child(tmp, "shared-child")


if __name__ == "__main__":
    unittest.main()
