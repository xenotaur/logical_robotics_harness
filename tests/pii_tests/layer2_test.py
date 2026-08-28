import pathlib
import subprocess
import tempfile
import unittest

from lrh.pii import config as pii_config
from lrh.pii import layer2 as pii_layer2


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


def _config(
    content_scan_scope: str = pii_config.CONTENT_SCAN_SCOPE_FLAGGED,
) -> pii_config.PiiConfig:
    return pii_config.PiiConfig(
        path_globs=pii_config.DEFAULT_PATH_GLOBS,
        filename_keywords=pii_config.DEFAULT_FILENAME_KEYWORDS,
        content_scan_scope=content_scan_scope,
    )


def _minimal_pdf(content_stream: bytes) -> bytes:
    return b"\n".join(
        [
            b"%PDF-1.4",
            b"1 0 obj << /Type /Pages /Count 1 >> endobj",
            b"2 0 obj << /Type /Page /Parent 1 0 R >> endobj",
            b"3 0 obj << /Length " + str(len(content_stream)).encode() + b" >>",
            b"stream",
            content_stream,
            b"endstream",
            b"endobj",
            b"trailer << /Root 4 0 R >>",
            b"%%EOF",
        ]
    )


class ContentFindingsForPathsTest(unittest.TestCase):
    def test_flagged_file_content_match_is_detected_under_default_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(
                project_root,
                "statement.pdf.txt",
                "contact: alice@example.com",
                "add statement",
            )

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=["statement.pdf.txt"],
                all_paths=["statement.pdf.txt"],
                config=_config(),
            )

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].category, "email")
            self.assertEqual(findings[0].path, "statement.pdf.txt")

    def test_ordinary_file_match_is_only_detected_under_all_text_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(
                project_root, "notes.txt", "contact: bob@example.com", "add notes"
            )

            # notes.txt is not Layer-1-flagged, so the default "flagged"
            # scope must not scan it even though it's in all_paths.
            flagged_findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_FLAGGED),
            )
            self.assertEqual(flagged_findings, [])

            all_text_findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT),
            )
            self.assertEqual(len(all_text_findings), 1)
            self.assertEqual(all_text_findings[0].category, "email")

    def test_all_text_scope_detects_pii_added_after_initial_benign_add(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "just some notes", "benign add")
            _commit_file(
                project_root, "notes.txt", "contact: carol@example.com", "add pii later"
            )
            _commit_file(project_root, "notes.txt", "cleaned up", "remove pii")

            # Per-commit enumeration (not just current working-tree content,
            # which is now PII-free) must still surface the middle commit's
            # email (PR #596 review, chatgpt-codex-connector P1).
            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT),
            )

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].category, "email")

    def test_pdf_content_is_scanned_via_pdf_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            pdf_bytes = _minimal_pdf(b"BT (dan@example.com) Tj ET")
            (project_root / "statement.pdf").write_bytes(pdf_bytes)
            _run_git(project_root, "add", "statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "add pdf statement")

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=["statement.pdf"],
                all_paths=["statement.pdf"],
                config=_config(),
            )

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].category, "email")

    def test_binary_content_is_skipped_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "data.bin").write_bytes(b"\x00\x01\xff\xfe\x00")
            _run_git(project_root, "add", "data.bin")
            _run_git(project_root, "commit", "-q", "-m", "add binary")

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=["data.bin"],
                all_paths=["data.bin"],
                config=_config(),
            )

            self.assertEqual(findings, [])

    def test_no_flagged_paths_scans_nothing_under_default_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "erin@example.com", "add notes")

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_FLAGGED),
            )

            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
