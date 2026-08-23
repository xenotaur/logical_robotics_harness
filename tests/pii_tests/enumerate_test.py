import pathlib
import subprocess
import tempfile
import unittest

from lrh.pii import enumerate as pii_enumerate


def _run_git(project_root: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(project_root), *args], check=True)


def _init_repo(project_root: pathlib.Path) -> None:
    # Explicitly pin the initial branch name so these fixtures (which
    # later `checkout main` by name) are independent of the local
    # `init.defaultBranch` config, which some environments still set to
    # "master" (PR #616 review, `chatgpt-codex-connector` P1).
    _run_git(project_root, "init", "-q", "-b", "main")
    _run_git(project_root, "config", "user.email", "test@example.com")
    _run_git(project_root, "config", "user.name", "test")


class EnumerateAddedPathsTest(unittest.TestCase):
    def test_enumerates_every_added_path_across_all_branches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "a.txt").write_text("hello")
            _run_git(project_root, "add", "a.txt")
            _run_git(project_root, "commit", "-q", "-m", "add a")
            (project_root / "statement.pdf").write_text("bank statement")
            _run_git(project_root, "add", "statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "add statement")

            paths = pii_enumerate.enumerate_added_paths(project_root)

            self.assertEqual(paths, ["a.txt", "statement.pdf"])

    def test_reports_both_the_add_name_and_the_rename_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "statement.pdf").write_text("bank statement")
            _run_git(project_root, "add", "statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "add statement")
            _run_git(project_root, "mv", "statement.pdf", "renamed_statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "rename statement")

            paths = pii_enumerate.enumerate_added_paths(project_root)

            # The rename destination must be a candidate too: a benign name
            # renamed to a suspicious one (e.g. notes.txt -> passport.pdf)
            # would otherwise never reach Layer 1 (PR #616 review,
            # `chatgpt-codex-connector` P1).
            self.assertEqual(paths, ["renamed_statement.pdf", "statement.pdf"])

    def test_finds_a_path_introduced_only_by_a_merge_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "main.txt").write_text("main")
            _run_git(project_root, "add", "main.txt")
            _run_git(project_root, "commit", "-q", "-m", "main commit")
            _run_git(project_root, "checkout", "-q", "-b", "feature")
            (project_root / "feature.txt").write_text("feature")
            _run_git(project_root, "add", "feature.txt")
            _run_git(project_root, "commit", "-q", "-m", "feature commit")
            _run_git(project_root, "checkout", "-q", "main")
            _run_git(project_root, "merge", "-q", "--no-ff", "--no-edit", "feature")
            (project_root / "merge_added.txt").write_text("merge-only file")
            _run_git(project_root, "add", "merge_added.txt")
            _run_git(project_root, "commit", "-q", "--amend", "--no-edit")

            paths = pii_enumerate.enumerate_added_paths(project_root)

            self.assertIn("merge_added.txt", paths)


class EnumerateCommitsForPathsTest(unittest.TestCase):
    def test_follows_rename_and_reports_the_historical_path_per_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "statement.pdf").write_text("bank statement")
            _run_git(project_root, "add", "statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "add statement")
            _run_git(project_root, "mv", "statement.pdf", "renamed_statement.pdf")
            _run_git(project_root, "commit", "-q", "-m", "rename statement")

            commits = pii_enumerate.enumerate_commits_for_paths(
                project_root, ["renamed_statement.pdf"]
            )

            self.assertEqual(len(commits), 2)
            # The add commit predates the rename, so `git show <commit>:<path>`
            # for it must use the pre-rename name, not the caller's input
            # path - the post-rename name did not exist yet at that commit
            # (PR #616 review, `chatgpt-codex-connector` P1).
            self.assertEqual(
                {c.path for c in commits}, {"statement.pdf", "renamed_statement.pdf"}
            )

    def test_finds_modification_on_a_non_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "a.txt").write_text("hello")
            _run_git(project_root, "add", "a.txt")
            _run_git(project_root, "commit", "-q", "-m", "add a")
            _run_git(project_root, "checkout", "-q", "-b", "feature")
            (project_root / "a.txt").write_text("hello\nmore")
            _run_git(project_root, "add", "a.txt")
            _run_git(project_root, "commit", "-q", "-m", "modify a on feature")

            commits = pii_enumerate.enumerate_commits_for_paths(project_root, ["a.txt"])

            self.assertEqual(len(commits), 2)

    def test_returns_empty_for_a_path_with_no_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "a.txt").write_text("hello")
            _run_git(project_root, "add", "a.txt")
            _run_git(project_root, "commit", "-q", "-m", "add a")

            commits = pii_enumerate.enumerate_commits_for_paths(
                project_root, ["never-existed.txt"]
            )

            self.assertEqual(commits, [])

    def test_finds_commit_for_a_path_introduced_only_by_a_merge_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "main.txt").write_text("main")
            _run_git(project_root, "add", "main.txt")
            _run_git(project_root, "commit", "-q", "-m", "main commit")
            _run_git(project_root, "checkout", "-q", "-b", "feature")
            (project_root / "feature.txt").write_text("feature")
            _run_git(project_root, "add", "feature.txt")
            _run_git(project_root, "commit", "-q", "-m", "feature commit")
            _run_git(project_root, "checkout", "-q", "main")
            _run_git(project_root, "merge", "-q", "--no-ff", "--no-edit", "feature")
            (project_root / "merge_added.txt").write_text("merge-only file")
            _run_git(project_root, "add", "merge_added.txt")
            _run_git(project_root, "commit", "-q", "--amend", "--no-edit")

            commits = pii_enumerate.enumerate_commits_for_paths(
                project_root, ["merge_added.txt"]
            )

            self.assertEqual(len(commits), 1)

    def test_accepts_an_arbitrary_path_set_not_only_flagged_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _init_repo(project_root)
            (project_root / "a.txt").write_text("hello")
            (project_root / "b.txt").write_text("world")
            _run_git(project_root, "add", "a.txt", "b.txt")
            _run_git(project_root, "commit", "-q", "-m", "add a and b")

            commits = pii_enumerate.enumerate_commits_for_paths(
                project_root, ["a.txt", "b.txt"]
            )

            self.assertEqual({c.path for c in commits}, {"a.txt", "b.txt"})


if __name__ == "__main__":
    unittest.main()
