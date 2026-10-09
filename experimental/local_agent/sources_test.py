import pathlib
import tempfile
import unittest
from unittest import mock

from local_agent import sources, testing_support


class SourcesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.commit = testing_support.make_repo(self.repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make(self, path: str, max_bytes: int = 100_000) -> tuple:
        return sources.make_source(
            repo=self.repo,
            repo_label="TEST",
            commit=self.commit,
            project_dir=".",
            project_relative_path=path,
            source_id="S1",
            relation="WorkItem",
            max_bytes=max_bytes,
        )

    def test_reads_tracked_file_with_provenance(self) -> None:
        ref, text = self._make("project/work_items/proposed/WI-T-1.md")
        self.assertEqual(ref.commit, self.commit)
        self.assertEqual(ref.line_start, 1)
        self.assertEqual(ref.line_end, ref.total_lines)
        self.assertFalse(ref.truncated)
        self.assertEqual(len(ref.sha256), 64)
        self.assertIn("Ready fixture item", text)

    def test_working_tree_edits_do_not_leak(self) -> None:
        path = self.repo / "project/work_items/proposed/WI-T-1.md"
        path.write_text("DIRTY UNCOMMITTED CONTENT\n", encoding="utf-8")
        _, text = self._make("project/work_items/proposed/WI-T-1.md")
        self.assertNotIn("DIRTY", text)

    def test_untracked_file_rejected(self) -> None:
        (self.repo / "project/untracked.md").write_text("x\n", encoding="utf-8")
        with self.assertRaises(sources.SourceError):
            self._make("project/untracked.md")

    def test_excluded_private_prefix_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "excluded"):
            self._make("project/executions/AD_HOC/private.md")

    def test_private_paths_rejected_at_any_depth_and_case(self) -> None:
        for path in (
            "sub/project/executions/AD_HOC/x.md",
            "Project/Executions/x.md",
            "lcats/PROJECT/memory/m.md",
        ):
            with self.subTest(path):
                with self.assertRaisesRegex(sources.SourceError, "private path"):
                    sources.check_path_allowed(path)

    def test_control_characters_in_paths_rejected_without_echo(self) -> None:
        for path in (
            "safe\ntoken: abcdef123.py",
            "a\tb.py",
            "x\x7f.py",
            "c\x9bd.py",
            "line\u2028sep.py",
            "para\u2029sep.py",
            "evil\u202egpj.py",
            "zero\u200bwidth.py",
            "\ufeffbom.py",
        ):
            with self.subTest(repr(path)):
                with self.assertRaises(sources.SourceError) as caught:
                    sources.check_path_allowed(path)
                self.assertNotIn("abcdef123", str(caught.exception))

    def test_shown_path_quotes_unicode_separators_and_bidi(self) -> None:
        self.assertEqual(sources.shown_path("ok/path.py"), "ok/path.py")
        self.assertEqual(sources.shown_path("caf\u00e9.md"), "caf\u00e9.md")
        for path in ("a\u2028b", "a\u202eb"):
            with self.subTest(repr(path)):
                shown = sources.shown_path(path)
                self.assertTrue(shown.isascii())
                self.assertNotEqual(shown, path)

    def test_credential_like_paths_rejected(self) -> None:
        for path in (
            ".env",
            "config/.env.local",
            ".envrc",
            "deploy/.env_prod",
            "config/secrets/prod.yaml",
            "Credentials/gcp.json",
            "keys/server.PEM",
            "home/id_rsa",
            "ops/aws_credentials.json",
            "notes/my-secret.md",
            ".npmrc",
        ):
            with self.subTest(path):
                with self.assertRaisesRegex(sources.SourceError, "credential-like"):
                    sources.check_path_allowed(path)
        sources.check_path_allowed("project/design/demo.md")

    def test_sensitivity_flagged_text_rejected_without_echoing_it(self) -> None:
        with self.assertRaises(sources.SourceError) as caught:
            sources.check_text_allowed(
                "x.md", "api_key = sk-live-abcdef0123456789abcdef\n"
            )
        self.assertIn("sensitivity scan", str(caught.exception))
        self.assertNotIn("sk-live", str(caught.exception))
        self.assertEqual(sources.check_text_allowed("ok.md", "plain text\n"), ())

    def test_medium_only_text_allowed_with_category_warnings(self) -> None:
        warnings = sources.check_text_allowed(
            "notes.md", "Mail ops@example.org; serve on 127.0.0.1.\n"
        )
        self.assertEqual(warnings, ("email", "ip_address"))

    def test_high_finding_excludes_even_with_medium_findings(self) -> None:
        text = "ops@example.org\napi_key = sk-live-abcdef0123456789abcdef\n"
        with self.assertRaises(sources.SourceError) as caught:
            sources.check_text_allowed("mixed.md", text)
        message = str(caught.exception)
        self.assertIn("secret", message)
        self.assertNotIn("email", message)
        self.assertNotIn("ops@example.org", message)

    def test_high_findings_are_structured_and_value_free(self) -> None:
        records = sources.high_findings(
            "x = 1\ntoken: Callable[[], str] = make_token\n"
            "if secret:\n    keep(secret)\n"
        )
        self.assertEqual(
            records,
            [
                {
                    "category": "secret",
                    "rule_id": "secret.keyword_assignment",
                    "start_line": 2,
                    "end_line": 2,
                },
                {
                    "category": "secret",
                    "rule_id": "secret.keyword_assignment",
                    "start_line": 3,
                    "end_line": 4,
                },
            ],
        )

    def test_allow_lifts_only_the_named_categories(self) -> None:
        mixed = 'api_key = "sk-live-abcdef0123456789abcdef"\n'
        with self.assertRaisesRegex(sources.SourceError, r"\(token\)"):
            sources.check_text_allowed("m.py", mixed, frozenset({"secret"}))
        self.assertEqual(
            sources.check_text_allowed("m.py", mixed, frozenset({"secret", "token"})),
            ("secret", "token"),
        )

    def test_binary_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "binary"):
            self._make("project/data.bin")

    def test_traversal_rejected(self) -> None:
        with self.assertRaisesRegex(sources.SourceError, "confined"):
            self._make("../outside.md")
        with self.assertRaisesRegex(sources.SourceError, "confined"):
            self._make("/etc/passwd")

    def test_truncates_on_line_boundary(self) -> None:
        ref, text = self._make("project/design/demo.md", max_bytes=60)
        self.assertTrue(ref.truncated)
        self.assertLess(ref.line_end, ref.total_lines)
        self.assertTrue(text.endswith("\n"))
        self.assertLessEqual(len(text.encode("utf-8")), 60)
        self.assertEqual(ref.included_bytes, len(text.encode("utf-8")))

    def test_line_splitting_matches_git_line_numbers(self) -> None:
        self.assertEqual(
            sources.split_lines("a\x0cb\nc\u2028d\ne"), ["a\x0cb\n", "c\u2028d\n", "e"]
        )
        self.assertEqual(sources.split_lines(""), [])
        self.assertEqual(sources.split_lines("x\n"), ["x\n"])

    def test_materialize_refuses_without_safe_tar_filters(self) -> None:
        with mock.patch.object(sources.tarfile, "data_filter", create=True):
            del sources.tarfile.data_filter
            with tempfile.TemporaryDirectory() as out:
                with self.assertRaisesRegex(sources.SourceError, "3.11.4"):
                    sources.materialize_project_tree(
                        self.repo, self.commit, ".", pathlib.Path(out)
                    )
        self.assertTrue(hasattr(sources.tarfile, "data_filter"))

    def test_materialize_extracts_only_tracked_tree(self) -> None:
        (self.repo / "project/untracked.md").write_text("x\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as out:
            root = sources.materialize_project_tree(
                self.repo, self.commit, ".", pathlib.Path(out)
            )
            self.assertTrue((root / "project/work_items/proposed/WI-T-1.md").exists())
            self.assertFalse((root / "project/untracked.md").exists())


if __name__ == "__main__":
    unittest.main()
