import pathlib
import shlex
import subprocess
import tempfile
import unittest

from lrh import branch_hygiene


def _run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_origin(
    parent: pathlib.Path, *, default_branch: str = "main"
) -> pathlib.Path:
    """Init a repo with a local bare 'origin' remote and origin/HEAD set.

    The bare remote is a *sibling* of the working tree, not nested inside
    it -- a bare repo has no `.git` marker of its own, so git cannot tell
    it apart from an ordinary directory of files. Nesting it inside the
    working tree let an in-test `git add -A` track its raw contents as
    plain tracked files on one branch; a later `git checkout` to a branch
    that never had those files then deleted them from disk -- including
    the remote's own `HEAD` -- as an ordinary "remove files not in the
    target tree" side effect, corrupting the fixture out from under the
    test with no error at add- or checkout-time.
    """
    root = parent / "work"
    root.mkdir()
    remote = parent / "remote_bare.git"
    remote.mkdir()
    _run(["git", "init", "-q", "--bare"], remote)

    _run(["git", "init", "-q", "-b", default_branch], root)
    _run(["git", "config", "user.email", "test@example.com"], root)
    _run(["git", "config", "user.name", "Test"], root)
    (root / "a.txt").write_text("a\n")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-q", "-m", "init"], root)
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-q", "-u", "origin", default_branch], root)
    _run(["git", "remote", "set-head", "origin", default_branch], root)
    return root


def _make_branch(
    root: pathlib.Path, name: str, *, push: bool = False, from_ref: str = "main"
) -> str:
    _run(["git", "branch", name, from_ref], root)
    if push:
        _run(["git", "push", "-q", "-u", "origin", f"{name}:{name}"], root)
    result = _run(["git", "rev-parse", name], root)
    return result.stdout.strip()


class QuoteAndRenderTest(unittest.TestCase):
    def test_quote_round_trips_a_plain_name(self) -> None:
        quoted = branch_hygiene.quote_branch_name("feature/thing")
        self.assertEqual(shlex.split(quoted), ["feature/thing"])

    def test_quote_neutralizes_shell_metacharacters(self) -> None:
        hostile = "$(touch PWN)"
        quoted = branch_hygiene.quote_branch_name(hostile)
        # Round-tripping through shlex.split must reproduce the exact
        # original string as a single argument -- proof the shell cannot
        # execute the substitution when this text is interpolated into a
        # command line and run by a POSIX shell.
        self.assertEqual(shlex.split(quoted), [hostile])
        self.assertNotEqual(quoted, hostile)

    def test_quote_neutralizes_semicolon_injection(self) -> None:
        hostile = "foo;echo PWN"
        quoted = branch_hygiene.quote_branch_name(hostile)
        self.assertEqual(shlex.split(quoted), [hostile])

    def test_render_delete_command_uses_option_terminator(self) -> None:
        info = branch_hygiene.BranchInfo(
            name="-rf",
            branch_class=branch_hygiene.BranchClass.MERGED_OR_EMPTY,
            reason="ancestor",
            has_upstream=True,
        )
        command = branch_hygiene.render_delete_command(info)
        self.assertIsNotNone(command)
        assert command is not None
        self.assertIn(" -- ", command)
        self.assertTrue(command.startswith("git branch -d -- "))

    def test_render_delete_command_none_for_report_only_class(self) -> None:
        info = branch_hygiene.BranchInfo(
            name="wip",
            branch_class=branch_hygiene.BranchClass.REVIEW_FIRST,
            reason="ambiguous",
            has_upstream=False,
        )
        self.assertIsNone(branch_hygiene.render_delete_command(info))

    def test_squash_merged_uses_capital_d(self) -> None:
        info = branch_hygiene.BranchInfo(
            name="squashed",
            branch_class=branch_hygiene.BranchClass.SQUASH_MERGED,
            reason="tip matches merged PR head",
            has_upstream=True,
            merged_pr_number=42,
        )
        command = branch_hygiene.render_delete_command(info)
        assert command is not None
        self.assertTrue(command.startswith("git branch -D -- "))


class ClassifyBranchPrecedenceTest(unittest.TestCase):
    def _classify(self, **overrides: object) -> branch_hygiene.BranchInfo:
        defaults: dict[str, object] = dict(
            name="b",
            is_default=False,
            in_worktree=False,
            is_ancestor_of_default=False,
            has_upstream=True,
            tip="deadbeef",
            prs=(),
        )
        defaults.update(overrides)
        return branch_hygiene.classify_branch(**defaults)  # type: ignore[arg-type]

    def test_default_branch_always_wins(self) -> None:
        # Even when every other signal says "delete me," is_default wins.
        info = self._classify(
            is_default=True,
            in_worktree=True,
            is_ancestor_of_default=True,
        )
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.DEFAULT)
        self.assertIsNone(info.delete_flag)

    def test_in_worktree_beats_merged_or_empty(self) -> None:
        info = self._classify(in_worktree=True, is_ancestor_of_default=True)
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.IN_WORKTREE)
        self.assertIsNone(info.delete_flag)

    def test_in_worktree_beats_squash_merged(self) -> None:
        pr = branch_hygiene._PrRecord(number=1, state="MERGED", head_ref_oid="deadbeef")
        info = self._classify(in_worktree=True, prs=(pr,))
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.IN_WORKTREE)

    def test_open_pr_beats_merged_or_empty(self) -> None:
        pr = branch_hygiene._PrRecord(number=2, state="OPEN", head_ref_oid="other")
        info = self._classify(is_ancestor_of_default=True, prs=(pr,))
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.OPEN_PR)
        self.assertEqual(info.open_pr_numbers, (2,))

    def test_merged_or_empty(self) -> None:
        info = self._classify(is_ancestor_of_default=True)
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.MERGED_OR_EMPTY)
        self.assertEqual(info.delete_flag, "-d")

    def test_squash_merged_requires_tip_match(self) -> None:
        pr = branch_hygiene._PrRecord(number=3, state="MERGED", head_ref_oid="deadbeef")
        info = self._classify(tip="deadbeef", prs=(pr,))
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.SQUASH_MERGED)
        self.assertEqual(info.delete_flag, "-D")
        self.assertEqual(info.merged_pr_number, 3)

    def test_merged_pr_with_different_tip_does_not_match(self) -> None:
        pr = branch_hygiene._PrRecord(
            number=3, state="MERGED", head_ref_oid="unrelated"
        )
        info = self._classify(tip="deadbeef", prs=(pr,), has_upstream=True)
        # No ancestor, no tip match, has upstream, has PR history (closed
        # analog via non-matching merged record) -> review-first, not a
        # guessed delete.
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.REVIEW_FIRST)
        self.assertIsNone(info.delete_flag)

    def test_never_pushed_no_pr_is_review_first(self) -> None:
        info = self._classify(has_upstream=False)
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.REVIEW_FIRST)
        self.assertIsNone(info.delete_flag)

    def test_pushed_no_pr_history_is_unique_work(self) -> None:
        info = self._classify(has_upstream=True, prs=())
        self.assertEqual(info.branch_class, branch_hygiene.BranchClass.UNIQUE_WORK)
        self.assertIsNone(info.delete_flag)


class RenderDeleteCommandsFileTest(unittest.TestCase):
    def test_default_branch_never_appears_at_all(self) -> None:
        default_info = branch_hygiene.BranchInfo(
            name="main",
            branch_class=branch_hygiene.BranchClass.DEFAULT,
            reason="default",
            has_upstream=True,
        )
        other = branch_hygiene.BranchInfo(
            name="stale",
            branch_class=branch_hygiene.BranchClass.MERGED_OR_EMPTY,
            reason="ancestor",
            has_upstream=True,
        )
        content = branch_hygiene.render_delete_commands_file([default_info, other])
        self.assertNotIn("main", content)
        self.assertIn("git branch -d -- stale", content)

    def test_default_branch_excluded_even_when_checked_out(self) -> None:
        # Simulates the exact scenario the review comments flagged: a
        # feature branch is checked out, so the default branch is an
        # ancestor of HEAD -- but classify_branch already assigns it
        # BranchClass.DEFAULT (is_default short-circuits everything
        # else), so it can never reach this renderer as merged_or_empty
        # in the first place. This test locks that contract at the
        # rendering layer too.
        default_info = branch_hygiene.BranchInfo(
            name="main",
            branch_class=branch_hygiene.BranchClass.DEFAULT,
            reason="discovered repository default branch; never delete-eligible",
            has_upstream=True,
        )
        content = branch_hygiene.render_delete_commands_file([default_info])
        self.assertNotIn("git branch -d", content)
        self.assertNotIn("git branch -D", content)
        self.assertNotIn("main", content)

    def test_review_first_is_commented_out(self) -> None:
        info = branch_hygiene.BranchInfo(
            name="wip",
            branch_class=branch_hygiene.BranchClass.REVIEW_FIRST,
            reason="ambiguous",
            has_upstream=False,
        )
        content = branch_hygiene.render_delete_commands_file([info])
        self.assertIn("# git branch -d -- wip", content)

    def test_hostile_refname_is_quoted_in_generated_file(self) -> None:
        hostile = "$(touch PWN)"
        info = branch_hygiene.BranchInfo(
            name=hostile,
            branch_class=branch_hygiene.BranchClass.MERGED_OR_EMPTY,
            reason="ancestor",
            has_upstream=True,
        )
        content = branch_hygiene.render_delete_commands_file([info])
        self.assertNotIn(f" {hostile} ", content)
        quoted = branch_hygiene.quote_branch_name(hostile)
        self.assertIn(quoted, content)


class RealGitDiscoveryTest(unittest.TestCase):
    def test_discover_default_branch_is_not_hardcoded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))
            git_runner = branch_hygiene.default_git_runner(str(root))
            self.assertEqual(branch_hygiene.discover_default_branch(git_runner), "main")

    def test_discover_default_branch_works_for_non_main_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp), default_branch="trunk")
            git_runner = branch_hygiene.default_git_runner(str(root))
            self.assertEqual(
                branch_hygiene.discover_default_branch(git_runner), "trunk"
            )

    def test_discover_default_branch_raises_without_origin_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _run(["git", "init", "-q", "-b", "main"], root)
            git_runner = branch_hygiene.default_git_runner(str(root))
            with self.assertRaises(branch_hygiene.BranchHygieneError):
                branch_hygiene.discover_default_branch(git_runner)

    def test_discover_worktree_branches_finds_every_checked_out_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))
            _make_branch(root, "wt-branch")
            _make_branch(root, "untouched-branch")
            with tempfile.TemporaryDirectory() as wt_tmp:
                wt_path = pathlib.Path(wt_tmp) / "wt"
                _run(["git", "worktree", "add", str(wt_path), "wt-branch"], root)
                git_runner = branch_hygiene.default_git_runner(str(root))
                branches = branch_hygiene.discover_worktree_branches(git_runner)
                # The added worktree's branch, and "main" itself (the
                # primary checkout is a worktree too, in git's own
                # model) are both checked-out branches. A branch that
                # was merely created, never checked out anywhere, is not.
                self.assertIn("wt-branch", branches)
                self.assertIn("main", branches)
                self.assertNotIn("untouched-branch", branches)

    def test_list_local_branches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))
            _make_branch(root, "second")
            git_runner = branch_hygiene.default_git_runner(str(root))
            branches = set(branch_hygiene.list_local_branches(git_runner))
            self.assertEqual(branches, {"main", "second"})


class SurveyLocalBranchesEndToEndTest(unittest.TestCase):
    """Exercises the full survey with a real repo and a stubbed gh runner."""

    def _stub_gh_runner(self, prs: list[dict[str, object]]) -> branch_hygiene.GhRunner:
        def runner(argv: list[str]) -> object:
            self.assertEqual(argv[0], "pr")
            self.assertEqual(argv[1], "list")
            return prs

        return runner

    def test_full_survey_classifies_every_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))

            # merged_or_empty: an ancestor of main with nothing unique.
            _make_branch(root, "stale-merged")

            # squash_merged: unrelated tip, but a stubbed merged PR
            # record's headRefOid matches this branch's own tip exactly.
            squash_tip = _make_branch(root, "squash-landed")
            _run(["git", "checkout", "-q", "squash-landed"], root)
            (root / "b.txt").write_text("b\n")
            _run(["git", "add", "-A"], root)
            _run(["git", "commit", "-q", "-m", "unique change"], root)
            squash_tip = _run(
                ["git", "rev-parse", "squash-landed"], root
            ).stdout.strip()
            _run(["git", "checkout", "-q", "main"], root)

            # open_pr: pushed, has an open PR.
            open_pr_tip = _make_branch(root, "open-feature", push=True)

            # unique_work: pushed, ahead, no PR at all.
            _run(["git", "checkout", "-q", "-b", "unclaimed-work"], root)
            (root / "c.txt").write_text("c\n")
            _run(["git", "add", "-A"], root)
            _run(["git", "commit", "-q", "-m", "unclaimed"], root)
            _run(["git", "push", "-q", "-u", "origin", "unclaimed-work"], root)
            _run(["git", "checkout", "-q", "main"], root)

            # review_first: never pushed, no PR. Needs a commit of its own
            # -- otherwise it is identical to main and correctly (not a
            # bug) classifies as merged_or_empty instead.
            _make_branch(root, "never-pushed")
            _run(["git", "checkout", "-q", "never-pushed"], root)
            (root / "d.txt").write_text("d\n")
            _run(["git", "add", "-A"], root)
            _run(["git", "commit", "-q", "-m", "unpushed work"], root)
            _run(["git", "checkout", "-q", "main"], root)

            # in_worktree: overlaps with merged_or_empty's own ancestry
            # condition to prove precedence, not just class membership.
            _make_branch(root, "worktree-and-merged")
            with tempfile.TemporaryDirectory() as wt_tmp:
                wt_path = pathlib.Path(wt_tmp) / "wt"
                _run(
                    ["git", "worktree", "add", str(wt_path), "worktree-and-merged"],
                    root,
                )

                prs = [
                    {
                        "number": 10,
                        "headRefName": "squash-landed",
                        "state": "MERGED",
                        "headRefOid": squash_tip,
                    },
                    {
                        "number": 11,
                        "headRefName": "open-feature",
                        "state": "OPEN",
                        "headRefOid": open_pr_tip,
                    },
                ]
                git_runner = branch_hygiene.default_git_runner(str(root))
                gh_runner = self._stub_gh_runner(prs)

                infos = branch_hygiene.survey_local_branches(
                    git_runner=git_runner, gh_runner=gh_runner, project_root=str(root)
                )

                by_name = {info.name: info for info in infos}
                self.assertEqual(
                    by_name["main"].branch_class, branch_hygiene.BranchClass.DEFAULT
                )
                self.assertEqual(
                    by_name["stale-merged"].branch_class,
                    branch_hygiene.BranchClass.MERGED_OR_EMPTY,
                )
                self.assertEqual(
                    by_name["squash-landed"].branch_class,
                    branch_hygiene.BranchClass.SQUASH_MERGED,
                )
                self.assertEqual(
                    by_name["open-feature"].branch_class,
                    branch_hygiene.BranchClass.OPEN_PR,
                )
                self.assertEqual(
                    by_name["unclaimed-work"].branch_class,
                    branch_hygiene.BranchClass.UNIQUE_WORK,
                )
                self.assertEqual(
                    by_name["never-pushed"].branch_class,
                    branch_hygiene.BranchClass.REVIEW_FIRST,
                )
                # The precedence case: an ancestor of main AND checked
                # out in a worktree must land in_worktree, not
                # merged_or_empty -- proving worktree status is checked
                # before mergedness, not merely that it *could* also be
                # merged_or_empty.
                self.assertEqual(
                    by_name["worktree-and-merged"].branch_class,
                    branch_hygiene.BranchClass.IN_WORKTREE,
                )

                # None of the delete-eligible-in-principle branches
                # that are also protected classes ever carry a delete
                # flag.
                for name in ("main", "open-feature", "worktree-and-merged"):
                    self.assertIsNone(by_name[name].delete_flag)

    def test_survey_excludes_default_branch_from_delete_output_even_when_checked_out(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))
            # Check out a feature branch, making "main" an ancestor of
            # HEAD -- the exact scenario the review comments flagged.
            _run(["git", "checkout", "-q", "-b", "feature"], root)

            git_runner = branch_hygiene.default_git_runner(str(root))
            gh_runner = self._stub_gh_runner([])
            infos = branch_hygiene.survey_local_branches(
                git_runner=git_runner, gh_runner=gh_runner, project_root=str(root)
            )
            by_name = {info.name: info for info in infos}
            self.assertEqual(
                by_name["main"].branch_class, branch_hygiene.BranchClass.DEFAULT
            )
            content = branch_hygiene.render_delete_commands_file(infos)
            self.assertNotIn("main", content)

    def test_survey_handles_hostile_refname_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _init_repo_with_origin(pathlib.Path(tmp))
            hostile = "weird/$(touch-PWN)"
            _make_branch(root, hostile)

            git_runner = branch_hygiene.default_git_runner(str(root))
            gh_runner = self._stub_gh_runner([])
            infos = branch_hygiene.survey_local_branches(
                git_runner=git_runner, gh_runner=gh_runner, project_root=str(root)
            )
            by_name = {info.name: info for info in infos}
            self.assertIn(hostile, by_name)
            self.assertEqual(
                by_name[hostile].branch_class,
                branch_hygiene.BranchClass.MERGED_OR_EMPTY,
            )
            content = branch_hygiene.render_delete_commands_file(infos)
            quoted = branch_hygiene.quote_branch_name(hostile)
            self.assertIn(quoted, content)
            # The unquoted literal must never appear unescaped as a bare
            # shell word -- only inside its quoted form.
            for line in content.splitlines():
                if hostile in line:
                    self.assertIn(quoted, line)


if __name__ == "__main__":
    unittest.main()
