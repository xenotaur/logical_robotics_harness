"""Real-git-subprocess smoke coverage for cross-PR slug discovery.

Exercises `lrh.prompt_workflow_slug.find_remote_matches` against actual
`git` subprocesses and a local file:// remote -- construction, fetching,
and merge-base computation against a real repository, not fakes. Kept
out of the normal unit suite (`tests/assist_tests/`) per AGENTS.md's
"keep unit tests fast, deterministic, and hermetic" rule: this class
launches many real `git` subprocesses and builds/fetches from a real
Git remote, which the hermetic unit suite must not depend on. Run via
`scripts/smoke`. The runner-injection behavior itself (fake `gh`/`git`
callables, error handling, status/recency policy) remains unit-tested
with fakes in `tests/assist_tests/prompt_workflow_slug_test.py`.
"""

import pathlib
import subprocess
import tempfile
import unittest

from lrh import prompt_workflow_slug


def _run_git(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return result


class _FakeGh:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> object:
        self.calls.append(argv)
        return self.payload


class _FailingGh:
    def __call__(self, argv: list[str]) -> object:
        raise RuntimeError("gh: authentication required")


class CrossPrDiscoveryGitSimulationTests(unittest.TestCase):
    """Exercises real git subprocess calls against local file:// remotes.

    Builds a real "origin" repo with two branches, PR#1 (introduces the
    slug's execution record) and PR#2 (stacked on PR#1, adds only an
    unrelated file), and asserts the merge-base check correctly keeps
    PR#1's match while excluding PR#2's inherited one.
    """

    def _build_origin(self, origin_dir: pathlib.Path) -> None:
        _run_git(origin_dir, "init", "-q")
        _run_git(origin_dir, "config", "user.email", "test@example.com")
        _run_git(origin_dir, "config", "user.name", "Test")
        (origin_dir / "README.md").write_text("base\n", encoding="utf-8")
        _run_git(origin_dir, "add", "README.md")
        _run_git(origin_dir, "commit", "-q", "-m", "base")
        _run_git(origin_dir, "branch", "-M", "main")

        _run_git(origin_dir, "checkout", "-q", "-b", "pr1")
        record_dir = origin_dir / "project/executions/AD_HOC"
        record_dir.mkdir(parents=True, exist_ok=True)
        (record_dir / "2026_01_01_00_00_00_MY_SLUG.md").write_text(
            "---\n"
            "execution_id: 2026_01_01_00_00_00_MY_SLUG\n"
            "status: in_progress\n"
            "created_at: 2026-01-01T00:00:00+00:00\n"
            'pr: ""\n'
            "---\nbody\n",
            encoding="utf-8",
        )
        _run_git(origin_dir, "add", "project/executions/AD_HOC")
        _run_git(origin_dir, "commit", "-q", "-m", "pr1 introduces slug file")

        _run_git(origin_dir, "checkout", "-q", "-b", "pr2")
        (origin_dir / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        _run_git(origin_dir, "add", "unrelated.txt")
        _run_git(origin_dir, "commit", "-q", "-m", "pr2 unrelated, stacked on pr1")

        _run_git(origin_dir, "update-ref", "refs/pull/1/head", "refs/heads/pr1")
        _run_git(origin_dir, "update-ref", "refs/pull/2/head", "refs/heads/pr2")
        _run_git(origin_dir, "checkout", "-q", "main")

    def _build_consumer(
        self, consumer_dir: pathlib.Path, origin_dir: pathlib.Path
    ) -> None:
        _run_git(consumer_dir, "init", "-q")
        _run_git(consumer_dir, "config", "user.email", "test@example.com")
        _run_git(consumer_dir, "config", "user.name", "Test")
        _run_git(consumer_dir, "remote", "add", "origin", str(origin_dir))

    def _git_runner(self, cwd: pathlib.Path):
        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args], cwd=cwd, check=False, capture_output=True, text=True
            )

        return runner

    def test_unrelated_pr_with_broken_base_ref_does_not_abort_discovery(self) -> None:
        # Regression test: a PR whose base branch has since been deleted
        # (or is otherwise unfetchable) must not abort discovery for
        # every other open PR. As long as that PR's own tree contains no
        # file matching the slug being checked, its base ref never needs
        # to be resolved at all -- so a genuinely matching PR elsewhere is
        # still found, and the whole check doesn't fail loudly (exit 3)
        # for a completely unrelated reason.
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)

            # PR#3: unrelated content, and a base ref that does not exist
            # in origin at all -- fetching it would fail outright.
            _run_git(origin_dir, "checkout", "-q", "main")
            _run_git(origin_dir, "checkout", "-q", "-b", "pr3")
            (origin_dir / "also-unrelated.txt").write_text(
                "unrelated\n", encoding="utf-8"
            )
            _run_git(origin_dir, "add", "also-unrelated.txt")
            _run_git(origin_dir, "commit", "-q", "-m", "pr3, unrelated, broken base")
            _run_git(origin_dir, "update-ref", "refs/pull/3/head", "refs/heads/pr3")
            _run_git(origin_dir, "checkout", "-q", "main")

            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh(
                [
                    {"number": 1, "baseRefName": "main"},
                    {"number": 3, "baseRefName": "this-branch-does-not-exist"},
                ]
            )

            # Must not raise SlugCheckError despite PR#3's unfetchable
            # base ref, and must still find PR#1's genuine match.
            matches = prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                gh_runner=gh_runner,
                git_runner=self._git_runner(consumer_dir),
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].source, "PR#1")

    def test_stacked_pr_inheritance_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh(
                [
                    {"number": 1, "baseRefName": "main"},
                    {"number": 2, "baseRefName": "pr1"},
                ]
            )

            matches = prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                gh_runner=gh_runner,
                git_runner=self._git_runner(consumer_dir),
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].source, "PR#1")
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")
        self.assertEqual(matches[0].status, "in_progress")

    def test_default_git_runner_binds_to_project_root_not_process_cwd(self) -> None:
        # Regression test: the default git/gh runners must run in
        # `project_root`, not the process's own current directory --
        # otherwise a caller targeting a different project root would
        # silently query (and mutate refs in) the wrong repository.
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])

            # Deliberately omit git_runner: rely on the default, which must
            # bind to `project_root` via cwd rather than this test
            # process's actual working directory (which is not a git repo
            # tracking an "origin" remote with a "pr1" branch at all).
            matches = prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                project_root=consumer_dir,
                gh_runner=gh_runner,
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")

    def test_force_pushed_pr_head_is_picked_up_not_left_stale(self) -> None:
        # Regression test for the force-refspec fetch
        # (`+refs/pull/<N>/head:...`): a previously-fetched PR ref must be
        # updated to a force-pushed non-fast-forward rewrite, not silently
        # left pointing at the stale commit.
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])
            git_runner = self._git_runner(consumer_dir)

            first_pass = prompt_workflow_slug.find_remote_matches(
                slug="my-slug", gh_runner=gh_runner, git_runner=git_runner
            )
            self.assertEqual(len(first_pass), 1)
            self.assertEqual(first_pass[0].status, "in_progress")

            # Force-push: rewrite pr1's tip with an amended commit changing
            # the record's status, then force-move refs/pull/1/head to it
            # (a non-fast-forward rewrite from the consumer's perspective).
            _run_git(origin_dir, "checkout", "-q", "pr1")
            record_path = (
                origin_dir / "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
            )
            record_path.write_text(
                "---\n"
                "execution_id: 2026_01_01_00_00_00_MY_SLUG\n"
                "status: landed\n"
                "created_at: 2026-01-02T00:00:00+00:00\n"
                'pr: ""\n'
                "---\nbody (force-pushed)\n",
                encoding="utf-8",
            )
            _run_git(origin_dir, "add", "project/executions/AD_HOC")
            _run_git(origin_dir, "commit", "--amend", "-q", "-m", "pr1 force-pushed")
            _run_git(origin_dir, "update-ref", "refs/pull/1/head", "refs/heads/pr1")
            _run_git(origin_dir, "checkout", "-q", "main")

            second_pass = prompt_workflow_slug.find_remote_matches(
                slug="my-slug", gh_runner=gh_runner, git_runner=git_runner
            )

        self.assertEqual(len(second_pass), 1)
        self.assertEqual(second_pass[0].status, "landed")
        self.assertEqual(second_pass[0].created_at, "2026-01-02T00:00:00+00:00")

    def test_merge_base_tree_check_failure_raises_not_treated_as_not_inherited(
        self,
    ) -> None:
        # A `git ls-tree` failure against the merge-base tree-ish (e.g. a
        # corrupted repo or bad object database making `merge_base`
        # itself unusable) must fail loudly, not be silently treated as
        # "not inherited, proceed as a genuine new match." This structural
        # check replaced an earlier `git cat-file -e` + stderr-text-match
        # approach: a subsequent review round found that git's "path
        # absent" message differs ("does not exist in" vs. "exists on
        # disk, but not in") depending on exactly how the path is absent,
        # and matching only one wording misclassified the other as a
        # fatal error. `ls-tree`'s success/failure split carries no such
        # free-text ambiguity: failure means the tree-ish itself is
        # unusable, full stop.
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])
            real_runner = self._git_runner(consumer_dir)

            def flaky_git_runner(args: list[str]):
                if args[0] == "ls-tree" and "-r" not in args:
                    return subprocess.CompletedProcess(
                        args=["git", *args],
                        returncode=128,
                        stdout="",
                        stderr="fatal: unable to read sha1 file (odb corrupt)",
                    )
                return real_runner(args)

            with self.assertRaises(prompt_workflow_slug.SlugCheckError):
                prompt_workflow_slug.find_remote_matches(
                    slug="my-slug", gh_runner=gh_runner, git_runner=flaky_git_runner
                )

    def test_path_present_on_disk_but_absent_from_merge_base_tree_is_new_match(
        self,
    ) -> None:
        # Regression test for the exact case round 6 review found: a path
        # that exists in the worktree/current tip but is absent from the
        # merge-base tree specifically must still be recognized as a
        # genuine new match (not misclassified as inherited, and not
        # raised as an unexpected failure) -- this is precisely PR#1's
        # own scenario in `_build_origin` (the slug file exists at pr1's
        # tip but not at main's tip, its merge-base with pr1).
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])
            matches = prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                gh_runner=gh_runner,
                git_runner=self._git_runner(consumer_dir),
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].source, "PR#1")

    def test_local_match_excluded_from_remote_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            origin_dir = root / "origin"
            consumer_dir = root / "consumer"
            origin_dir.mkdir()
            consumer_dir.mkdir()
            self._build_origin(origin_dir)
            self._build_consumer(consumer_dir, origin_dir)

            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])

            matches = prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                local_paths=[
                    "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
                ],
                gh_runner=gh_runner,
                git_runner=self._git_runner(consumer_dir),
            )

        self.assertEqual(matches, [])

    def test_gh_failure_raises_slug_check_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            consumer_dir = pathlib.Path(temp_dir)
            with self.assertRaises(prompt_workflow_slug.SlugCheckError):
                prompt_workflow_slug.find_remote_matches(
                    slug="my-slug",
                    gh_runner=_FailingGh(),
                    git_runner=self._git_runner(consumer_dir),
                )

    def test_git_fetch_failure_raises_slug_check_error_not_silent_no_match(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # No "origin" remote configured in this bare cwd, so any fetch
            # attempt fails -- this must surface as an error, not as an
            # empty (falsely reassuring) match list.
            consumer_dir = pathlib.Path(temp_dir)
            _run_git(consumer_dir, "init", "-q")
            gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])

            with self.assertRaises(prompt_workflow_slug.SlugCheckError):
                prompt_workflow_slug.find_remote_matches(
                    slug="my-slug",
                    gh_runner=gh_runner,
                    git_runner=self._git_runner(consumer_dir),
                )


if __name__ == "__main__":
    unittest.main()
