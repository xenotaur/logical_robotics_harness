import concurrent.futures
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock

from lrh import prompt_workflow_memory
from lrh.prompt_workflow_sessions import project_slug_for_path


class WriteMemoryTest(unittest.TestCase):
    def test_write_creates_file_and_index_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            project_root.mkdir()

            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo-bar",
                description="a test memory",
                type_="feedback",
                agent="claude",
                body="body text\n",
                claude_projects_root=claude_root,
            )

            self.assertTrue(result.memory_path.exists())
            self.assertEqual(result.memory_path.name, "feedback_foo_bar.md")
            self.assertTrue(result.index_updated)
            content = result.memory_path.read_text(encoding="utf-8")
            self.assertIn("name: feedback-foo-bar", content)
            self.assertIn("description: a test memory", content)
            self.assertIn("metadata:", content)
            self.assertIn("  type: feedback", content)
            self.assertIn("  authored_by: claude", content)
            self.assertIn("body text", content)

            index_content = result.index_path.read_text(encoding="utf-8")
            self.assertIn("feedback_foo_bar.md", index_content)

    def test_write_rejects_invalid_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.write_memory(
                    pathlib.Path(tmp) / "proj",
                    "feedback-foo",
                    description="d",
                    type_="not-a-real-type",
                    agent="claude",
                    body="b",
                    claude_projects_root=pathlib.Path(tmp) / "claude-projects",
                )

    def test_write_rejects_empty_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.write_memory(
                    pathlib.Path(tmp) / "proj",
                    "feedback-foo",
                    description="   ",
                    type_="feedback",
                    agent="claude",
                    body="b",
                    claude_projects_root=pathlib.Path(tmp) / "claude-projects",
                )

    def test_write_rejects_non_kebab_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.write_memory(
                    pathlib.Path(tmp) / "proj",
                    "Not_Kebab_Case",
                    description="d",
                    type_="feedback",
                    agent="claude",
                    body="b",
                    claude_projects_root=pathlib.Path(tmp) / "claude-projects",
                )

    def test_second_write_refuses_cross_agent_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-contested",
                description="codex's memory",
                type_="feedback",
                agent="codex",
                body="codex body",
                claude_projects_root=claude_root,
            )

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.write_memory(
                    project_root,
                    "feedback-contested",
                    description="claude overwrites",
                    type_="feedback",
                    agent="claude",
                    body="claude body",
                    claude_projects_root=claude_root,
                )

            # force=True succeeds
            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-contested",
                description="claude overwrites",
                type_="feedback",
                agent="claude",
                body="claude body",
                claude_projects_root=claude_root,
                force=True,
            )
            content = result.memory_path.read_text(encoding="utf-8")
            self.assertIn("authored_by: claude", content)

    def test_write_index_no_op_when_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="a test memory",
                type_="feedback",
                agent="claude",
                body="body",
                claude_projects_root=claude_root,
            )
            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="a test memory",
                type_="feedback",
                agent="claude",
                body="updated body",
                claude_projects_root=claude_root,
                force=True,
            )
            self.assertFalse(result.index_updated)

    def test_write_escapes_colon_in_description(self) -> None:
        """A description containing a colon must not corrupt the YAML.

        Regression test: an earlier draft hand-interpolated frontmatter
        values into an f-string with no escaping, so
        `--description 'Rule: retain evidence'` produced
        `description: Rule: retain evidence` -- a second, unintended
        top-level YAML key-value pair that `yaml.safe_load` rejects on
        read-back.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-colon-desc",
                description="Rule: retain evidence",
                type_="feedback",
                agent="claude",
                body="body",
                claude_projects_root=claude_root,
            )
            frontmatter, _ = prompt_workflow_memory.read_frontmatter_and_body(
                result.memory_path.read_text(encoding="utf-8")
            )
            self.assertEqual(frontmatter["description"], "Rule: retain evidence")

    def test_write_escapes_embedded_newline_in_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-newline-agent",
                description="d",
                type_="feedback",
                agent="claude\nmetadata:\n  authored_by: injected",
                body="body",
                claude_projects_root=claude_root,
            )
            frontmatter, _ = prompt_workflow_memory.read_frontmatter_and_body(
                result.memory_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                frontmatter["metadata"]["authored_by"],
                "claude\nmetadata:\n  authored_by: injected",
            )

    def test_concurrent_writes_do_not_lose_index_entries(self) -> None:
        """Two concurrent writers to different names must both land in the index.

        Regression test: an earlier draft's index read-modify-write had
        no locking, so two concurrent `write_memory` calls could each
        read the same MEMORY.md, append only their own entry, and
        atomically replace it -- the later replacement silently dropping
        the earlier caller's entry even though both memory files were
        written successfully.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            names = [f"feedback-concurrent-{i}" for i in range(12)]

            def _write(name: str) -> None:
                prompt_workflow_memory.write_memory(
                    project_root,
                    name,
                    description="d",
                    type_="feedback",
                    agent="claude",
                    body="body",
                    claude_projects_root=claude_root,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                list(pool.map(_write, names))

            entries = prompt_workflow_memory.list_memories(
                project_root, claude_projects_root=claude_root
            )
            indexed_filenames = {e.filename for e in entries}
            expected = {prompt_workflow_memory.filename_for(n) for n in names}
            self.assertEqual(indexed_filenames, expected)

    def test_write_resolves_corpus_path_via_project_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            result = prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="b",
                claude_projects_root=claude_root,
            )
            slug = project_slug_for_path(project_root)
            expected = claude_root / slug / "memory" / "feedback_foo.md"
            self.assertEqual(result.memory_path, expected)


class ListMemoriesTest(unittest.TestCase):
    def test_list_empty_when_no_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entries = prompt_workflow_memory.list_memories(
                pathlib.Path(tmp) / "proj",
                claude_projects_root=pathlib.Path(tmp) / "claude-projects",
            )
            self.assertEqual(entries, [])

    def test_list_filters_by_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-a",
                description="a",
                type_="feedback",
                agent="claude",
                body="b",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-b",
                description="b",
                type_="feedback",
                agent="codex",
                body="b",
                claude_projects_root=claude_root,
            )

            claude_entries = prompt_workflow_memory.list_memories(
                project_root, claude_projects_root=claude_root, agent="claude"
            )
            self.assertEqual(len(claude_entries), 1)
            self.assertEqual(claude_entries[0].filename, "feedback_a.md")

            all_entries = prompt_workflow_memory.list_memories(
                project_root, claude_projects_root=claude_root
            )
            self.assertEqual(len(all_entries), 2)

    def test_list_skips_path_traversal_index_entries(self) -> None:
        """A crafted index line must never resolve outside the memory dir.

        Regression test: an earlier draft did `memory_dir / filename` for
        whatever string the ``(...)`` link target contained, so a crafted
        or corrupted `MEMORY.md` line like `[x](../../secret.md)` would
        read an arbitrary accessible file. Also covers the related
        "no match at all" case, which previously appended a bogus
        empty-filename entry instead of skipping the line.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            outside = pathlib.Path(tmp) / "outside"
            outside.mkdir()
            (outside / "secret.md").write_text(
                "---\nname: secret\ndescription: d\nmetadata:\n"
                "  type: feedback\n  authored_by: codex\n---\n\nSECRET\n",
                encoding="utf-8",
            )
            (memory_dir / "MEMORY.md").write_text(
                "# Memory Index\n"
                "- [traversal](../../outside/secret.md) — d\n"
                "- [malformed link with no closing target\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.list_memories(
                project_root, claude_projects_root=claude_root
            )
            self.assertEqual(entries, [])


class ValidateCorpusTest(unittest.TestCase):
    def test_validate_empty_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = prompt_workflow_memory.validate_corpus(
                pathlib.Path(tmp) / "proj",
                claude_projects_root=pathlib.Path(tmp) / "claude-projects",
            )
            self.assertEqual(report.malformed, ())
            self.assertEqual(report.legacy, ())
            self.assertEqual(report.conforming, ())

    def test_validate_distinguishes_malformed_legacy_conforming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)

            (memory_dir / "conforming.md").write_text(
                "---\n"
                "name: conforming\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: claude\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )
            (memory_dir / "legacy.md").write_text(
                "---\n"
                "name: legacy\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )
            (memory_dir / "malformed.md").write_text(
                "---\nname: malformed\n---\n\nbody\n",
                encoding="utf-8",
            )
            (memory_dir / "unindexed.md").write_text(
                "---\n"
                "name: unindexed\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: claude\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )
            (memory_dir / "MEMORY.md").write_text(
                "# Memory Index\n"
                "- [conforming](conforming.md) — d\n"
                "- [legacy](legacy.md) — d\n",
                encoding="utf-8",
            )

            report = prompt_workflow_memory.validate_corpus(
                project_root, claude_projects_root=claude_root
            )
            self.assertEqual(report.conforming, ("conforming.md",))
            self.assertEqual(report.legacy, ("legacy.md",))
            self.assertEqual(report.malformed, ("malformed.md",))
            self.assertEqual(report.unindexed, ("unindexed.md",))


class RepairMemoryTest(unittest.TestCase):
    def test_repair_requires_authored_by_when_none_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy.md").write_text(
                "---\nname: legacy\ndescription: d\nmetadata:\n"
                "  type: feedback\n---\n\nbody\n",
                encoding="utf-8",
            )

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.repair_memory(
                    project_root,
                    "legacy",
                    sets={},
                    claude_projects_root=claude_root,
                )

    def test_repair_preserves_existing_authored_by_when_not_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "codex_authored.md").write_text(
                "---\n"
                "name: codex-authored\n"
                "description: original\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "---\n\noriginal body\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "codex-authored",
                sets={"description": "patched"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")
            self.assertIn("authored_by: codex", content)
            self.assertIn("description: patched", content)
            self.assertIn("original body", content)

    def test_repair_never_touches_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "codex_authored.md").write_text(
                "---\n"
                "name: codex-authored\n"
                "description: original\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "---\n\nunique body sentinel text\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "codex-authored",
                sets={"metadata.authored_by": "claude"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")
            self.assertIn("unique body sentinel text", content)
            self.assertIn("authored_by: claude", content)

    def test_repair_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            original = (
                "---\n"
                "name: codex-authored\n"
                "description: original\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "---\n\nbody\n"
            )
            (memory_dir / "codex_authored.md").write_text(original, encoding="utf-8")

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "codex-authored",
                sets={"description": "would change"},
                claude_projects_root=claude_root,
                dry_run=True,
            )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_repair_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.repair_memory(
                    pathlib.Path(tmp) / "proj",
                    "does-not-exist",
                    sets={},
                    claude_projects_root=pathlib.Path(tmp) / "claude-projects",
                )

    def test_repair_rejects_path_traversal_name(self) -> None:
        """A `name` with path segments must never escape the memory dir.

        Regression test: an earlier draft only validated `name` in
        `write_memory`, not `repair_memory`, letting a `../`-laden
        `--set`-style name resolve outside the corpus and read an
        arbitrary accessible `.md` file's frontmatter/body into it.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            outside_dir = pathlib.Path(tmp) / "outside"
            outside_dir.mkdir()
            (outside_dir / "secret.md").write_text(
                "---\n"
                "name: secret\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "---\n\nSECRET BODY CONTENTS\n",
                encoding="utf-8",
            )

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.repair_memory(
                    project_root,
                    "../../../outside/secret.md",
                    sets={"description": "PWNED"},
                    claude_projects_root=claude_root,
                )

            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            if memory_dir.exists():
                self.assertNotIn("secret.md", [p.name for p in memory_dir.glob("*.md")])

    def test_repair_rejects_set_name(self) -> None:
        """`--set name=<new>` must be rejected, not silently orphan the original.

        Regression test: an earlier draft let `--set name=<new>` write a
        *new* file+index entry under the new name via `write_memory`
        without ever removing the original file or its old index entry,
        leaving a stale duplicate behind.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-original",
                description="d",
                type_="feedback",
                agent="claude",
                body="b",
                claude_projects_root=claude_root,
            )

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.repair_memory(
                    project_root,
                    "feedback-original",
                    sets={"name": "feedback-renamed"},
                    claude_projects_root=claude_root,
                )

    def test_repair_handles_non_mapping_metadata_without_crashing(self) -> None:
        """A malformed `metadata: broken` value must raise, not crash.

        Regression test: `dict(frontmatter.get("metadata") or {})` raises
        `TypeError`, not `MemoryValidationError`, when `metadata` is a
        non-mapping scalar -- the CLI only catches the latter, so this
        repair scenario used to end in an unhandled traceback instead of
        the intended clean error (or, with `--set metadata.type=...`
        supplied, a successful recovery).
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "broken_meta.md").write_text(
                "---\nname: broken-meta\ndescription: d\n"
                "metadata: broken\n---\n\nbody\n",
                encoding="utf-8",
            )

            # No fields supplied to recover with: raises cleanly, not a TypeError.
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.repair_memory(
                    project_root,
                    "broken-meta",
                    sets={},
                    claude_projects_root=claude_root,
                )

            # Supplying the missing fields recovers the file successfully.
            path = prompt_workflow_memory.repair_memory(
                project_root,
                "broken-meta",
                sets={
                    "metadata.type": "feedback",
                    "metadata.authored_by": "claude",
                },
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")
            self.assertIn("authored_by: claude", content)

    def test_repair_fixes_unindexed_file(self) -> None:
        """Repairing an unindexed-but-complete file adds its missing index entry.

        This is the crash state Decision 4's write ordering intentionally
        permits (memory file written, MEMORY.md rename interrupted) --
        `repair` closes it by re-running `write`'s own path, which adds
        the missing index line as a side effect of the ordinary write.
        """

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "feedback_orphan.md").write_text(
                "---\n"
                "name: feedback-orphan\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: claude\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )

            report_before = prompt_workflow_memory.validate_corpus(
                project_root, claude_projects_root=claude_root
            )
            self.assertEqual(report_before.unindexed, ("feedback_orphan.md",))

            prompt_workflow_memory.repair_memory(
                project_root,
                "feedback-orphan",
                sets={},
                claude_projects_root=claude_root,
            )

            report_after = prompt_workflow_memory.validate_corpus(
                project_root, claude_projects_root=claude_root
            )
            self.assertEqual(report_after.unindexed, ())
            self.assertIn("feedback_orphan.md", report_after.conforming)

    def test_repair_preserves_claude_code_auto_memory_metadata(self) -> None:
        """Regression for WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA: repair must
        not drop unknown frontmatter keys when backfilling authored_by on a
        legacy, Claude-Code-auto-memory-authored file. This test fails
        without the fix: the pre-fix _render_memory_file emits only name/
        description/metadata.{type,authored_by,applies_to}, silently
        discarding node_type/originSessionId/modified."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            original = (
                "---\n"
                "name: feedback-gh-api-jq-arg-flag\n"
                "description: gh api --jq does not accept a separate --arg flag\n"
                "metadata: \n"
                "  node_type: memory\n"
                "  type: feedback\n"
                "  originSessionId: 0f1bccdb-af9f-45df-bcbe-7151730fd643\n"
                "  modified: 2026-08-19T04:27:39.225Z\n"
                "---\n\nbody text here\n"
            )
            (memory_dir / "feedback_gh_api_jq_arg_flag.md").write_text(
                original, encoding="utf-8"
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "feedback-gh-api-jq-arg-flag",
                sets={"metadata.authored_by": "claude_app"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")

            self.assertIn("authored_by: claude_app", content)
            self.assertIn("  node_type: memory\n", content)
            self.assertIn(
                "  originSessionId: 0f1bccdb-af9f-45df-bcbe-7151730fd643\n", content
            )
            # Byte-for-byte: a YAML parse-then-safe_dump round trip would
            # instead rewrite this to "2026-08-19 04:27:39.225000+00:00".
            self.assertIn("  modified: 2026-08-19T04:27:39.225Z\n", content)
            self.assertIn("body text here", content)

    def test_repair_preserves_extras_in_both_positions(self) -> None:
        """Regression: a preserved top-level key ordered BEFORE ``metadata:``
        in the source, combined with a preserved metadata-nested key, must
        not corrupt the output. An earlier version of the fix concatenated
        both preserved groups into one flat, appended list regardless of
        where they belonged, which placed the metadata-nested line after
        the top-level line -- outside the ``metadata:`` mapping -- and the
        result failed to re-parse at all (``mapping values are not
        allowed here``)."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy.md").write_text(
                "---\n"
                "name: legacy\n"
                "custom: before\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  node_type: memory\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "legacy",
                sets={"metadata.authored_by": "claude_app"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")

            # Must re-parse -- this is the assertion the pre-fix version failed.
            frontmatter, _ = prompt_workflow_memory.read_frontmatter_and_body(content)
            self.assertEqual(frontmatter["custom"], "before")
            self.assertEqual(frontmatter["metadata"]["node_type"], "memory")
            self.assertEqual(frontmatter["metadata"]["authored_by"], "claude_app")

    def test_repair_preserves_an_unknown_top_level_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy.md").write_text(
                "---\n"
                "name: legacy\n"
                "description: d\n"
                "custom_top_level: keep-me\n"
                "metadata:\n"
                "  type: feedback\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "legacy",
                sets={"metadata.authored_by": "claude_app"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")

            self.assertIn("custom_top_level: keep-me", content)
            self.assertIn("authored_by: claude_app", content)

    def test_repair_preserved_keys_cannot_shadow_canonical_fields(self) -> None:
        """A same-named extra key (however it got there) must never win over
        the canonical value repair computes."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy.md").write_text(
                "---\n"
                "name: legacy\n"
                "description: d\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: sneaky\n"
                "  node_type: memory\n"
                "---\n\nbody\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "legacy",
                sets={"metadata.authored_by": "claude_app"},
                claude_projects_root=claude_root,
            )
            content = path.read_text(encoding="utf-8")

            self.assertIn("authored_by: claude_app", content)
            self.assertNotIn("authored_by: sneaky", content)
            self.assertEqual(content.count("authored_by:"), 1)
            self.assertIn("node_type: memory", content)

    def test_repair_output_unchanged_for_canonical_only_frontmatter(self) -> None:
        """No unknown keys to preserve -> byte-identical to today's output."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            slug = project_slug_for_path(project_root)
            memory_dir = claude_root / slug / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "codex_authored.md").write_text(
                "---\n"
                "name: codex-authored\n"
                "description: original\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "---\n\noriginal body\n",
                encoding="utf-8",
            )

            path = prompt_workflow_memory.repair_memory(
                project_root,
                "codex-authored",
                sets={"description": "patched"},
                claude_projects_root=claude_root,
            )

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "---\n"
                "name: codex-authored\n"
                "description: patched\n"
                "metadata:\n"
                "  type: feedback\n"
                "  authored_by: codex\n"
                "  applies_to:\n"
                "  - codex\n"
                "---\n\noriginal body\n",
            )


class ExtractPreservedFrontmatterLinesTest(unittest.TestCase):
    def test_no_unknown_keys_returns_empty(self) -> None:
        text = (
            "name: x\ndescription: d\nmetadata:\n"
            "  type: feedback\n  authored_by: claude_app\n"
        )
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, [])
        self.assertEqual(metadata, [])

    def test_preserves_top_level_and_nested_unknown_keys_verbatim_and_separately(
        self,
    ) -> None:
        """Top-level and metadata-nested preserved lines come back as two
        separate lists -- see the regression this guards in
        RepairMemoryTest.test_repair_preserves_extras_in_both_positions."""

        text = (
            "name: x\ndescription: d\ncustom: kept\nmetadata:\n"
            "  type: feedback\n  node_type: memory\n"
            "  modified: 2026-08-19T04:27:39.225Z\n"
        )
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, ["custom: kept"])
        self.assertEqual(
            metadata,
            ["  node_type: memory", "  modified: 2026-08-19T04:27:39.225Z"],
        )

    def test_rejects_a_top_level_block_sequence_value(self) -> None:
        """A list written at the key's own indentation (`tags:\\n- a\\n- b`,
        ordinary and common YAML style) must be rejected, not silently
        dropped -- a line-based split cannot safely re-nest it."""

        text = "name: x\ndescription: d\ntags:\n- a\n- b\nmetadata:\n  type: feedback\n"
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_a_metadata_nested_block_sequence_value(self) -> None:
        text = (
            "name: x\ndescription: d\nmetadata:\n  type: feedback\n"
            "  tags:\n  - a\n  - b\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_flow_style_metadata_with_inline_content(self) -> None:
        text = (
            "name: x\ndescription: d\nmetadata: {type: feedback, node_type: memory}\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_accepts_a_non_mapping_metadata_scalar(self) -> None:
        """`metadata: broken` (a non-mapping scalar) has no extra keys to
        preserve -- it is not the flow-mapping case above and must not
        raise; `repair_memory` recovers from it separately."""

        text = "name: x\ndescription: d\nmetadata: broken\n"
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, [])
        self.assertEqual(metadata, [])

    def test_preserves_a_null_scalar_unknown_key(self) -> None:
        """A key with no value on its own line (`custom:` alone, ordinary
        YAML for a null scalar) is a genuine single-line value -- it must
        be preserved verbatim, not rejected as an unrepresentable nested
        block."""

        text = (
            "name: x\ndescription: d\ncustom:\nmetadata:\n  type: feedback\n  weird:\n"
        )
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, ["custom:"])
        self.assertEqual(metadata, ["  weird:"])

    def test_preserves_single_line_flow_collection_values(self) -> None:
        """A flow-style list or mapping that fits on the key's own line is
        a single-line value like any other -- it is preserved verbatim,
        not rejected (only a value that continues onto further lines is)."""

        text = (
            "name: x\ndescription: d\ntags: [a, b]\nmetadata:\n"
            "  type: feedback\n  extra: {x: 1}\n"
        )
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, ["tags: [a, b]"])
        self.assertEqual(metadata, ["  extra: {x: 1}"])

    def test_rejects_a_block_scalar_value(self) -> None:
        text = (
            "name: x\ndescription: d\nnote: |\n  line one\n  line two\n"
            "metadata:\n  type: feedback\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_a_block_sequence_with_an_internal_blank_line(self) -> None:
        """Regression: a blank line inside a block sequence (valid YAML --
        `tags:\\n\\n- a\\n- b` parses identically to the no-blank form) must
        not terminate the block scan early. An earlier version of the fix
        stopped scanning at the blank line, silently dropping the
        sequence items that came after it instead of raising."""

        text = (
            "name: x\ndescription: d\ntags:\n\n- a\n- b\n"
            "metadata:\n  type: feedback\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_a_metadata_nested_block_sequence_with_an_internal_blank_line(
        self,
    ) -> None:
        text = (
            "name: x\ndescription: d\nmetadata:\n  type: feedback\n"
            "  tags:\n\n  - a\n  - b\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_a_block_sequence_interrupted_by_a_comment_line(self) -> None:
        """Regression: a comment line between a key and its block-sequence
        items (valid YAML -- PyYAML ignores the comment the same way it
        ignores a blank line) must not terminate the block scan early,
        the same way a blank-line interruption must not."""

        text = (
            "name: x\ndescription: d\ntags:\n# a comment\n- a\n- b\n"
            "metadata:\n  type: feedback\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_preserves_a_null_scalar_followed_by_a_comment_line(self) -> None:
        text = (
            "name: x\ndescription: d\ncustom:\n# a comment\n"
            "metadata:\n  type: feedback\n"
        )
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, ["custom:"])
        self.assertEqual(metadata, [])

    def test_rejects_a_duplicate_top_level_unknown_key(self) -> None:
        """A duplicate key is already ambiguous YAML -- a parser silently
        keeps only the last occurrence. Splicing both lines through
        verbatim would reproduce that silent collapse in the output with
        no warning, so this must raise instead."""

        text = (
            "name: x\ndescription: d\ncustom: first\ncustom: second\n"
            "metadata:\n  type: feedback\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_rejects_a_duplicate_metadata_nested_unknown_key(self) -> None:
        text = (
            "name: x\ndescription: d\nmetadata:\n  type: feedback\n"
            "  custom: first\n  custom: second\n"
        )
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)

    def test_preserves_a_null_scalar_followed_by_a_blank_line(self) -> None:
        """A genuinely single-line null scalar followed by a blank line
        before the next key must not be misclassified as multi-line --
        the blank line does not belong to it."""

        text = "name: x\ndescription: d\ncustom:\n\nmetadata:\n  type: feedback\n"
        top_level, metadata = (
            prompt_workflow_memory._extract_preserved_frontmatter_lines(text)
        )
        self.assertEqual(top_level, ["custom:"])
        self.assertEqual(metadata, [])


class ReadFrontmatterAndBodyTest(unittest.TestCase):
    def test_parses_nested_metadata_mapping(self) -> None:
        text = (
            "---\n"
            "name: foo\n"
            "description: bar\n"
            "metadata:\n"
            "  type: feedback\n"
            "  authored_by: claude\n"
            "  applies_to:\n"
            "    - claude\n"
            "    - codex\n"
            "---\n\nbody text\n"
        )
        frontmatter, body = prompt_workflow_memory.read_frontmatter_and_body(text)
        self.assertEqual(frontmatter["name"], "foo")
        self.assertEqual(frontmatter["metadata"]["type"], "feedback")
        self.assertEqual(frontmatter["metadata"]["applies_to"], ["claude", "codex"])
        self.assertEqual(body, "body text\n")

    def test_body_has_no_spurious_leading_newline(self) -> None:
        """Regression test: the blank separator line after the closing
        `---` must not become part of the returned body -- a prior draft
        included it, so every read body carried one extra leading newline
        relative to what `write_memory`/`_render_memory_file` actually
        wrote (which always `.strip("\\n")`s the body)."""

        text = (
            "---\nname: foo\ndescription: d\nmetadata:\n"
            "  type: feedback\n  authored_by: claude\n---\n\nbody text\n"
        )
        _, body = prompt_workflow_memory.read_frontmatter_and_body(text)
        self.assertEqual(body, "body text\n")
        self.assertFalse(body.startswith("\n"))

    def test_missing_opening_delimiter_raises(self) -> None:
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory.read_frontmatter_and_body("no frontmatter here")

    def test_missing_closing_delimiter_raises(self) -> None:
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory.read_frontmatter_and_body("---\nname: foo\n")


class SyncMemoryTest(unittest.TestCase):
    def test_sync_mirrors_corpus_into_archive_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v1\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
            )

            self.assertEqual(len(entries), 2)  # feedback_foo.md + MEMORY.md
            for entry in entries:
                self.assertTrue(entry.copied)
                self.assertIsNone(entry.snapshot)
                self.assertEqual(entry.dest.read_bytes(), entry.source.read_bytes())

            slug = project_slug_for_path(project_root)
            expected_dest = archive_root / "raw" / slug / "memory" / "feedback_foo.md"
            self.assertTrue(expected_dest.exists())

    def test_sync_is_a_no_op_when_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
            )

            second_run = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
            )

            self.assertTrue(all(not entry.copied for entry in second_run))

    def test_sync_snapshots_prior_content_before_overwrite_and_never_deletes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v1\n",
                claude_projects_root=claude_root,
            )
            first_run = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
                timestamp="20260101T000000Z",
            )
            memory_file = next(
                e.dest for e in first_run if e.dest.name == "feedback_foo.md"
            )

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v2, edited and shorter\n",
                claude_projects_root=claude_root,
                force=True,
            )
            second_run = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
                timestamp="20260102T000000Z",
            )

            entry = next(e for e in second_run if e.dest.name == "feedback_foo.md")
            self.assertTrue(entry.copied)
            self.assertIsNotNone(entry.snapshot)
            self.assertTrue(entry.snapshot.exists())
            self.assertIn("20260102T000000Z", entry.snapshot.name)
            self.assertIn("body v1", entry.snapshot.read_text(encoding="utf-8"))

            # Regression test: the snapshot filename must not double the
            # `.md` extension (e.g. `feedback_foo.md.<ts>.<hash>.md`) --
            # exactly one `.md` suffix, derived from dest.stem/dest.suffix.
            self.assertEqual(entry.snapshot.suffix, ".md")
            self.assertNotIn(".md.", entry.snapshot.name[:-3])
            self.assertTrue(entry.snapshot.name.startswith("feedback_foo."))
            self.assertIn("body v2", memory_file.read_text(encoding="utf-8"))

    def test_sync_mirrors_a_shrunk_file_rather_than_blocking_it(self) -> None:
        """Decision 6: snapshot-before-overwrite, not mirror_transcript's
        never-shrink invariant -- a smaller edited memory (e.g. via
        consolidate-memory) must be mirrored, not refused."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="a much longer original body with lots of detail\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
            )

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="short\n",
                claude_projects_root=claude_root,
                force=True,
            )
            second_run = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
            )

            entry = next(e for e in second_run if e.dest.name == "feedback_foo.md")
            self.assertTrue(entry.copied)
            self.assertIn("short", entry.dest.read_text(encoding="utf-8"))

    def test_sync_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v1\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
                dry_run=True,
            )

            self.assertTrue(all(entry.copied for entry in entries))
            self.assertFalse(archive_root.exists())

    def test_sync_is_empty_when_corpus_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entries = prompt_workflow_memory.sync_memory(
                pathlib.Path(tmp) / "proj",
                claude_projects_root=pathlib.Path(tmp) / "claude-projects",
                archive_root=pathlib.Path(tmp) / "archive",
            )
            self.assertEqual(entries, [])

    def test_sync_rejects_archive_root_nested_under_memory_corpus(self) -> None:
        """Regression test: an archive root inside the memory corpus would
        have its own mirrored output picked up by the next run's rglob,
        re-mirroring it one level deeper every run without ever converging."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            memory_dir = prompt_workflow_memory.memory_dir_for_project(
                project_root, claude_root
            )
            nested_archive_root = memory_dir / "archive"

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.sync_memory(
                    project_root,
                    claude_projects_root=claude_root,
                    archive_root=nested_archive_root,
                )

    def test_sync_rejects_memory_corpus_nested_under_archive_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.sync_memory(
                    project_root,
                    claude_projects_root=claude_root,
                    archive_root=claude_root,
                )

    def test_sync_concurrent_syncs_never_drop_an_intermediate_version(self) -> None:
        """Regression test: two overlapping mirrors of the same dest must
        not both snapshot the same prior content and race the final write --
        that would drop whichever version landed on dest between their reads
        (never snapshotted, never left current)."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            archive_root = pathlib.Path(tmp) / "archive"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.sync_memory(
                project_root,
                claude_projects_root=claude_root,
                archive_root=archive_root,
                timestamp="20260101T000000Z",
            )

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body v2\n",
                claude_projects_root=claude_root,
                force=True,
            )

            def run_sync(timestamp: str) -> None:
                prompt_workflow_memory.sync_memory(
                    project_root,
                    claude_projects_root=claude_root,
                    archive_root=archive_root,
                    timestamp=timestamp,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(run_sync, "20260102T000000Z"),
                    pool.submit(run_sync, "20260102T000001Z"),
                ]
                for future in futures:
                    future.result()

            slug = project_slug_for_path(project_root)
            dest = archive_root / "raw" / slug / "memory" / "feedback_foo.md"
            self.assertIn("body v2", dest.read_text(encoding="utf-8"))
            history_dir = archive_root / "history" / slug / "memory"
            snapshot_contents = [
                p.read_text(encoding="utf-8") for p in history_dir.glob("*")
            ]
            self.assertTrue(any("body v1" in c for c in snapshot_contents))


class ExportMemoriesTest(unittest.TestCase):
    def test_export_rejects_missing_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.export_memories(
                    project_root,
                    output=pathlib.Path(tmp) / "bundle.jsonl",
                    claude_projects_root=claude_root,
                )

    def test_export_by_name_produces_jsonl_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            output = pathlib.Path(tmp) / "bundle.jsonl"
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body text\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-bar",
                description="d2",
                type_="feedback",
                agent="claude",
                body="other body\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.export_memories(
                project_root,
                output=output,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(result.count, 1)
            lines = output.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["name"], "feedback-foo")
            self.assertEqual(record["body"], "body text\n")
            self.assertEqual(record["metadata"]["authored_by"], "claude")
            slug = project_slug_for_path(project_root)
            self.assertEqual(record["exported_from_slug"], slug)

    def test_export_by_agent_filters_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            output = pathlib.Path(tmp) / "bundle.jsonl"
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="b1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-bar",
                description="d2",
                type_="feedback",
                agent="codex",
                body="b2\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.export_memories(
                project_root,
                output=output,
                agent="codex",
                claude_projects_root=claude_root,
            )

            self.assertEqual(result.count, 1)
            record = json.loads(output.read_text(encoding="utf-8").strip())
            self.assertEqual(record["name"], "feedback-bar")


class ImportMemoriesTest(unittest.TestCase):
    def test_import_writes_through_write_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.export_memories(
                source_root,
                output=bundle,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root, input=bundle, claude_projects_root=claude_root
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)
            self.assertIsNone(entries[0].error)
            imported = prompt_workflow_memory.list_memories(
                dest_root, claude_projects_root=claude_root
            )
            self.assertEqual([e.filename for e in imported], ["feedback_foo.md"])

    def test_import_rejects_what_write_would_reject(self) -> None:
        """A bundled record with an invalid type must fail the same way a
        direct write_memory() call would -- import is not a second, less
        validated write mechanism."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"
            bundle.write_text(
                json.dumps(
                    {
                        "name": "feedback-bad",
                        "description": "d",
                        "metadata": {
                            "type": "not-a-real-type",
                            "authored_by": "claude",
                        },
                        "body": "b\n",
                        "exported_from_slug": "somewhere",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root, input=bundle, claude_projects_root=claude_root
            )

            self.assertEqual(len(entries), 1)
            self.assertFalse(entries[0].written)
            self.assertIsNotNone(entries[0].error)

    def test_import_rejects_malformed_bundle_records_without_crashing(self) -> None:
        """Regression test: a JSONL line may legally decode to a list,
        scalar, or an object with incorrectly typed fields -- these must
        become a clean ImportEntry error, not an uncaught AttributeError/
        TypeError from calling .get() or string/sequence operations on a
        non-dict or mistyped value."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"
            bundle.write_text(
                "\n".join(
                    [
                        json.dumps([1, 2, 3]),
                        json.dumps("just a string"),
                        json.dumps(
                            {
                                "name": "feedback-bad-description",
                                "description": 7,
                                "metadata": {
                                    "type": "feedback",
                                    "authored_by": "claude",
                                },
                                "body": "b\n",
                            }
                        ),
                        json.dumps(
                            {
                                "name": "feedback-bad-applies-to",
                                "description": "d",
                                "metadata": {
                                    "type": "feedback",
                                    "authored_by": "claude",
                                    "applies_to": "not-a-list",
                                },
                                "body": "b\n",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root, input=bundle, claude_projects_root=claude_root
            )

            self.assertEqual(len(entries), 4)
            self.assertTrue(all(not entry.written for entry in entries))
            self.assertTrue(all(entry.error is not None for entry in entries))

    def test_import_rejects_path_traversal_name_before_any_filesystem_access(
        self,
    ) -> None:
        """Security regression test: a bundle record's `name` is untrusted
        input (per _read_bundle's own docstring), yet the overwrite guard
        added for Bug 2 built a filesystem path from it (via filename_for,
        which does not strip path separators or `..` segments) and read
        whatever it found there -- before that name was ever validated as a
        safe kebab-case slug. A crafted `name` like
        `../../../secret_area/evil_target` let import read an arbitrary
        file outside the destination corpus and copy its content into
        <memory_dir>/history/ as a side effect, even though the record was
        ultimately (and only afterward) rejected with an innocuous-looking
        "not a valid kebab-case slug" error. Found by an independent
        self-review pass; fixed by validating `name` before any filesystem
        access, not just before the final write."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj_b"
            secret_dir = pathlib.Path(tmp) / "secret_area"
            secret_dir.mkdir()
            secret_file = secret_dir / "evil_target.md"
            secret_file.write_text(
                "---\nfoo: bar\n---\nTOP SECRET BODY CONTENT\n", encoding="utf-8"
            )

            # The traversed-to path must exist on disk under the real
            # destination corpus for the exploit to have anywhere to land --
            # write one real memory first so memory_dir genuinely exists.
            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-placeholder",
                description="d",
                type_="feedback",
                agent="claude",
                body="x\n",
                claude_projects_root=claude_root,
            )

            bundle = pathlib.Path(tmp) / "bundle.jsonl"
            bundle.write_text(
                json.dumps(
                    {
                        "name": "../../../secret_area/evil_target",
                        "description": "d",
                        "metadata": {"type": "feedback", "authored_by": "claude"},
                        "body": "x",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root, input=bundle, force=True, claude_projects_root=claude_root
            )

            self.assertEqual(len(entries), 1)
            self.assertFalse(entries[0].written)
            self.assertIsNotNone(entries[0].error)
            memory_dir = prompt_workflow_memory.memory_dir_for_project(
                dest_root, claude_root
            )
            history_dir = memory_dir / "history"
            self.assertFalse(
                history_dir.exists(),
                "traversed-to file content must never be read/copied before "
                "the record's name is validated",
            )

    def test_import_dry_run_runs_real_validation(self) -> None:
        """Regression test: dry-run previously marked every parsed record
        error-free unconditionally, before write_memory's own validation
        ever ran -- so an invalid type, missing author, or cross-agent
        conflict that a real import rejects was reported as `would write`.
        Dry-run must run the exact same validation/conflict checks a real
        import would, just without touching the filesystem."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"
            bundle.write_text(
                json.dumps(
                    {
                        "name": "feedback-bad",
                        "description": "d",
                        "metadata": {
                            "type": "not-a-real-type",
                            "authored_by": "claude",
                        },
                        "body": "b\n",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root, input=bundle, dry_run=True, claude_projects_root=claude_root
            )

            self.assertEqual(len(entries), 1)
            self.assertFalse(entries[0].written)
            self.assertIsNotNone(entries[0].error)

    def test_import_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.export_memories(
                source_root,
                output=bundle,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root,
                input=bundle,
                dry_run=True,
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertFalse(entries[0].written)
            imported = prompt_workflow_memory.list_memories(
                dest_root, claude_projects_root=claude_root
            )
            self.assertEqual(imported, [])

    def test_import_name_filter_restricts_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            bundle = pathlib.Path(tmp) / "bundle.jsonl"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="b1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-bar",
                description="d2",
                type_="feedback",
                agent="claude",
                body="b2\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.export_memories(
                source_root,
                output=bundle,
                agent="claude",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.import_memories(
                dest_root,
                input=bundle,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].name, "feedback-foo")


class TransferMemoriesTest(unittest.TestCase):
    def test_transfer_moves_memories_between_corpora_by_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)
            dest_memories = prompt_workflow_memory.list_memories(
                dest_root, claude_projects_root=claude_root
            )
            self.assertEqual([e.filename for e in dest_memories], ["feedback_foo.md"])

    def test_transfer_accepts_a_literal_slug_for_to(self) -> None:
        """transfer's --to may name an existing corpus slug directly, not
        only a project-root path -- the whole point of transfer is moving
        memories between two corpora, which need not both be reachable via
        "the current project"."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            dest_slug = project_slug_for_path(dest_root)

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_slug,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)
            self.assertTrue(
                (claude_root / dest_slug / "memory" / "feedback_foo.md").exists()
            )

    def test_transfer_accepts_a_fresh_literal_slug_with_no_existing_corpus(
        self,
    ) -> None:
        """Regression test: an earlier revision only accepted the
        literal-slug interpretation of --to when
        <claude_projects_root>/<value>/memory already existed, silently
        falling through to project_slug_for_path() (treating the bare slug
        string as a relative filesystem path from the CWD) for the normal
        "fresh destination corpus" case -- exactly the state transfer is
        meant to populate. A bare slug (no path separators) must be
        accepted unconditionally, regardless of whether its corpus
        directory exists yet."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            fresh_slug = "brand-new-project-slug"
            self.assertFalse((claude_root / fresh_slug).exists())

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=fresh_slug,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)
            self.assertTrue(
                (claude_root / fresh_slug / "memory" / "feedback_foo.md").exists()
            )

    def test_transfer_with_absolute_path_never_escapes_claude_projects_root(
        self,
    ) -> None:
        """Regression test: pathlib's `/` operator silently discards its
        left operand whenever the right operand is itself absolute, so
        `root / str(absolute_path_or_slug)` would previously resolve to
        `<path_or_slug>/memory` -- a directory *inside* the caller's own
        project root, entirely outside claude_projects_root -- and write
        there silently if that directory happened to already exist (e.g.
        an unrelated local `memory/` folder), reporting success with no
        error and no data ever reaching the real corpus."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"
            # An unrelated local "memory" directory that happens to already
            # exist directly under dest_root -- the exact collision shape
            # the bug exploited.
            local_decoy_dir = dest_root / "memory"
            local_decoy_dir.mkdir(parents=True)

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)
            # Must land under claude_projects_root/<slug>/memory, never in
            # the decoy directory inside dest_root itself.
            self.assertEqual(list(local_decoy_dir.iterdir()), [])
            dest_slug = project_slug_for_path(dest_root)
            self.assertTrue(
                (claude_root / dest_slug / "memory" / "feedback_foo.md").exists()
            )

    def test_transfer_by_agent_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="b1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-bar",
                description="d2",
                type_="feedback",
                agent="codex",
                body="b2\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                agent="codex",
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].name, "feedback-bar")

    def test_transfer_rejects_missing_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.transfer_memories(
                    from_=source_root, to=dest_root, claude_projects_root=claude_root
                )

    def test_transfer_force_overwrites_cross_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="codex",
                body="from source\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-foo",
                description="pre-existing",
                type_="feedback",
                agent="claude",
                body="original\n",
                claude_projects_root=claude_root,
            )

            without_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )
            self.assertFalse(without_force[0].written)
            self.assertIsNotNone(without_force[0].error)

            with_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                force=True,
                claude_projects_root=claude_root,
            )
            self.assertTrue(with_force[0].written)
            dest_memories = prompt_workflow_memory.list_memories(
                dest_root, claude_projects_root=claude_root
            )
            self.assertEqual(dest_memories[0].authored_by, "codex")

    def test_transfer_from_bare_nonexistent_slug_fails_loudly(self) -> None:
        """Regression test for Bug 1: a bare relative directory name with no
        path separator (the natural way to reference a sibling directory,
        e.g. `--from spoke1`) is always resolved as a literal project slug
        by `_resolve_memory_dir`, not the caller's intended relative path.
        Previously this silently proceeded to export/import zero records,
        reporting an innocuous `0 written, 0 errors` -- indistinguishable
        from a genuinely empty corpus. `--from` must fail loudly instead,
        since (unlike `--to`) there is no legitimate "fresh, not-yet-
        existing" case for a transfer source."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj_b"

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError) as ctx:
                prompt_workflow_memory.transfer_memories(
                    from_="spoke1",
                    to=dest_root,
                    names=["feedback-foo"],
                    claude_projects_root=claude_root,
                )
            self.assertIn("does not exist", str(ctx.exception))

    def test_transfer_from_existing_path_still_works(self) -> None:
        """A `--from` value that resolves to a real, existing corpus (the
        normal path-based case) must be unaffected by the Bug 1 fix."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0].written)

    def test_transfer_same_agent_overwrite_requires_force_and_snapshots(self) -> None:
        """Regression test for Bug 2: transfer's same-agent overwrite was
        unconditional in `_write_memory_into_dir` -- no `--force` required,
        no snapshot kept -- unlike `sync`'s snapshot-before-overwrite
        invariant. A local edit at the destination could be silently and
        irrecoverably destroyed."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="hub canonical",
                type_="feedback",
                agent="claude",
                body="hub's canonical version\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-foo",
                description="local edit",
                type_="feedback",
                agent="claude",
                body="spoke1's LOCALLY EDITED version, not yet pushed anywhere\n",
                claude_projects_root=claude_root,
            )

            without_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )
            self.assertFalse(without_force[0].written)
            self.assertIsNotNone(without_force[0].error)
            # The local edit must survive untouched when --force is absent.
            still_local = prompt_workflow_memory.read_memory(
                dest_root, "feedback-foo", claude_projects_root=claude_root
            )
            self.assertIn("LOCALLY EDITED", still_local.body)

            with_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                force=True,
                claude_projects_root=claude_root,
            )
            self.assertTrue(with_force[0].written)
            overwritten = prompt_workflow_memory.read_memory(
                dest_root, "feedback-foo", claude_projects_root=claude_root
            )
            self.assertIn("canonical", overwritten.body)

            # The destroyed local edit must be recoverable from a snapshot.
            history_dir = (
                claude_root / project_slug_for_path(dest_root) / "memory" / "history"
            )
            self.assertTrue(history_dir.exists())
            snapshots = list(history_dir.glob("feedback_foo.*.md"))
            self.assertEqual(len(snapshots), 1)
            self.assertIn("LOCALLY EDITED", snapshots[0].read_text(encoding="utf-8"))

    def test_transfer_legacy_no_authored_by_overwrite_requires_force(self) -> None:
        """Regression test: a destination memory with no `authored_by` at
        all (a legacy pre-schema record, per PROP-LRH-MEMORY-COMMAND's own
        grandfathering decision) previously bypassed
        `_write_memory_into_dir`'s cross-agent check entirely (it only
        fires `if existing_authored_by and existing_authored_by != agent`),
        falling through to the same unconditional, unsnapshotted overwrite
        as the same-agent case."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="hub canonical",
                type_="feedback",
                agent="claude",
                body="hub's canonical version\n",
                claude_projects_root=claude_root,
            )
            dest_memory_dir = claude_root / project_slug_for_path(dest_root) / "memory"
            dest_memory_dir.mkdir(parents=True)
            legacy_path = dest_memory_dir / "feedback_foo.md"
            legacy_path.write_text(
                "---\n"
                "name: feedback-foo\n"
                "description: legacy record, predates authored_by\n"
                "metadata:\n"
                "  type: feedback\n"
                "---\n"
                "\n"
                "legacy body, no authored_by field at all\n",
                encoding="utf-8",
            )

            without_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )
            self.assertFalse(without_force[0].written)
            self.assertIsNotNone(without_force[0].error)
            self.assertIn("legacy", without_force[0].error)
            self.assertIn("legacy body", legacy_path.read_text(encoding="utf-8"))

            with_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                force=True,
                claude_projects_root=claude_root,
            )
            self.assertTrue(with_force[0].written)
            history_dir = dest_memory_dir / "history"
            snapshots = list(history_dir.glob("feedback_foo.*.md"))
            self.assertEqual(len(snapshots), 1)
            self.assertIn("legacy body", snapshots[0].read_text(encoding="utf-8"))

    def test_transfer_dry_run_does_not_snapshot(self) -> None:
        """The overwrite guard's dry-run path must report the same
        accept/reject outcome a real transfer would without touching the
        filesystem at all -- no snapshot file written."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="source\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="dest original\n",
                claude_projects_root=claude_root,
            )

            entries = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                force=True,
                dry_run=True,
                claude_projects_root=claude_root,
            )
            self.assertIsNone(entries[0].error)  # would have succeeded for real
            history_dir = (
                claude_root / project_slug_for_path(dest_root) / "memory" / "history"
            )
            self.assertFalse(history_dir.exists())

    def test_transfer_force_overwrites_malformed_destination(self) -> None:
        """Regression test for Codex's and Copilot's review comments on
        WI-LRH-MEMORY-TRANSFER-SAFETY: a destination whose frontmatter
        fails to parse (or isn't valid UTF-8) previously blocked the
        overwrite guard's own parse attempt even with --force -- a
        regression against _write_memory_into_dir's own pre-existing
        behavior, which skips parsing the destination entirely when
        force=True. The malformed file's raw bytes must still be
        preserved as a snapshot, and the forced overwrite must succeed."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="hub canonical",
                type_="feedback",
                agent="claude",
                body="hub's canonical version\n",
                claude_projects_root=claude_root,
            )
            dest_memory_dir = claude_root / project_slug_for_path(dest_root) / "memory"
            dest_memory_dir.mkdir(parents=True)
            malformed_path = dest_memory_dir / "feedback_foo.md"
            malformed_path.write_bytes(b"not even close to frontmatter \xff\xfe")

            without_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )
            self.assertFalse(without_force[0].written)
            self.assertIsNotNone(without_force[0].error)
            self.assertIn("malformed", without_force[0].error)

            with_force = prompt_workflow_memory.transfer_memories(
                from_=source_root,
                to=dest_root,
                names=["feedback-foo"],
                force=True,
                claude_projects_root=claude_root,
            )
            self.assertTrue(with_force[0].written)
            overwritten = prompt_workflow_memory.read_memory(
                dest_root, "feedback-foo", claude_projects_root=claude_root
            )
            self.assertIn("canonical", overwritten.body)

            history_dir = dest_memory_dir / "history"
            snapshots = list(history_dir.glob("feedback_foo.*.md"))
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(
                snapshots[0].read_bytes(),
                b"not even close to frontmatter \xff\xfe",
            )

    def test_transfer_repeated_unchanged_force_does_not_grow_history(self) -> None:
        """Regression test for Codex's review comment: repeating an
        already-applied --force transfer/import (destination content
        already matches what would be written) must not create a new
        snapshot each time -- otherwise an unbounded sequence of
        identical-content files accumulates across periodic re-syncs,
        which `sync` would go on to recursively archive every round."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            source_root = pathlib.Path(tmp) / "proj_a"
            dest_root = pathlib.Path(tmp) / "proj_b"

            prompt_workflow_memory.write_memory(
                source_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="same content every time\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="original\n",
                claude_projects_root=claude_root,
            )
            history_dir = (
                claude_root / project_slug_for_path(dest_root) / "memory" / "history"
            )

            for _ in range(3):
                entries = prompt_workflow_memory.transfer_memories(
                    from_=source_root,
                    to=dest_root,
                    names=["feedback-foo"],
                    force=True,
                    claude_projects_root=claude_root,
                )
                self.assertTrue(entries[0].written)

            # Exactly one real change happened (original -> "same content
            # every time"), so exactly one snapshot must exist -- not one
            # per repeated call.
            snapshots = list(history_dir.glob("feedback_foo.*.md"))
            self.assertEqual(len(snapshots), 1)
            self.assertIn("original", snapshots[0].read_text(encoding="utf-8"))

    def test_transfer_concurrent_forced_overwrites_never_drop_a_version(self) -> None:
        """Regression test for Codex's review comment: two concurrent
        forced transfers into the same destination must not both read and
        snapshot the same prior content and then race the final write --
        that would drop whichever version landed on the destination
        between their reads (never snapshotted, never left current)."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            dest_root = pathlib.Path(tmp) / "proj_b"
            source_v2_root = pathlib.Path(tmp) / "proj_v2"
            source_v3_root = pathlib.Path(tmp) / "proj_v3"

            prompt_workflow_memory.write_memory(
                dest_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="v1\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                source_v2_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="v2\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                source_v3_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="v3\n",
                claude_projects_root=claude_root,
            )

            def run_transfer(source_root: pathlib.Path) -> None:
                prompt_workflow_memory.transfer_memories(
                    from_=source_root,
                    to=dest_root,
                    names=["feedback-foo"],
                    force=True,
                    claude_projects_root=claude_root,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(run_transfer, source_v2_root),
                    pool.submit(run_transfer, source_v3_root),
                ]
                for future in futures:
                    future.result()

            final = prompt_workflow_memory.read_memory(
                dest_root, "feedback-foo", claude_projects_root=claude_root
            )
            self.assertIn(final.body.strip(), ("v2", "v3"))

            history_dir = (
                claude_root / project_slug_for_path(dest_root) / "memory" / "history"
            )
            snapshot_bodies = {
                p.read_text(encoding="utf-8").strip().splitlines()[-1]
                for p in history_dir.glob("feedback_foo.*.md")
            }
            # v1 (the original) must always be snapshotted. Whichever of
            # v2/v3 lost the race must also be snapshotted -- never
            # silently dropped.
            self.assertIn("v1", snapshot_bodies)
            loser = "v3" if final.body.strip() == "v2" else "v2"
            self.assertIn(loser, snapshot_bodies)


class ReadMemoryTest(unittest.TestCase):
    def test_read_returns_frontmatter_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body text\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.read_memory(
                project_root, "feedback-foo", claude_projects_root=claude_root
            )

            self.assertEqual(result.name, "feedback-foo")
            self.assertEqual(result.frontmatter["name"], "feedback-foo")
            self.assertEqual(result.frontmatter["description"], "d")
            self.assertEqual(result.body, "body text\n")
            self.assertIn("body text", result.content)
            self.assertTrue(result.path.exists())

    def test_read_missing_memory_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.read_memory(
                    project_root,
                    "feedback-nonexistent",
                    claude_projects_root=claude_root,
                )

    def test_read_rejects_path_traversal_name(self) -> None:
        """A `name` with path segments must never escape the memory dir."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.read_memory(
                    project_root, "../../etc/passwd", claude_projects_root=claude_root
                )

    def test_read_rejects_symlinked_memory_file(self) -> None:
        """Regression test: `_validate_name` blocks path traversal via the
        `name` argument, but Path.read_text() follows filesystem symlinks
        by default -- a symlink placed directly in the corpus
        (feedback-x.md -> /some/other/file) would otherwise let `read`
        print content from anywhere on disk."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            outside_secret = pathlib.Path(tmp) / "secret.md"
            outside_secret.write_text("top secret content\n", encoding="utf-8")

            memory_dir = claude_root / project_slug_for_path(project_root) / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "feedback_symlinked.md").symlink_to(outside_secret)

            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.read_memory(
                    project_root, "feedback-symlinked", claude_projects_root=claude_root
                )


class SearchMemoriesTest(unittest.TestCase):
    def test_search_finds_substring_in_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="a line about apples\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-bar",
                description="d2",
                type_="feedback",
                agent="claude",
                body="a line about oranges\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "apples", claude_projects_root=claude_root
            )

            self.assertEqual(result.match_count, 1)
            self.assertEqual(result.matches[0].name, "feedback-foo")
            self.assertEqual(result.exit_code, 0)

    def test_search_finds_substring_in_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-unique-description-xyz",
                description="a very distinctive description",
                type_="feedback",
                agent="claude",
                body="unrelated body\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "distinctive", claude_projects_root=claude_root
            )

            self.assertEqual(result.match_count, 1)
            self.assertTrue(
                any("frontmatter.description" in c for c in result.matches[0].contexts)
            )

    def test_search_is_case_insensitive_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="MixedCase Content\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "mixedcase", claude_projects_root=claude_root
            )
            self.assertEqual(result.match_count, 1)

            case_sensitive_result = prompt_workflow_memory.search_memories(
                project_root,
                "mixedcase",
                case_sensitive=True,
                claude_projects_root=claude_root,
            )
            self.assertEqual(case_sensitive_result.match_count, 0)

    def test_search_filters_by_agent_and_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-claude",
                description="d",
                type_="feedback",
                agent="claude",
                body="shared search term\n",
                claude_projects_root=claude_root,
            )
            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-codex",
                description="d",
                type_="feedback",
                agent="codex",
                body="shared search term\n",
                claude_projects_root=claude_root,
            )

            by_agent = prompt_workflow_memory.search_memories(
                project_root,
                "shared search term",
                agent="codex",
                claude_projects_root=claude_root,
            )
            self.assertEqual(by_agent.match_count, 1)
            self.assertEqual(by_agent.matches[0].name, "feedback-codex")

    def test_search_excludes_the_index_file_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-foo",
                description="a searchable description",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "searchable", claude_projects_root=claude_root
            )

            self.assertTrue(
                all(match.path.name != "MEMORY.md" for match in result.matches)
            )

    def test_search_rejects_empty_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
                prompt_workflow_memory.search_memories(
                    project_root, "", claude_projects_root=claude_root
                )

    def test_search_empty_corpus_returns_no_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            result = prompt_workflow_memory.search_memories(
                project_root, "anything", claude_projects_root=claude_root
            )
            self.assertEqual(result.match_count, 0)
            self.assertEqual(result.exit_code, 1)

    def test_search_finds_substring_in_malformed_memory_raw_content(self) -> None:
        """Regression test: a memory without valid frontmatter (legacy or
        malformed) must still be searchable by its raw content -- silently
        skipping it would hide exactly the population `lrh memory search`
        exists to help inspect and repair."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            memory_dir = claude_root / project_slug_for_path(project_root) / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy_foo.md").write_text(
                "no frontmatter here, just a distinctive_needle_xyz string\n",
                encoding="utf-8",
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "distinctive_needle_xyz", claude_projects_root=claude_root
            )

            self.assertEqual(result.match_count, 1)
            self.assertEqual(result.matches[0].name, "legacy_foo")
            self.assertIsNone(result.matches[0].authored_by)
            self.assertTrue(
                any("distinctive_needle_xyz" in c for c in result.matches[0].contexts)
            )

    def test_search_skips_malformed_memory_when_agent_or_type_filter_set(
        self,
    ) -> None:
        """A malformed memory has no valid metadata to filter by -- it must
        be excluded (not error, not falsely included) when --agent/--type
        is requested, since the filter question is unanswerable for it."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            memory_dir = claude_root / project_slug_for_path(project_root) / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "legacy_foo.md").write_text(
                "no frontmatter, but has the word needle in it\n", encoding="utf-8"
            )

            result = prompt_workflow_memory.search_memories(
                project_root,
                "needle",
                agent="claude",
                claude_projects_root=claude_root,
            )
            self.assertEqual(result.match_count, 0)

    def test_search_skips_symlinked_entries_rather_than_following_them(self) -> None:
        """Regression test: search must never follow a symlink placed
        directly in the corpus out to arbitrary filesystem content --
        skip it like any other bad entry, don't abort or leak content."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"
            outside_secret = pathlib.Path(tmp) / "secret.md"
            outside_secret.write_text("needle in outside file\n", encoding="utf-8")

            memory_dir = claude_root / project_slug_for_path(project_root) / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "feedback_symlinked.md").symlink_to(outside_secret)

            result = prompt_workflow_memory.search_memories(
                project_root, "needle", claude_projects_root=claude_root
            )
            self.assertEqual(result.match_count, 0)

    def test_search_skips_unreadable_file_rather_than_aborting(self) -> None:
        """Regression test: one unreadable/non-UTF-8 *.md entry must not
        abort the whole search -- other memories must still be found."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            project_root = pathlib.Path(tmp) / "proj"

            prompt_workflow_memory.write_memory(
                project_root,
                "feedback-good",
                description="d",
                type_="feedback",
                agent="claude",
                body="a findable needle\n",
                claude_projects_root=claude_root,
            )
            memory_dir = claude_root / project_slug_for_path(project_root) / "memory"
            (memory_dir / "feedback_bad_encoding.md").write_bytes(
                b"---\nname: feedback-bad-encoding\n---\n\n\xff\xfe not valid utf-8"
            )

            result = prompt_workflow_memory.search_memories(
                project_root, "needle", claude_projects_root=claude_root
            )
            self.assertEqual(result.match_count, 1)
            self.assertEqual(result.matches[0].name, "feedback-good")


def _git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _make_repo_with_worktree(base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Return ``(main_checkout, linked_worktree)`` as real, symlink-free paths,
    using Claude Code's own ``.claude/worktrees/<name>`` layout."""

    repo = pathlib.Path(os.path.realpath(base)) / "proj"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    worktree = repo / ".claude" / "worktrees" / "wt-one"
    _git(repo, "worktree", "add", "-q", "-b", "wt-branch", str(worktree))
    return repo, worktree


class CanonicalProjectRootTest(unittest.TestCase):
    def test_linked_worktree_maps_to_main_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))

            self.assertEqual(
                prompt_workflow_memory.canonical_project_root(worktree), repo
            )

    def test_main_checkout_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = _make_repo_with_worktree(pathlib.Path(tmp))

            self.assertEqual(prompt_workflow_memory.canonical_project_root(repo), repo)

    def test_non_git_directory_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plain = pathlib.Path(tmp) / "plain"
            plain.mkdir()

            self.assertEqual(
                prompt_workflow_memory.canonical_project_root(plain), plain
            )
            self.assertIsNone(prompt_workflow_memory.worktree_mapping_note(plain))

    def test_subdirectory_of_worktree_maps_to_main_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))
            sub = worktree / "sub"
            sub.mkdir()

            self.assertEqual(prompt_workflow_memory.canonical_project_root(sub), repo)

    def test_worktree_mapping_note_names_main_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))

            note = prompt_workflow_memory.worktree_mapping_note(worktree)

            self.assertIsNotNone(note)
            self.assertIn(str(repo), note)
            self.assertIsNone(prompt_workflow_memory.worktree_mapping_note(repo))


class WorktreeMemoryDirTest(unittest.TestCase):
    def test_worktree_and_main_checkout_share_one_memory_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))

            self.assertEqual(
                prompt_workflow_memory.memory_dir_for_project(worktree, claude_root),
                prompt_workflow_memory.memory_dir_for_project(repo, claude_root),
            )

    def test_write_from_worktree_lands_in_canonical_dir_not_worktree_slug(
        self,
    ) -> None:
        """Regression for WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR: the cwd-derived
        worktree slug (``...--claude-worktrees-<name>``) must not receive the
        write -- no future session reads it."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))
            orphan_dir = claude_root / project_slug_for_path(worktree) / "memory"
            canonical_dir = claude_root / project_slug_for_path(repo) / "memory"
            self.assertIn("--claude-worktrees-", str(orphan_dir))

            result = prompt_workflow_memory.write_memory(
                worktree,
                "feedback-from-worktree",
                description="written from a worktree cwd",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            self.assertEqual(result.memory_path.parent, canonical_dir)
            self.assertTrue((canonical_dir / "feedback_from_worktree.md").exists())
            self.assertFalse(orphan_dir.exists())


_ORPHAN_MEMORY = """---
name: {name}
description: {description}
metadata:
  type: feedback
{authored_line}---

body
"""


def _write_orphan_memory(
    memory_dir: pathlib.Path,
    filename: str,
    *,
    authored_by: str | None = "claude",
    description: str = "an orphaned memory",
) -> pathlib.Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    path = memory_dir / filename
    path.write_text(
        _ORPHAN_MEMORY.format(
            name=filename.removesuffix(".md").replace("_", "-"),
            description=description,
            authored_line=(f"  authored_by: {authored_by}\n" if authored_by else ""),
        ),
        encoding="utf-8",
    )
    return path


class RecoverOrphanMemoriesTest(unittest.TestCase):
    def _setup(self, tmp: str) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        base = pathlib.Path(os.path.realpath(tmp))
        claude_root = base / "claude-projects"
        project = base / "my_proj"
        project.mkdir()
        slug = project_slug_for_path(project)
        canonical_dir = claude_root / slug / "memory"
        canonical_dir.mkdir(parents=True)
        return claude_root, project, canonical_dir

    def test_finds_hyphen_and_underscore_worktree_dirs_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, _ = self._setup(tmp)
            slug = project_slug_for_path(project)
            hyphen = claude_root / f"{slug}--claude-worktrees-wt-a" / "memory"
            underscore = (
                claude_root
                / f"{slug.replace('my-proj', 'my_proj')}--claude-worktrees-wt-b"
                / "memory"
            )
            unrelated = claude_root / f"{slug}-other--claude-worktrees-wt-c" / "memory"
            for directory in (hyphen, underscore, unrelated):
                directory.mkdir(parents=True)

            found = prompt_workflow_memory.find_orphan_memory_dirs(project, claude_root)

            self.assertEqual(found, sorted([hyphen, underscore]))

    def test_dry_run_reports_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            _write_orphan_memory(orphan, "feedback_one.md")

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root
            )

            self.assertEqual([e.action for e in entries], ["would_copy"])
            self.assertFalse((canonical_dir / "feedback_one.md").exists())
            self.assertFalse((canonical_dir / "MEMORY.md").exists())

    def test_apply_copies_indexes_and_leaves_originals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            original = _write_orphan_memory(
                orphan, "feedback_one.md", description="recovered one"
            )

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["copied"])
            copied = canonical_dir / "feedback_one.md"
            self.assertEqual(copied.read_bytes(), original.read_bytes())
            self.assertTrue(original.exists())
            index = (canonical_dir / "MEMORY.md").read_text(encoding="utf-8")
            self.assertIn("(feedback_one.md)", index)
            self.assertIn("recovered one", index)

    def test_apply_never_overwrites_a_differing_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            _write_orphan_memory(orphan, "feedback_one.md", description="orphan copy")
            existing = _write_orphan_memory(
                canonical_dir, "feedback_one.md", description="canonical copy"
            )
            before = existing.read_bytes()

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["conflict"])
            self.assertEqual(existing.read_bytes(), before)

    def test_identical_canonical_file_is_reported_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            _write_orphan_memory(orphan, "feedback_one.md")
            existing = _write_orphan_memory(canonical_dir, "feedback_one.md")
            before = existing.read_bytes()
            before_inode = existing.stat().st_ino

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["identical"])
            self.assertEqual(existing.read_bytes(), before)
            self.assertEqual(existing.stat().st_ino, before_inode)

    def test_unattributed_files_reported_and_skipped_unless_included(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            _write_orphan_memory(orphan, "feedback_mystery.md", authored_by=None)

            skipped = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )
            self.assertEqual([e.action for e in skipped], ["unattributed"])
            self.assertFalse((canonical_dir / "feedback_mystery.md").exists())

            included = prompt_workflow_memory.recover_orphan_memories(
                project,
                claude_projects_root=claude_root,
                apply=True,
                include_unattributed=True,
            )
            self.assertEqual([e.action for e in included], ["copied"])
            self.assertTrue((canonical_dir / "feedback_mystery.md").exists())

    def test_malformed_file_is_reported_and_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, canonical_dir = self._setup(tmp)
            orphan = (
                claude_root
                / f"{project_slug_for_path(project)}--claude-worktrees-wt"
                / "memory"
            )
            orphan.mkdir(parents=True)
            (orphan / "broken.md").write_text("no frontmatter\n", encoding="utf-8")

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["malformed"])
            self.assertFalse((canonical_dir / "broken.md").exists())

    def test_recovery_from_a_worktree_cwd_targets_the_main_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))
            orphan = claude_root / f"{project_slug_for_path(worktree)}" / "memory"
            _write_orphan_memory(orphan, "feedback_one.md")

            entries = prompt_workflow_memory.recover_orphan_memories(
                worktree, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["copied"])
            canonical_dir = claude_root / project_slug_for_path(repo) / "memory"
            self.assertTrue((canonical_dir / "feedback_one.md").exists())


class WorktreeDownstreamIdentityTest(unittest.TestCase):
    """sync/export must derive their slug from the canonical root too, or a
    worktree session archives the main corpus under a second slug."""

    def test_sync_from_worktree_archives_under_the_canonical_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            archive_root = pathlib.Path(tmp) / "archive"
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))
            prompt_workflow_memory.write_memory(
                worktree,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )

            prompt_workflow_memory.sync_memory(
                worktree, claude_projects_root=claude_root, archive_root=archive_root
            )

            canonical = archive_root / "raw" / project_slug_for_path(repo) / "memory"
            self.assertTrue((canonical / "feedback_foo.md").exists())
            self.assertEqual(
                [p.name for p in (archive_root / "raw").iterdir()],
                [project_slug_for_path(repo)],
            )

    def test_export_from_worktree_records_the_canonical_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = pathlib.Path(tmp) / "claude-projects"
            repo, worktree = _make_repo_with_worktree(pathlib.Path(tmp))
            prompt_workflow_memory.write_memory(
                worktree,
                "feedback-foo",
                description="d",
                type_="feedback",
                agent="claude",
                body="body\n",
                claude_projects_root=claude_root,
            )
            output = pathlib.Path(tmp) / "bundle.jsonl"

            prompt_workflow_memory.export_memories(
                worktree,
                output=output,
                names=["feedback-foo"],
                claude_projects_root=claude_root,
            )

            record = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["exported_from_slug"], project_slug_for_path(repo))


class RecoverOrphanSafetyTest(unittest.TestCase):
    def _setup(self, tmp: str) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        base = pathlib.Path(os.path.realpath(tmp))
        claude_root = base / "claude-projects"
        project = base / "proj"
        project.mkdir()
        canonical_dir = claude_root / project_slug_for_path(project) / "memory"
        canonical_dir.mkdir(parents=True)
        orphan = (
            claude_root
            / f"{project_slug_for_path(project)}--claude-worktrees-wt"
            / "memory"
        )
        return claude_root, project, orphan

    def test_symlinked_memory_dir_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            outside = pathlib.Path(tmp) / "outside"
            _write_orphan_memory(outside, "feedback_secret.md")
            orphan.parent.mkdir(parents=True)
            orphan.symlink_to(outside)

            self.assertEqual(
                prompt_workflow_memory.find_orphan_memory_dirs(project, claude_root),
                [],
            )

    def test_symlinked_bucket_dir_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            outside = pathlib.Path(tmp) / "outside-bucket"
            _write_orphan_memory(outside / "memory", "feedback_secret.md")
            orphan.parent.symlink_to(outside)

            self.assertEqual(
                prompt_workflow_memory.find_orphan_memory_dirs(project, claude_root),
                [],
            )

    def test_symlinked_memory_file_is_reported_and_not_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            outside = _write_orphan_memory(
                pathlib.Path(tmp) / "outside", "feedback_secret.md"
            )
            orphan.mkdir(parents=True)
            (orphan / "feedback_link.md").symlink_to(outside)

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["malformed"])
            self.assertIn("symlink", entries[0].detail)
            canonical_dir = claude_root / project_slug_for_path(project) / "memory"
            self.assertFalse((canonical_dir / "feedback_link.md").exists())

    def test_structurally_invalid_attributed_file_is_not_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            orphan.mkdir(parents=True)
            (orphan / "feedback_nodesc.md").write_text(
                "---\nname: feedback-nodesc\nmetadata:\n  type: feedback\n"
                "  authored_by: claude\n---\n\nbody\n",
                encoding="utf-8",
            )
            (orphan / "feedback_badtype.md").write_text(
                "---\nname: feedback-badtype\ndescription: d\nmetadata:\n"
                "  type: nonsense\n  authored_by: claude\n---\n\nbody\n",
                encoding="utf-8",
            )

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["malformed", "malformed"])
            canonical_dir = claude_root / project_slug_for_path(project) / "memory"
            self.assertEqual(list(canonical_dir.glob("*.md")), [])
            report = prompt_workflow_memory.validate_corpus(project, claude_root)
            self.assertEqual(report.malformed, ())


class RecoverOrphanRobustnessTest(unittest.TestCase):
    def _setup(self, tmp: str) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        base = pathlib.Path(os.path.realpath(tmp))
        claude_root = base / "claude-projects"
        project = base / "proj"
        project.mkdir()
        orphan = (
            claude_root
            / f"{project_slug_for_path(project)}--claude-worktrees-wt"
            / "memory"
        )
        return claude_root, project, orphan

    def test_unreadable_source_entry_is_reported_and_run_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_good.md")
            (orphan / "a_dir.md").mkdir()

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual(
                sorted((e.filename, e.action) for e in entries),
                [("a_dir.md", "malformed"), ("feedback_good.md", "copied")],
            )

    def test_unreadable_canonical_path_is_a_conflict_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_one.md")
            canonical_dir = claude_root / project_slug_for_path(project) / "memory"
            (canonical_dir / "feedback_one.md").mkdir(parents=True)

            entries = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in entries], ["conflict"])

    def test_copy_never_overwrites_a_file_that_appears_after_the_checks(self) -> None:
        """A concurrent ``write`` landing between recovery's existence check
        and its copy must survive: the copy is an atomic no-clobber link."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_one.md", description="orphan")
            canonical_dir = claude_root / project_slug_for_path(project) / "memory"
            canonical_dir.mkdir(parents=True)
            racing = canonical_dir / "feedback_one.md"
            real_link = os.link

            def link_after_racing_write(src: str, dst: str) -> None:
                racing.write_text("written concurrently\n", encoding="utf-8")
                real_link(src, dst)

            with unittest.mock.patch.object(os, "link", link_after_racing_write):
                entries = prompt_workflow_memory.recover_orphan_memories(
                    project, claude_projects_root=claude_root, apply=True
                )

            self.assertEqual([e.action for e in entries], ["conflict"])
            self.assertEqual(
                racing.read_text(encoding="utf-8"), "written concurrently\n"
            )
            self.assertEqual(
                [p.name for p in canonical_dir.iterdir() if p.name.endswith(".tmp")], []
            )


class RecoverOrphanFallbackTest(unittest.TestCase):
    def _setup(
        self, tmp: str
    ) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
        base = pathlib.Path(os.path.realpath(tmp))
        claude_root = base / "claude-projects"
        project = base / "proj"
        project.mkdir()
        orphan = (
            claude_root
            / f"{project_slug_for_path(project)}--claude-worktrees-wt"
            / "memory"
        )
        canonical_dir = claude_root / project_slug_for_path(project) / "memory"
        return claude_root, project, orphan, canonical_dir

    def test_unsupported_hard_links_are_reported_per_entry_and_leave_no_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan, canonical_dir = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_one.md")
            _write_orphan_memory(orphan, "feedback_two.md")

            def no_links(src: str, dst: str) -> None:
                raise PermissionError(1, "Operation not permitted")

            with unittest.mock.patch.object(os, "link", no_links):
                entries = prompt_workflow_memory.recover_orphan_memories(
                    project, claude_projects_root=claude_root, apply=True
                )

            self.assertEqual([e.action for e in entries], ["conflict", "conflict"])
            self.assertIn("could not link", entries[0].detail)
            self.assertEqual(
                sorted(
                    p.name
                    for p in canonical_dir.iterdir()
                    if not p.name.startswith(".")
                ),
                [],
            )
            self.assertEqual(
                [p.name for p in canonical_dir.iterdir() if p.name.endswith(".tmp")],
                [],
            )

    def test_apply_indexes_an_identical_but_unindexed_file(self) -> None:
        """Heals a run interrupted between the copy and the index write."""

        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan, canonical_dir = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_one.md", description="d1")
            _write_orphan_memory(canonical_dir, "feedback_one.md", description="d1")
            self.assertFalse((canonical_dir / "MEMORY.md").exists())

            dry = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root
            )
            self.assertEqual([e.action for e in dry], ["identical"])
            self.assertFalse((canonical_dir / "MEMORY.md").exists())

            applied = prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual([e.action for e in applied], ["identical"])
            index = (canonical_dir / "MEMORY.md").read_text(encoding="utf-8")
            self.assertIn("(feedback_one.md)", index)

    def test_healing_never_rewrites_an_existing_hand_edited_index_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root, project, orphan, canonical_dir = self._setup(tmp)
            _write_orphan_memory(orphan, "feedback_one.md", description="d1")
            _write_orphan_memory(canonical_dir, "feedback_one.md", description="d1")
            curated = "- [My curated title](feedback_one.md) — a hand-written hook\n"
            (canonical_dir / "MEMORY.md").write_text(
                "# Memory Index\n" + curated, encoding="utf-8"
            )

            prompt_workflow_memory.recover_orphan_memories(
                project, claude_projects_root=claude_root, apply=True
            )

            self.assertEqual(
                (canonical_dir / "MEMORY.md").read_text(encoding="utf-8"),
                "# Memory Index\n" + curated,
            )


if __name__ == "__main__":
    unittest.main()
