import json
import pathlib
import subprocess
import tempfile
import unittest

from lrh.pii import allowlist as pii_allowlist
from lrh.pii import output as pii_output
from lrh.pii import scan as pii_scan


def _run_git(project_root: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(project_root), *args], check=True)


def _init_repo(project_root: pathlib.Path) -> None:
    _run_git(project_root, "init", "-q", "-b", "main")
    _run_git(project_root, "config", "user.email", "test@example.com")
    _run_git(project_root, "config", "user.name", "test")


def _commit_file(
    project_root: pathlib.Path, path: str, content: str, message: str
) -> None:
    (project_root / path).write_text(content)
    _run_git(project_root, "add", path)
    _run_git(project_root, "commit", "-q", "-m", message)


class RunScanTest(unittest.TestCase):
    def test_writes_pii_findings_json_with_layer1_and_layer2_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            project_root.mkdir()
            _init_repo(project_root)
            _commit_file(
                project_root, "statement.pdf.txt", "contact: alice@example.com", "add"
            )
            out_dir = pathlib.Path(tmp) / "out"

            result = pii_scan.run_scan(project_root, out_dir)

            self.assertTrue(result.findings_path.exists())
            rendered = json.loads(result.findings_path.read_text())
            self.assertEqual(len(rendered), result.findings_count)
            matched_layers = {finding["matched_layer"] for finding in rendered}
            self.assertIn("path", matched_layers)
            self.assertIn("content", matched_layers)

    def test_allowlisted_finding_is_suppressed_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            project_root.mkdir()
            _init_repo(project_root)
            _commit_file(project_root, "statement.pdf", "bank statement", "add")

            out_dir = pathlib.Path(tmp) / "out"
            first_pass = pii_scan.run_scan(project_root, out_dir)
            findings = json.loads(first_pass.findings_path.read_text())
            path_finding = next(f for f in findings if f["matched_layer"] == "path")
            fingerprint = pii_allowlist.compute_fingerprint(
                path_finding["path"],
                path_finding["rule_id"],
                path_finding["content_digest"],
            )
            (project_root / pii_allowlist.ALLOWLIST_FILENAME).write_text(
                f"{fingerprint}\n"
            )

            second_pass = pii_scan.run_scan(project_root, out_dir)

            self.assertEqual(second_pass.findings_count, first_pass.findings_count - 1)
            self.assertEqual(second_pass.allowlisted_count, 1)

    def test_config_path_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            project_root.mkdir()
            _init_repo(project_root)
            _commit_file(project_root, "report.docx", "quarterly numbers", "add")
            custom_config = pathlib.Path(tmp) / "custom.toml"
            custom_config.write_text(
                'path_globs = ["*.docx"]\n[extend]\nuseDefault = false\n'
            )
            out_dir = pathlib.Path(tmp) / "out"

            result = pii_scan.run_scan(project_root, out_dir, config_path=custom_config)

            findings = json.loads(result.findings_path.read_text())
            self.assertTrue(any(f["path"] == "report.docx" for f in findings))

    def test_no_findings_writes_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp) / "repo"
            project_root.mkdir()
            _init_repo(project_root)
            _commit_file(project_root, "readme.md", "hello world", "add")
            out_dir = pathlib.Path(tmp) / "out"

            result = pii_scan.run_scan(project_root, out_dir)

            self.assertEqual(result.findings_count, 0)
            self.assertEqual(json.loads(result.findings_path.read_text()), [])


def _fake_finding(path: str = "a.txt") -> pii_output.Finding:
    return pii_output.Finding(
        path=path,
        rule_id="email.basic",
        category="email",
        severity="medium",
        confidence="high",
        commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        content_digest="abc123",
        still_in_working_tree=True,
        matched_layer=pii_output.MATCHED_LAYER_2,
    )


class FormatTest(unittest.TestCase):
    def test_format_text_includes_disclosure_counts_and_finding_details(self) -> None:
        result = pii_scan.ScanResult(
            findings_count=2,
            allowlisted_count=1,
            findings_path=pathlib.Path("/tmp/pii_findings.json"),
            findings=(_fake_finding("a.txt"), _fake_finding("b.txt")),
        )

        text = pii_scan.format_text(result)

        self.assertIn("2 finding(s)", text)
        self.assertIn("1 allowlisted finding(s)", text)
        self.assertIn("a.txt", text)
        self.assertIn("b.txt", text)
        self.assertIn(pii_output.DISCLOSURE_TEXT, text)

    def test_format_json_matches_expected_keys(self) -> None:
        result = pii_scan.ScanResult(
            findings_count=0,
            allowlisted_count=0,
            findings_path=pathlib.Path("/tmp/pii_findings.json"),
            findings=(),
        )

        rendered = json.loads(pii_scan.format_json(result))

        self.assertEqual(
            set(rendered), {"findings_count", "allowlisted_count", "findings_path"}
        )


if __name__ == "__main__":
    unittest.main()
