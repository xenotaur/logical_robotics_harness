import io
import json
import pathlib
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from lrh.secrets import scan


def _write_report(report_path: pathlib.Path, findings: list[dict]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as f:
        json.dump(findings, f)


class ScanTest(unittest.TestCase):
    def test_draft_replacements_dedupes_by_secret(self) -> None:
        findings = [
            {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
            {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
            {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
            {"Secret": "", "RuleID": "generic-api-key"},
        ]
        replacements = scan.draft_replacements(findings)
        self.assertEqual(
            replacements,
            [
                ("sk-aaa", "***REMOVED-openai-api-key***"),
                ("sk-bbb", "***REMOVED-generic-api-key***"),
            ],
        )

    def test_load_findings_missing_or_empty_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "findings.json"
            self.assertEqual(scan.load_findings(missing), [])

            empty = pathlib.Path(tmp) / "empty.json"
            empty.touch()
            self.assertEqual(scan.load_findings(empty), [])

    def test_check_gitleaks_available_missing_binary_fails_fast(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("lrh.secrets.scan.shutil.which", return_value=None):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    scan.check_gitleaks_available()
        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("gitleaks", stderr.getvalue())

    def test_run_scan_no_findings_does_not_write_replacements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            out_dir = pathlib.Path(tmp) / "out"
            project_root.mkdir()

            def fake_run(cmd, check):
                report_path = pathlib.Path(cmd[cmd.index("--report-path") + 1])
                _write_report(report_path, [])
                return mock.Mock(returncode=0)

            with mock.patch(
                "lrh.secrets.scan.shutil.which", return_value="/usr/bin/gitleaks"
            ):
                with mock.patch(
                    "lrh.secrets.scan.subprocess.run", side_effect=fake_run
                ):
                    result = scan.run_scan(project_root=project_root, out_dir=out_dir)

            self.assertEqual(result.findings_count, 0)
            self.assertIsNone(result.replacements_path)
            self.assertTrue((out_dir / "findings.json").exists())
            self.assertFalse((out_dir / "replacements.txt").exists())

    def test_run_scan_with_findings_writes_deduped_replacements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            out_dir = pathlib.Path(tmp) / "out"
            project_root.mkdir()

            findings = [
                {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
                {"Secret": "sk-aaa", "RuleID": "openai-api-key"},
                {"Secret": "sk-bbb", "RuleID": "generic-api-key"},
            ]

            def fake_run(cmd, check):
                report_path = pathlib.Path(cmd[cmd.index("--report-path") + 1])
                _write_report(report_path, findings)
                return mock.Mock(returncode=0)

            with mock.patch(
                "lrh.secrets.scan.shutil.which", return_value="/usr/bin/gitleaks"
            ):
                with mock.patch(
                    "lrh.secrets.scan.subprocess.run", side_effect=fake_run
                ):
                    result = scan.run_scan(project_root=project_root, out_dir=out_dir)

            self.assertEqual(result.findings_count, 3)
            self.assertEqual(result.replacements_count, 2)
            replacements_text = (out_dir / "replacements.txt").read_text()
            self.assertIn("sk-aaa==>***REMOVED-openai-api-key***", replacements_text)
            self.assertIn("sk-bbb==>***REMOVED-generic-api-key***", replacements_text)
            self.assertEqual(replacements_text.count("sk-aaa"), 1)

    def test_run_scan_writes_findings_and_replacements_as_0600(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            out_dir = pathlib.Path(tmp) / "out"
            project_root.mkdir()

            findings = [{"Secret": "sk-aaa", "RuleID": "openai-api-key"}]

            def fake_run(cmd, check):
                report_path = pathlib.Path(cmd[cmd.index("--report-path") + 1])
                _write_report(report_path, findings)
                return mock.Mock(returncode=0)

            with mock.patch(
                "lrh.secrets.scan.shutil.which", return_value="/usr/bin/gitleaks"
            ):
                with mock.patch(
                    "lrh.secrets.scan.subprocess.run", side_effect=fake_run
                ):
                    scan.run_scan(project_root=project_root, out_dir=out_dir)

            for name in ("findings.json", "replacements.txt"):
                mode = stat.S_IMODE((out_dir / name).stat().st_mode)
                self.assertEqual(
                    mode, 0o600, f"{name} should be user-only readable/writable"
                )

    def test_run_scan_removes_stale_replacements_on_clean_rescan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            out_dir = pathlib.Path(tmp) / "out"
            project_root.mkdir()
            out_dir.mkdir()
            stale = out_dir / "replacements.txt"
            stale.write_text("old-secret==>***REMOVED-old-rule***\n")

            def fake_run(cmd, check):
                report_path = pathlib.Path(cmd[cmd.index("--report-path") + 1])
                _write_report(report_path, [])
                return mock.Mock(returncode=0)

            with mock.patch(
                "lrh.secrets.scan.shutil.which", return_value="/usr/bin/gitleaks"
            ):
                with mock.patch(
                    "lrh.secrets.scan.subprocess.run", side_effect=fake_run
                ):
                    result = scan.run_scan(project_root=project_root, out_dir=out_dir)

            self.assertEqual(result.findings_count, 0)
            self.assertIsNone(result.replacements_path)
            self.assertFalse(
                stale.exists(), "stale draft with old secrets must be removed"
            )

    def test_run_gitleaks_never_suppresses_gitleaks_toml_auto_discovery(self) -> None:
        """Regression guard: never pass a flag that would override or suppress
        gitleaks' automatic discovery of a target repo's own .gitleaks.toml."""
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            report_path = pathlib.Path(tmp) / "out" / "findings.json"
            project_root.mkdir()
            report_path.parent.mkdir()

            captured_cmd = []

            def fake_run(cmd, check):
                captured_cmd.extend(cmd)
                _write_report(report_path, [])
                return mock.Mock(returncode=0)

            with mock.patch("lrh.secrets.scan.subprocess.run", side_effect=fake_run):
                scan.run_gitleaks(project_root, report_path)

            for forbidden in ("--config", "--no-config", "--no-git"):
                self.assertNotIn(
                    forbidden,
                    captured_cmd,
                    f"gitleaks command must never pass {forbidden}",
                )

    def test_format_text_no_findings(self) -> None:
        result = scan.ScanResult(0, 0, pathlib.Path("findings.json"), None)
        text = scan.format_text(result)
        self.assertIn("found 0 finding(s)", text)
        self.assertIn("Nothing to review", text)

    def test_format_text_with_findings_mentions_review(self) -> None:
        result = scan.ScanResult(
            2, 2, pathlib.Path("findings.json"), pathlib.Path("replacements.txt")
        )
        text = scan.format_text(result)
        self.assertIn("lrh secrets review", text)

    def test_format_json_round_trips(self) -> None:
        result = scan.ScanResult(
            1, 1, pathlib.Path("findings.json"), pathlib.Path("replacements.txt")
        )
        data = json.loads(scan.format_json(result))
        self.assertEqual(data["findings_count"], 1)
        self.assertEqual(data["replacements_count"], 1)
        self.assertEqual(data["replacements_path"], "replacements.txt")

        result_none = scan.ScanResult(0, 0, pathlib.Path("findings.json"), None)
        data_none = json.loads(scan.format_json(result_none))
        self.assertIsNone(data_none["replacements_path"])


if __name__ == "__main__":
    unittest.main()
