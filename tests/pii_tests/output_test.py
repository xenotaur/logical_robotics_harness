import json
import pathlib
import subprocess
import tempfile
import unittest

from lrh.pii import allowlist as pii_allowlist
from lrh.pii import config as pii_config
from lrh.pii import layer1 as pii_layer1
from lrh.pii import layer2 as pii_layer2
from lrh.pii import output as pii_output


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


def _head(project_root: pathlib.Path) -> str:
    return subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _blob_sha(project_root: pathlib.Path, commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _config(content_scan_scope: str = pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT):
    return pii_config.PiiConfig(
        path_globs=pii_config.DEFAULT_PATH_GLOBS,
        filename_keywords=pii_config.DEFAULT_FILENAME_KEYWORDS,
        content_scan_scope=content_scan_scope,
    )


class BuildFindingsTest(unittest.TestCase):
    def test_layer1_finding_is_expanded_with_blob_sha_content_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "statement.pdf", "bank statement", "add")
            head = _head(project_root)

            layer1_findings = pii_layer1.flag_paths(["statement.pdf"], _config())
            findings = pii_output.build_findings(project_root, layer1_findings, [])

            self.assertEqual(len(findings), 1)
            finding = findings[0]
            self.assertEqual(finding.path, "statement.pdf")
            self.assertEqual(finding.matched_layer, pii_output.MATCHED_LAYER_1)
            self.assertEqual(finding.commit, head)
            self.assertEqual(
                finding.content_digest, _blob_sha(project_root, head, "statement.pdf")
            )
            self.assertTrue(finding.still_in_working_tree)

    def test_layer1_finding_produces_one_row_per_touching_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "statement.pdf", "v1", "add")
            first_commit = _head(project_root)
            _commit_file(project_root, "statement.pdf", "v2", "modify")
            second_commit = _head(project_root)

            layer1_findings = pii_layer1.flag_paths(["statement.pdf"], _config())
            findings = pii_output.build_findings(project_root, layer1_findings, [])

            self.assertEqual(
                {f.commit for f in findings}, {first_commit, second_commit}
            )
            self.assertFalse(
                [f for f in findings if f.commit == first_commit][
                    0
                ].still_in_working_tree
            )
            self.assertTrue(
                [f for f in findings if f.commit == second_commit][
                    0
                ].still_in_working_tree
            )

    def test_layer1_finding_keeps_pre_rename_commits_not_only_post_rename(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "bank data", "add notes")
            add_commit = _head(project_root)
            _run_git(project_root, "mv", "notes.txt", "passport.pdf")
            _run_git(project_root, "commit", "-q", "-m", "rename to passport")
            rename_commit = _head(project_root)

            # Layer1Finding.path is the current/canonical name
            # (passport.pdf); enumerate_commits_for_paths reports the
            # add commit under its historical pre-rename name
            # (notes.txt). build_findings must not drop that commit just
            # because its historical path differs from finding.path.
            layer1_findings = pii_layer1.flag_paths(["passport.pdf"], _config())
            findings = pii_output.build_findings(project_root, layer1_findings, [])

            self.assertEqual({f.commit for f in findings}, {add_commit, rename_commit})
            for finding in findings:
                self.assertEqual(finding.path, "passport.pdf")
                # Content never actually changed across the rename, so
                # both commits' blob SHA content_digest must match.
                self.assertEqual(
                    finding.content_digest,
                    _blob_sha(project_root, rename_commit, "passport.pdf"),
                )

    def test_layer2_finding_passes_through_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "jack@example.com", "add")
            head = _head(project_root)

            layer2_findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(),
            )
            findings = pii_output.build_findings(project_root, [], layer2_findings)

            self.assertEqual(len(findings), 1)
            finding = findings[0]
            self.assertEqual(finding.matched_layer, pii_output.MATCHED_LAYER_2)
            self.assertEqual(finding.commit, head)
            self.assertEqual(finding.content_digest, layer2_findings[0].content_digest)
            self.assertTrue(finding.still_in_working_tree)


class FilterAllowlistedTest(unittest.TestCase):
    def test_matching_fingerprint_is_suppressed(self) -> None:
        finding = pii_output.Finding(
            path="a.txt",
            rule_id="email.basic",
            category="email",
            severity="medium",
            confidence="high",
            commit="deadbeef",
            content_digest="abc123",
            still_in_working_tree=True,
            matched_layer=pii_output.MATCHED_LAYER_2,
        )
        fingerprint = pii_allowlist.compute_fingerprint(
            "a.txt", "email.basic", "abc123"
        )

        remaining = pii_output.filter_allowlisted([finding], frozenset({fingerprint}))

        self.assertEqual(remaining, [])

    def test_content_change_at_allowlisted_path_and_rule_produces_a_fresh_finding(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            _commit_file(project_root, "notes.txt", "kate@example.com", "benign email")

            approved_findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(),
            )
            approved_fingerprint = pii_allowlist.compute_fingerprint(
                approved_findings[0].path,
                approved_findings[0].rule_id,
                approved_findings[0].content_digest,
            )
            allowlist = frozenset({approved_fingerprint})

            # A later commit swaps in a genuinely different email at the
            # same path/rule - the scenario the content-bound fingerprint
            # exists to catch (PR #591 review, chatgpt-codex-connector).
            _commit_file(
                project_root, "notes.txt", "leaked-secret@example.com", "swap value"
            )
            all_findings = pii_layer2.content_findings_for_paths(
                project_root,
                flagged_paths=[],
                all_paths=["notes.txt"],
                config=_config(),
            )
            output_findings = pii_output.build_findings(project_root, [], all_findings)

            remaining = pii_output.filter_allowlisted(output_findings, allowlist)

            self.assertEqual(len(all_findings), 2)
            self.assertEqual(len(remaining), 1)
            self.assertNotEqual(
                remaining[0].content_digest, approved_findings[0].content_digest
            )

    def test_empty_allowlist_suppresses_nothing(self) -> None:
        finding = pii_output.Finding(
            path="a.txt",
            rule_id="email.basic",
            category="email",
            severity="medium",
            confidence="high",
            commit="deadbeef",
            content_digest="abc123",
            still_in_working_tree=True,
            matched_layer=pii_output.MATCHED_LAYER_2,
        )

        remaining = pii_output.filter_allowlisted([finding], frozenset())

        self.assertEqual(remaining, [finding])


class RenderTest(unittest.TestCase):
    def _finding(self) -> pii_output.Finding:
        return pii_output.Finding(
            path="a.txt",
            rule_id="email.basic",
            category="email",
            severity="medium",
            confidence="high",
            commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            content_digest="abc123",
            still_in_working_tree=True,
            matched_layer=pii_output.MATCHED_LAYER_2,
        )

    def test_render_json_matches_the_revised_schema(self) -> None:
        rendered = json.loads(pii_output.render_json([self._finding()]))

        self.assertEqual(len(rendered), 1)
        self.assertEqual(
            set(rendered[0]),
            {
                "path",
                "rule_id",
                "category",
                "severity",
                "confidence",
                "commit",
                "content_digest",
                "still_in_working_tree",
                "matched_layer",
            },
        )

    def test_render_text_summary_includes_disclosure_block(self) -> None:
        summary = pii_output.render_text_summary([self._finding()])

        self.assertIn(pii_output.DISCLOSURE_TEXT, summary)
        self.assertIn("a.txt", summary)

    def test_render_text_summary_includes_disclosure_block_with_no_findings(
        self,
    ) -> None:
        summary = pii_output.render_text_summary([])

        self.assertIn(pii_output.DISCLOSURE_TEXT, summary)
        self.assertIn("0 finding(s)", summary)


if __name__ == "__main__":
    unittest.main()
