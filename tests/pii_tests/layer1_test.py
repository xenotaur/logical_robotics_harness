import unittest

from lrh.pii import config as pii_config
from lrh.pii import layer1


class FlagPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = pii_config.PiiConfig(
            path_globs=("*.pdf", "*.xlsx"),
            filename_keywords=("statement", "ssn"),
        )

    def test_flags_file_matching_a_default_glob(self) -> None:
        finding = layer1.flag_path("docs/notes.pdf", self.config)

        self.assertIsNotNone(finding)
        self.assertEqual(finding.rule_id, "path_glob.*.pdf")
        self.assertEqual(finding.matched_glob, "*.pdf")
        self.assertIsNone(finding.matched_keyword)

    def test_flags_file_matching_a_glob_case_insensitively(self) -> None:
        finding = layer1.flag_path("Scans/Bank_Report.PDF", self.config)

        self.assertIsNotNone(finding)
        self.assertEqual(finding.rule_id, "path_glob.*.pdf")

    def test_flags_file_matching_a_filename_keyword_case_insensitively(self) -> None:
        finding = layer1.flag_path("Bank_Statement_2026.txt", self.config)

        self.assertIsNotNone(finding)
        self.assertEqual(finding.rule_id, "filename_keyword.statement")
        self.assertEqual(finding.matched_keyword, "statement")
        self.assertIsNone(finding.matched_glob)

    def test_does_not_flag_ordinary_file(self) -> None:
        finding = layer1.flag_path("src/lrh/cli/main.py", self.config)

        self.assertIsNone(finding)

    def test_does_not_flag_contributor_listing_style_file(self) -> None:
        finding = layer1.flag_path("CODEOWNERS", self.config)

        self.assertIsNone(finding)

    def test_glob_match_takes_precedence_over_keyword_match(self) -> None:
        finding = layer1.flag_path("statement.pdf", self.config)

        self.assertEqual(finding.rule_id, "path_glob.*.pdf")


class FlagPathsTest(unittest.TestCase):
    def test_returns_a_finding_only_for_matching_paths(self) -> None:
        config = pii_config.PiiConfig(
            path_globs=("*.pdf",),
            filename_keywords=(),
        )

        findings = layer1.flag_paths(["a.py", "statement.pdf", "b.txt"], config)

        self.assertEqual([f.path for f in findings], ["statement.pdf"])


if __name__ == "__main__":
    unittest.main()
