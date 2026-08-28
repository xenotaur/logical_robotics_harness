import tempfile
import unittest
from pathlib import Path

import yaml

from lrh.control import frontmatter_lint, frontmatter_migration


class TestPlanFixes(unittest.TestCase):
    def test_no_findings_returns_unchanged(self) -> None:
        text = "title: fine\n"
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(new_text, text)
        self.assertEqual(fixes, [])

    def test_mid_scalar_hash_preserves_full_text(self) -> None:
        text = "instruction_source: discovered verifying PR #531\n"
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(len(fixes), 1)
        data = yaml.safe_load(new_text)
        self.assertEqual(data["instruction_source"], "discovered verifying PR #531")

    def test_colon_collapse_list_item_stays_a_string(self) -> None:
        text = "acceptance:\n  - a bullet: with a colon\n"
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(len(fixes), 1)
        data = yaml.safe_load(new_text)
        self.assertEqual(data["acceptance"], ["a bullet: with a colon"])
        self.assertIsInstance(data["acceptance"][0], str)

    def test_reserved_indicator_preserves_backtick(self) -> None:
        text = "title: `lrh validate` is broken\n"
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(len(fixes), 1)
        data = yaml.safe_load(new_text)
        self.assertEqual(data["title"], "`lrh validate` is broken")

    def test_numeric_commit_stays_a_string(self) -> None:
        text = "commit: 7926567\n"
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(len(fixes), 1)
        data = yaml.safe_load(new_text)
        self.assertEqual(data["commit"], "7926567")
        self.assertIsInstance(data["commit"], str)

    def test_fixed_output_has_no_remaining_unsafe_scalars(self) -> None:
        text = (
            "commit: 7926567\n"
            "title: `bad`\n"
            "instruction_source: fixed the bug #402\n"
            "acceptance:\n"
            "  - a bullet: with a colon\n"
        )
        new_text, fixes = frontmatter_migration.plan_fixes(text)
        self.assertEqual(len(fixes), 4)
        self.assertEqual(frontmatter_lint.iter_unsafe_scalars(new_text), [])

    def test_unaffected_fields_are_untouched(self) -> None:
        text = "title: fine\ncommit: 7926567\nowner: anthony\n"
        new_text, _fixes = frontmatter_migration.plan_fixes(text)
        self.assertIn("title: fine\n", new_text)
        self.assertIn("owner: anthony\n", new_text)


class TestDetectorAndMigrationToolAgree(unittest.TestCase):
    """Acceptance criterion: the lint guard and the migration tool share
    one detector implementation, verified against the same fixtures."""

    FIXTURES = [
        "instruction_source: discovered verifying PR #531\n",
        "acceptance:\n  - a bullet: with a colon\n",
        "title: `lrh validate` is broken\n",
        "commit: 7926567\n",
        "title: fine, nothing to see here\n",
        "evidence: []\n",
    ]

    def test_migrated_output_has_zero_lint_findings(self) -> None:
        for fixture in self.FIXTURES:
            with self.subTest(fixture=fixture):
                new_text, _fixes = frontmatter_migration.plan_fixes(fixture)
                self.assertEqual(frontmatter_lint.iter_unsafe_scalars(new_text), [])

    def test_fix_count_matches_finding_count(self) -> None:
        for fixture in self.FIXTURES:
            with self.subTest(fixture=fixture):
                findings = frontmatter_lint.iter_unsafe_scalars(fixture)
                _new_text, fixes = frontmatter_migration.plan_fixes(fixture)
                self.assertEqual(len(fixes), len(findings))


class TestFixFile(unittest.TestCase):
    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_dry_run_does_not_write(self) -> None:
        root = Path(tempfile.mkdtemp())
        path = root / "WI-1.md"
        original = "---\ncommit: 7926567\n---\n\nbody text\n"
        self._write(path, original)

        result = frontmatter_migration.fix_file(path, apply=False)

        self.assertTrue(result.changed)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_apply_writes_and_preserves_body(self) -> None:
        root = Path(tempfile.mkdtemp())
        path = root / "WI-1.md"
        self._write(
            path,
            "---\ncommit: 7926567\n---\n\nbody text stays exactly the same\n",
        )

        result = frontmatter_migration.fix_file(path, apply=True)

        self.assertTrue(result.changed)
        written = path.read_text(encoding="utf-8")
        self.assertIn("body text stays exactly the same\n", written)
        self.assertIn("commit: '7926567'\n", written)

    def test_clean_file_is_not_changed(self) -> None:
        root = Path(tempfile.mkdtemp())
        path = root / "WI-1.md"
        original = "---\ntitle: fine\n---\n\nbody\n"
        self._write(path, original)

        result = frontmatter_migration.fix_file(path, apply=True)

        self.assertFalse(result.changed)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_non_frontmatter_file_is_skipped(self) -> None:
        root = Path(tempfile.mkdtemp())
        path = root / "README.md"
        original = "# Just a regular doc\n"
        self._write(path, original)

        result = frontmatter_migration.fix_file(path, apply=True)

        self.assertFalse(result.changed)
        self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
