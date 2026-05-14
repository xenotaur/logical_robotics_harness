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

    def test_request_template_names_includes_catalog_canonical_names(self) -> None:
        self.assertEqual(
            completion_sources.request_template_names(prefix="improve-"),
            ["improve-coverage"],
        )
        self.assertIn(
            "assess-continuous-integration-status",
            completion_sources.request_template_names(prefix="assess-"),
        )

    def test_request_template_names_includes_explicit_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = pathlib.Path(temp_dir)
            template_path = template_dir / "request" / "custom_explicit.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("custom\n", encoding="utf-8")

            names = completion_sources.request_template_names(
                prefix="custom",
                template_dirs=[template_dir],
                environ={},
            )

        self.assertEqual(names, ["custom_explicit"])

    def test_request_template_names_includes_environment_only_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_dir = pathlib.Path(temp_dir)
            template_path = env_dir / "request" / "custom_env.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("custom\n", encoding="utf-8")

            names = completion_sources.request_template_names(
                prefix="custom",
                environ={"LRH_TEMPLATE_DIR": str(env_dir)},
            )

        self.assertEqual(names, ["custom_env"])

    def test_request_template_names_includes_project_local_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            template_path = (
                project_root / ".lrh" / "templates" / "request" / "custom_project.md"
            )
            template_path.parent.mkdir(parents=True)
            template_path.write_text("custom\n", encoding="utf-8")

            names = completion_sources.request_template_names(
                prefix="custom",
                project_root=project_root,
                environ={},
            )

        self.assertEqual(names, ["custom_project"])

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

    def test_work_item_ids_discovers_flat_and_nested_with_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_items = root / "project" / "work_items"
            active = work_items / "active"
            nested = active / "nested"
            work_items.mkdir(parents=True)
            active.mkdir(parents=True)
            nested.mkdir(parents=True)
            (work_items / "WI-FLAT-FRONTMATTER.md").write_text(
                "---\nid: WI-FLAT-FRONTMATTER\n---\n",
                encoding="utf-8",
            )
            (work_items / "flat-h1.md").write_text(
                "# WI-FLAT-H1: Example work item\n",
                encoding="utf-8",
            )
            (work_items / "WI-FLAT-FILENAME.md").write_text(
                "no frontmatter\nno h1 id\n", encoding="utf-8"
            )
            (active / "bucketed.md").write_text(
                "---\nid: WI-ACTIVE-FRONTMATTER\n---\n",
                encoding="utf-8",
            )
            (nested / "nested-h1.md").write_text(
                "# WI-NESTED-H1 Example\n",
                encoding="utf-8",
            )

            self.assertEqual(
                completion_sources.work_item_ids(root),
                [
                    "WI-ACTIVE-FRONTMATTER",
                    "WI-FLAT-FILENAME",
                    "WI-FLAT-FRONTMATTER",
                    "WI-FLAT-H1",
                    "WI-NESTED-H1",
                ],
            )

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

    def test_work_item_ids_dedupes_and_filters_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_items = root / "project" / "work_items"
            work_items.mkdir(parents=True)
            (work_items / "WI-RELEASE-TAG-CI.md").write_text(
                "---\nid: WI-RELEASE-TAG-CI\n---\n",
                encoding="utf-8",
            )
            (work_items / "duplicate-heading.md").write_text(
                "# WI-RELEASE-TAG-CI: Duplicate from heading\n",
                encoding="utf-8",
            )
            (work_items / "other.md").write_text(
                "---\nid: WI-META-CLI-MVP\n---\n",
                encoding="utf-8",
            )

            self.assertEqual(
                completion_sources.work_item_ids(root, prefix="WI-R"),
                ["WI-RELEASE-TAG-CI"],
            )

    def test_work_item_ids_skips_malformed_frontmatter_with_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_items = root / "project" / "work_items"
            work_items.mkdir(parents=True)
            (work_items / "broken.md").write_text(
                "---\nid: [not-valid\n---\n# WI-FROM-H1\n",
                encoding="utf-8",
            )
            (work_items / "note.md").write_text("hello\n", encoding="utf-8")

            self.assertEqual(completion_sources.work_item_ids(root), ["WI-FROM-H1"])

    def test_work_item_ids_supports_lowercase_and_underscore(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            work_items = root / "project" / "work_items"
            work_items.mkdir(parents=True)
            (work_items / "wi_mixed.md").write_text(
                "---\nid: WI-meta_cli_mvp\n---\n",
                encoding="utf-8",
            )
            (work_items / "leading-text.md").write_text(
                "Intro paragraph.\n\n# WI-lower_case-123: Example\n",
                encoding="utf-8",
            )

            self.assertEqual(
                completion_sources.work_item_ids(root),
                ["WI-lower_case-123", "WI-meta_cli_mvp"],
            )

    def test_work_item_ids_accepts_crlf_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            active = root / "project" / "work_items" / "active"
            active.mkdir(parents=True)
            (active / "windows.md").write_text(
                "---\r\nid: WI-WINDOWS\r\ntitle: Windows\r\n---\r\n",
                encoding="utf-8",
            )

            self.assertEqual(completion_sources.work_item_ids(root), ["WI-WINDOWS"])


if __name__ == "__main__":
    unittest.main()
