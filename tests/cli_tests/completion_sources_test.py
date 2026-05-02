import pathlib
import tempfile
import unittest

from lrh.cli import completion_sources


class TestCompletionSources(unittest.TestCase):

    def test_request_template_names_returns_sorted_prefix_matches(self) -> None:
        names = completion_sources.request_template_names(prefix="ci_")
        self.assertEqual(names, sorted(names))
        self.assertTrue(names)
        self.assertTrue(all(name.startswith("ci_") for name in names))

    def test_work_item_ids_reads_ids_from_known_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            proposed = root / "project" / "work_items" / "proposed"
            resolved = root / "project" / "work_items" / "resolved"
            proposed.mkdir(parents=True)
            resolved.mkdir(parents=True)
            (proposed / "one.md").write_text(
                "---\nid: WI-ALPHA\ntitle: A\n---\nBody\n", encoding="utf-8"
            )
            (resolved / "two.md").write_text(
                "---\nid: WI-RELEASE-TAG-CI\ntitle: B\n---\nBody\n",
                encoding="utf-8",
            )

            ids = completion_sources.work_item_ids(root)

            self.assertEqual(ids, ["WI-ALPHA", "WI-RELEASE-TAG-CI"])

    def test_work_item_ids_prefix_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            active = root / "project" / "work_items" / "active"
            active.mkdir(parents=True)
            (active / "one.md").write_text(
                "---\nid: WI-RELEASE-TAG-CI\n---\n", encoding="utf-8"
            )
            (active / "two.md").write_text("---\nid: WI-OTHER\n---\n", encoding="utf-8")

            ids = completion_sources.work_item_ids(root, prefix="WI-R")

            self.assertEqual(ids, ["WI-RELEASE-TAG-CI"])

    def test_work_item_ids_ignores_missing_or_malformed_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            active = root / "project" / "work_items" / "active"
            active.mkdir(parents=True)
            (active / "no-frontmatter.md").write_text("hello\n", encoding="utf-8")

            self.assertEqual(completion_sources.work_item_ids(root), [])
            self.assertEqual(
                completion_sources.work_item_ids(root / "missing-project"), []
            )


if __name__ == "__main__":
    unittest.main()
