import json
import pathlib
import stat
import tempfile
import unittest

from lrh.secrets import review


def _write_findings(out_dir: pathlib.Path, findings: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "findings.json").open("w") as f:
        json.dump(findings, f)


def _write_decisions(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class ReviewTest(unittest.TestCase):
    def test_unique_secrets_dedupes(self) -> None:
        findings = [
            {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
            {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
            {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
            {"Secret": "", "RuleID": "generic-api-key"},
        ]
        secrets = review.unique_secrets(findings)
        self.assertEqual(
            secrets,
            [
                ("sk-aaa", "***REMOVED-openai-api-key***"),
                ("sk-bbb", "***REMOVED-generic-api-key***"),
            ],
        )

    def test_load_findings_missing_report_raises(self) -> None:
        """A missing findings.json means scan was never run here -- this
        must never be silently treated as a clean, zero-finding scan."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(review.ReviewInputError):
                review.load_findings(pathlib.Path(tmp))

    def test_load_findings_existing_empty_report_is_valid_clean_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            (out_dir / "findings.json").touch()
            self.assertEqual(review.load_findings(out_dir), [])

    def test_load_findings_out_dir_not_a_directory_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            not_a_dir = pathlib.Path(tmp) / "nope"
            with self.assertRaises(review.ReviewInputError):
                review.load_findings(not_a_dir)

    def test_load_findings_malformed_json_raises_review_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            (out_dir / "findings.json").write_text("{not valid json")
            with self.assertRaises(review.ReviewInputError):
                review.load_findings(out_dir)

    def test_load_decisions_missing_path_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "decisions.yaml"
            with self.assertRaises(review.ReviewInputError):
                review.load_decisions(missing)

    def test_load_decisions_malformed_yaml_raises_review_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "decisions.yaml"
            path.write_text("sk-aaa: [this, is, not, a, mapping\n")
            with self.assertRaises(review.ReviewInputError):
                review.load_decisions(path)

    def test_load_decisions_non_mapping_entry_raises_review_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "decisions.yaml"
            path.write_text("sk-aaa: keep\n")
            with self.assertRaises(review.ReviewInputError):
                review.load_decisions(path)

    def test_report_undecided_when_no_decisions_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(out_dir, [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}])
            report = review.build_report(out_dir=out_dir, decisions_path=None)
            self.assertEqual(report.undecided(), ["sk-aaa"])
            self.assertEqual(report.kept(), [])

    def test_check_fails_when_finding_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(
                out_dir,
                [
                    {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
                    {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
                ],
            )
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path,
                "sk-aaa:\n  decision: keep\n  reason: real secret\n",
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), ["sk-bbb"])

    def test_check_passes_when_all_decided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(
                out_dir,
                [
                    {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
                    {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
                ],
            )
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path,
                "sk-aaa:\n  decision: keep\n  reason: real\n"
                "sk-bbb:\n  decision: ignore\n  reason: test fixture\n",
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), [])

    def test_invalid_decision_value_counts_as_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(out_dir, [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}])
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path, "sk-aaa:\n  decision: maybe\n  reason: unsure\n"
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), ["sk-aaa"])

    def test_decision_without_reason_counts_as_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(out_dir, [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}])
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(decisions_path, "sk-aaa:\n  decision: keep\n")
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), ["sk-aaa"])

    def test_decision_with_blank_reason_counts_as_undecided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(out_dir, [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}])
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path, "sk-aaa:\n  decision: keep\n  reason: '   '\n"
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), ["sk-aaa"])

    def test_invalidate_stale_reviewed_removes_leftover_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            stale = out_dir / "replacements.reviewed.txt"
            stale.write_text("# lrh-secrets-reviewed v1\nold-secret==>placeholder\n")
            review.invalidate_stale_reviewed(out_dir)
            self.assertFalse(stale.exists())

    def test_invalidate_stale_reviewed_is_noop_when_nothing_to_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            review.invalidate_stale_reviewed(out_dir)  # must not raise

    def test_apply_writes_reviewed_file_with_marker_and_only_kept_secrets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(
                out_dir,
                [
                    {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
                    {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
                ],
            )
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path,
                "sk-aaa:\n  decision: keep\n  reason: real\n"
                "sk-bbb:\n  decision: ignore\n  reason: test fixture\n",
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            self.assertEqual(report.undecided(), [])
            reviewed_path = review.write_reviewed_replacements(report, out_dir)

            self.assertEqual(reviewed_path, out_dir / "replacements.reviewed.txt")
            lines = reviewed_path.read_text().splitlines()
            self.assertEqual(lines[0], review.MARKER_LINE)
            self.assertEqual(lines[0], "# lrh-secrets-reviewed v1")
            self.assertIn("sk-aaa==>***REMOVED-openai-api-key***", lines)
            self.assertNotIn("sk-bbb==>***REMOVED-generic-api-key***", "\n".join(lines))
            # scan's draft is never overwritten by review
            self.assertFalse((out_dir / "replacements.txt").exists())

    def test_apply_output_is_0600(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = pathlib.Path(tmp)
            _write_findings(out_dir, [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}])
            decisions_path = out_dir / "decisions.yaml"
            _write_decisions(
                decisions_path, "sk-aaa:\n  decision: keep\n  reason: real\n"
            )
            report = review.build_report(out_dir=out_dir, decisions_path=decisions_path)
            reviewed_path = review.write_reviewed_replacements(report, out_dir)
            mode = stat.S_IMODE(reviewed_path.stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_format_text_no_findings(self) -> None:
        report = review.ReviewReport(secrets=[], decisions={})
        text = review.format_text(report)
        self.assertIn("0 unique secret(s)", text)
        self.assertIn("Nothing to review", text)


if __name__ == "__main__":
    unittest.main()
