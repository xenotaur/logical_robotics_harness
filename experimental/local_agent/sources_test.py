import pathlib
import tempfile
import unittest

from local_agent import sources, testing_support


class SourcesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.commit = testing_support.make_repo(self.repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make(self, path: str, max_bytes: int = 100_000) -> tuple:
        return sources.make_source(
            repo=self.repo,
            repo_label="TEST",
            commit=self.commit,
            project_dir=".",
            project_relative_path=path,
            source_id="S1",
            relation="WorkItem",
            max_bytes=max_bytes,
        )

    def test_reads_tracked_file_with_provenance(self) -> None:
        ref, text = self._make("project/work_items/proposed/WI-T-1.md")
        self.assertEqual(ref.commit, self.commit)
        self.assertEqual(ref.line_start, 1)
        self.assertEqual(ref.line_end, ref.total_lines)
        self.assertFalse(ref.truncated)
        self.assertEqual(len(ref.sha256), 64)
        self.assertIn("Ready fixture item", text)

    def test_working_tree_edits_do_not_leak(self) -> None:
        path = self.repo / "project/work_items/proposed/WI-T-1.md"
        path.write_text("DIRTY UNCOMMITTED CONTENT\n", encoding="utf-8")
        _, text = self._make("project/work_items/proposed/WI-T-1.md")
        self.assertNotIn("DIRTY", text)

    def test_untracked_file_rejected(self) -> None:
        (self.repo / "project/untracked.md").write_text("x\n", encoding="utf-8")
        with self.assertRaises(sources.SourceError):
            self._make("project/untracked.md")

    def test_excluded_private_prefix_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "excluded"):
            self._make("project/executions/AD_HOC/private.md")

    def test_binary_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "binary"):
            self._make("project/data.bin")

    def test_traversal_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "confined"):
            self._make("../outside.md")
        with self.assertRaisesRegex(sources.SourceError, "confined"):
            self._make("/etc/passwd")

    def test_truncates_on_line_boundary(self) -> None:
        ref, text = self._make("project/design/demo.md", max_bytes=60)
        self.assertTrue(ref.truncated)
        self.assertLess(ref.line_end, ref.total_lines)
        self.assertTrue(text.endswith("\n"))
        self.assertLessEqual(len(text.encode("utf-8")), 60)
        self.assertEqual(ref.included_bytes, len(text.encode("utf-8")))

    def test_line_splitting_matches_git_line_numbers(self) -> None:
        self.assertEqual(
            sources.split_lines("a\x0cb\nc\u2028d\ne"), ["a\x0cb\n", "c\u2028d\n", "e"]
        )
        self.assertEqual(sources.split_lines(""), [])
        self.assertEqual(sources.split_lines("x\n"), ["x\n"])

    def test_materialize_extracts_only_tracked_tree(self) -> None:
        (self.repo / "project/untracked.md").write_text("x\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as out:
            root = sources.materialize_project_tree(
                self.repo, self.commit, ".", pathlib.Path(out)
            )
            self.assertTrue((root / "project/work_items/proposed/WI-T-1.md").exists())
            self.assertFalse((root / "project/untracked.md").exists())


if __name__ == "__main__":
    unittest.main()
