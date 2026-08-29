import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

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
    def test_content_digest_differs_for_different_matched_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "gina@example.com", "add gina")
            _run_git(project_root, "mv", "notes.txt", "moved_notes.txt")
            _commit_file(
                project_root, "moved_notes.txt", "harry@example.com", "swap to harry"
            )

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt", "moved_notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT),
            )

            # Two different email values at the same rule (and, after the
            # rename, the same reportable path) must not collide on the
            # same content-bound digest - that's the whole point of
            # binding the digest to the matched substring, not just the
            # location (WI-PII-SCAN-ALLOWLIST-OUTPUT).
            digests = {f.content_digest for f in findings}
            self.assertEqual(len(findings), 2)
            self.assertEqual(len(digests), 2)

    def test_content_digest_is_identical_for_the_same_matched_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "irene@example.com", "add irene")
            _commit_file(
                project_root, "notes.txt", "irene@example.com\nmore", "unrelated edit"
            )

            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT),
            )

            self.assertEqual(len(findings), 2)
            self.assertEqual(findings[0].content_digest, findings[1].content_digest)

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

    def test_renamed_file_content_is_not_double_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "a.txt", "frank@example.com", "add a")
            _run_git(project_root, "mv", "a.txt", "b.txt")
            _run_git(project_root, "commit", "-q", "-m", "rename a to b")

            # Requesting both the pre- and post-rename name (as
            # enumerate_added_paths() normally returns for a rename) makes
            # enumerate_commits_for_paths() report the add commit under
            # (a.txt, add_commit) twice - once via each query. The rename
            # commit itself is a genuinely separate, real historical
            # revision (its tree contains b.txt's content), so it produces
            # its own finding, not a duplicate. Without deduplication this
            # scenario yields 3 findings (the add commit double-counted);
            # deduplicating by (commit, path) collapses it to the correct
            # 2 - one per real revision (PR #646 review,
            # chatgpt-codex-connector).
            findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["a.txt", "b.txt"],
                config=_config(pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT),
            )

            self.assertEqual(len(findings), 2)


class ReadContentAtCommitTest(unittest.TestCase):
    def test_returns_none_for_a_path_deleted_at_that_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "a.txt", "hello", "add a")
            _run_git(project_root, "rm", "-q", "a.txt")
            _run_git(project_root, "commit", "-q", "-m", "remove a")
            head = subprocess.run(
                ["git", "-C", str(project_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            content = pii_layer2._read_content_at_commit(project_root, head, "a.txt")

            self.assertIsNone(content)

    def test_unexpected_git_show_failure_raises_instead_of_skipping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "a.txt", "hello", "add a")
            head = subprocess.run(
                ["git", "-C", str(project_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            fake_result = subprocess.CompletedProcess(
                args=[],
                returncode=128,
                stdout=b"",
                stderr=b"fatal: bad object deadbeef",
            )
            with mock.patch.object(
                pii_layer2.subprocess, "run", return_value=fake_result
            ):
                with self.assertRaises(pii_layer2.Layer2ContentReadError):
                    pii_layer2._read_content_at_commit(project_root, head, "a.txt")


if __name__ == "__main__":
    unittest.main()
