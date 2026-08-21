import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from lrh.secrets import purge
from lrh.secrets.review import MARKER_LINE


class LoadRefsTest(unittest.TestCase):
    def test_missing_refs_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "refs.txt"
            with self.assertRaises(purge.PurgeInputError):
                purge.load_refs(missing)

    def test_empty_refs_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            refs_file = pathlib.Path(tmp) / "refs.txt"
            refs_file.write_text("\n# just a comment\n\n")
            with self.assertRaises(purge.PurgeInputError):
                purge.load_refs(refs_file)

    def test_strips_comments_and_blanks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            refs_file = pathlib.Path(tmp) / "refs.txt"
            refs_file.write_text("refs/heads/main\n\n# comment\nrefs/heads/dev\n")
            self.assertEqual(
                purge.load_refs(refs_file), ["refs/heads/main", "refs/heads/dev"]
            )


class LoadStrippedReplacementsTest(unittest.TestCase):
    def test_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "replacements.reviewed.txt"
            with self.assertRaises(purge.PurgeInputError):
                purge.load_stripped_replacements(missing)

    def test_missing_marker_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "replacements.txt"
            path.write_text("sk-aaa==>***REMOVED-openai-api-key***\n")
            with self.assertRaises(purge.PurgeInputError):
                purge.load_stripped_replacements(path)

    def test_wrong_marker_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "replacements.txt"
            path.write_text(
                "# some-other-marker\nsk-aaa==>***REMOVED-openai-api-key***\n"
            )
            with self.assertRaises(purge.PurgeInputError):
                purge.load_stripped_replacements(path)

    def test_strips_marker_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "replacements.reviewed.txt"
            path.write_text(
                f"{MARKER_LINE}\nsk-aaa==>***REMOVED-openai-api-key***\n"
                "sk-bbb==>***REMOVED-generic-api-key***\n"
            )
            stripped = purge.load_stripped_replacements(path)
            self.assertEqual(
                stripped,
                [
                    "sk-aaa==>***REMOVED-openai-api-key***",
                    "sk-bbb==>***REMOVED-generic-api-key***",
                ],
            )


class SecretsFromReplacementsTest(unittest.TestCase):
    def test_extracts_secret_values(self) -> None:
        self.assertEqual(
            purge.secrets_from_replacements(
                ["sk-aaa==>***REMOVED-x***", "sk-bbb==>***REMOVED-y***"]
            ),
            ["sk-aaa", "sk-bbb"],
        )


class RunPurgeDryRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = pathlib.Path(self.tmp.name)
        self.refs_file = self.tmp_path / "refs.txt"
        self.refs_file.write_text("refs/heads/main\n")
        self.replacements_path = self.tmp_path / "replacements.reviewed.txt"
        self.replacements_path.write_text(f"{MARKER_LINE}\nsk-aaa==>***REMOVED-x***\n")

    @mock.patch("lrh.secrets.purge.mirror_clone")
    @mock.patch("lrh.secrets.purge.check_filter_repo_available")
    @mock.patch("lrh.secrets.purge.default_source", return_value="git@example.com:x")
    def test_dry_run_performs_no_clone(
        self, mock_default_source, mock_check_available, mock_clone
    ) -> None:
        output = purge.run_purge(
            project_root=self.tmp_path,
            source=None,
            refs_file=self.refs_file,
            replacements_path=self.replacements_path,
            mirror_dir=None,
            apply=False,
        )
        mock_clone.assert_not_called()
        mock_check_available.assert_called_once()
        self.assertIn("DRY RUN", output)


class DefaultSourceTest(unittest.TestCase):
    def test_no_origin_remote_raises_purge_input_error_not_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
            with self.assertRaises(purge.PurgeInputError):
                purge.default_source(tmp_path)


class RunPurgeApplyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = pathlib.Path(self.tmp.name)
        self.refs_file = self.tmp_path / "refs.txt"
        self.refs_file.write_text("refs/heads/main\n")
        self.replacements_path = self.tmp_path / "replacements.reviewed.txt"
        self.replacements_path.write_text(f"{MARKER_LINE}\nsk-aaa==>***REMOVED-x***\n")
        self.mirror_dir = self.tmp_path / "mirror"

    @mock.patch("lrh.secrets.purge.verify_clean", return_value=[])
    @mock.patch("lrh.secrets.purge.run_filter_repo")
    @mock.patch("lrh.secrets.purge.mirror_clone")
    @mock.patch("lrh.secrets.purge.check_filter_repo_available")
    def test_apply_success_prints_push_command_and_reminders(
        self, mock_check_available, mock_clone, mock_run_filter_repo, mock_verify
    ) -> None:
        output = purge.run_purge(
            project_root=self.tmp_path,
            source="git@example.com:x",
            refs_file=self.refs_file,
            replacements_path=self.replacements_path,
            mirror_dir=self.mirror_dir,
            apply=True,
        )
        mock_check_available.assert_called_once()
        mock_clone.assert_called_once_with("git@example.com:x", self.mirror_dir)
        mock_run_filter_repo.assert_called_once_with(
            self.mirror_dir, ["sk-aaa==>***REMOVED-x***"], ["refs/heads/main"]
        )
        self.assertIn(
            f"git -C {self.mirror_dir} push --force git@example.com:x refs/heads/main",
            output,
        )
        self.assertIn("Notify every collaborator", output)
        self.assertIn("host to purge cached views", output)

    @mock.patch("lrh.secrets.purge.verify_clean", return_value=["sk-aaa"])
    @mock.patch("lrh.secrets.purge.run_filter_repo")
    @mock.patch("lrh.secrets.purge.mirror_clone")
    @mock.patch("lrh.secrets.purge.check_filter_repo_available")
    def test_apply_failed_verification_hard_exits_no_push_command(
        self, mock_check_available, mock_clone, mock_run_filter_repo, mock_verify
    ) -> None:
        with self.assertRaises(SystemExit) as ctx:
            purge.run_purge(
                project_root=self.tmp_path,
                source="git@example.com:x",
                refs_file=self.refs_file,
                replacements_path=self.replacements_path,
                mirror_dir=self.mirror_dir,
                apply=True,
            )
        self.assertEqual(ctx.exception.code, 1)


class SecretStillPresentTest(unittest.TestCase):
    @mock.patch("subprocess.run")
    def test_never_passes_pickaxe_regex_and_matches_metacharacter_secret(
        self, mock_run
    ) -> None:
        mock_run.return_value = mock.Mock(stdout="deadbeef commit msg\n")
        found = purge.secret_still_present(pathlib.Path("/repo"), "ab+c")
        self.assertTrue(found)
        called_cmd = mock_run.call_args.args[0]
        self.assertNotIn("--pickaxe-regex", called_cmd)
        self.assertIn("-Sab+c", called_cmd)

    @mock.patch("subprocess.run")
    def test_clean_result_when_no_output(self, mock_run) -> None:
        mock_run.return_value = mock.Mock(stdout="")
        self.assertFalse(purge.secret_still_present(pathlib.Path("/repo"), "sk-aaa"))
