import concurrent.futures
import pathlib
import tempfile
import unittest

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
        self.assertEqual(body.strip(), "body text")

    def test_missing_opening_delimiter_raises(self) -> None:
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory.read_frontmatter_and_body("no frontmatter here")

    def test_missing_closing_delimiter_raises(self) -> None:
        with self.assertRaises(prompt_workflow_memory.MemoryValidationError):
            prompt_workflow_memory.read_frontmatter_and_body("---\nname: foo\n")


if __name__ == "__main__":
    unittest.main()
