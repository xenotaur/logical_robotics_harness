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


class SlugMatchSortAndPolicyTest(unittest.TestCase):
    def _match(
        self, execution_id: str, status: str, created_at: str
    ) -> prompt_workflow_slug.SlugMatch:
        return prompt_workflow_slug.SlugMatch(
            path=f"project/executions/AD_HOC/{execution_id}.md",
            execution_id=execution_id,
            status=status,
            pr="",
            created_at=created_at,
            source="local",
        )

    def test_no_matches_is_non_blocking(self) -> None:
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug", work_item="AD_HOC", matches=[]
        )
        self.assertIsNone(result.most_recent)
        self.assertFalse(result.blocking)
        self.assertEqual(result.exit_code, 0)

    def test_landed_match_blocks(self) -> None:
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[self._match("A", "landed", "2026-01-01T00:00:00+00:00")],
        )
        self.assertTrue(result.blocking)
        self.assertEqual(result.exit_code, 1)

    def test_terminal_status_match_does_not_block(self) -> None:
        for status in ("failed", "reverted", "superseded"):
            with self.subTest(status=status):
                result = prompt_workflow_slug.SlugCheckResult(
                    slug="my-slug",
                    work_item="AD_HOC",
                    matches=[self._match("A", status, "2026-01-01T00:00:00+00:00")],
                )
                self.assertFalse(result.blocking)
                self.assertEqual(result.exit_code, 0)

    def test_unrecognized_planned_status_blocks_as_unresolved(self) -> None:
        # DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT leaves `planned` unresolved
        # centrally, but an unresolved outcome is not license to proceed --
        # only explicit terminal statuses are non-blocking.
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[self._match("A", "planned", "2026-01-01T00:00:00+00:00")],
        )
        self.assertTrue(result.blocking)
        self.assertTrue(result.unresolved_status)
        self.assertEqual(result.exit_code, 1)

    def test_missing_or_garbage_status_blocks_as_unresolved(self) -> None:
        for status in ("", "not-a-real-status"):
            with self.subTest(status=status):
                result = prompt_workflow_slug.SlugCheckResult(
                    slug="my-slug",
                    work_item="AD_HOC",
                    matches=[self._match("A", status, "2026-01-01T00:00:00+00:00")],
                )
                self.assertTrue(result.blocking)
                self.assertTrue(result.unresolved_status)

    def test_known_blocking_status_is_not_flagged_unresolved(self) -> None:
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[self._match("A", "landed", "2026-01-01T00:00:00+00:00")],
        )
        self.assertTrue(result.blocking)
        self.assertFalse(result.unresolved_status)

    def test_most_recent_selected_by_created_at_not_list_order(self) -> None:
        older_landed = self._match("OLDER", "landed", "2026-01-01T00:00:00+00:00")
        newer_failed = self._match("NEWER", "failed", "2026-06-01T00:00:00+00:00")
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[newer_failed, older_landed],
        )
        # The most recent attempt is the failed one, so it should not block,
        # even though an older landed match is also present.
        self.assertEqual(result.most_recent, newer_failed)
        self.assertFalse(result.blocking)

    def test_unresolved_recency_blocks_even_if_naive_pick_is_terminal(self) -> None:
        # A match with unknown recency sorts as the oldest possible instant
        # (a tiebreak, not a real timestamp). If an older-but-parseable
        # terminal match were allowed to "win" the most-recent comparison
        # against it, the truly-latest (recency-unknown) attempt would be
        # silently ignored and could itself be in_progress/landed.
        unknown_recency = self._match("UNKNOWN", "in_progress", "")
        older_but_parseable_failed = self._match(
            "OLDER", "failed", "2020-01-01T00:00:00+00:00"
        )
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[unknown_recency, older_but_parseable_failed],
        )
        self.assertTrue(result.has_unresolved_recency)
        self.assertTrue(result.blocking)
        self.assertEqual(result.exit_code, 1)

    def test_all_matches_have_known_recency_is_not_flagged_unresolved(self) -> None:
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[self._match("A", "failed", "2026-01-01T00:00:00+00:00")],
        )
        self.assertFalse(result.has_unresolved_recency)

    def test_exact_timestamp_tie_blocks_regardless_of_list_order(self) -> None:
        # created_at is truncated to whole seconds, so two independent
        # records (e.g. two PRs minting the same slug within one second)
        # can share the exact same instant. A single max()-by-timestamp
        # pick breaks that tie by incidental list order, which could let
        # a `failed` match "beat" an equally-recent `in_progress` match
        # just because of ordering. Every match tied for the latest
        # instant must be considered, regardless of order.
        tied_failed = self._match("FAILED", "failed", "2026-01-01T00:00:00+00:00")
        tied_in_progress = self._match(
            "IN_PROGRESS", "in_progress", "2026-01-01T00:00:00+00:00"
        )
        for matches in (
            [tied_failed, tied_in_progress],
            [tied_in_progress, tied_failed],
        ):
            with self.subTest(order=[m.execution_id for m in matches]):
                result = prompt_workflow_slug.SlugCheckResult(
                    slug="my-slug", work_item="AD_HOC", matches=matches
                )
                self.assertTrue(result.blocking)
                self.assertEqual(result.exit_code, 1)

    def test_exact_timestamp_tie_both_terminal_does_not_block(self) -> None:
        tied_failed = self._match("A", "failed", "2026-01-01T00:00:00+00:00")
        tied_reverted = self._match("B", "reverted", "2026-01-01T00:00:00+00:00")
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[tied_failed, tied_reverted],
        )
        self.assertFalse(result.blocking)
        self.assertEqual(result.exit_code, 0)

    def test_offset_naive_created_at_is_not_treated_as_known_recency(self) -> None:
        # datetime.fromisoformat() happily accepts offset-naive strings
        # (a bare date, or a timestamp missing its UTC offset), but the
        # execution-record contract requires an offset. An offset-naive
        # parse must be treated exactly like an unparseable one -- both
        # unresolved recency -- and, critically, must never reach
        # sort_key as a genuine timestamp: comparing a naive datetime
        # against an offset-aware one raises TypeError, not a wrong
        # answer, so the ONLY safe outcome is to filter it out upstream.
        for naive_value in ("2026-01-01", "2026-01-01T00:00:00"):
            with self.subTest(created_at=naive_value):
                match = self._match("A", "failed", naive_value)
                self.assertFalse(match.has_known_created_at)

    def test_offset_naive_created_at_blocks_without_crashing_next_to_aware_match(
        self,
    ) -> None:
        naive_terminal = self._match("NAIVE", "failed", "2026-01-01T00:00:00")
        aware_terminal = self._match("AWARE", "reverted", "2020-01-01T00:00:00+00:00")
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[naive_terminal, aware_terminal],
        )
        # Must not raise TypeError (naive vs. aware datetime comparison)
        # and must block: recency can't be established for the naive one.
        self.assertTrue(result.has_unresolved_recency)
        self.assertTrue(result.blocking)
        self.assertEqual(result.exit_code, 1)


class FindLocalMatchesTest(unittest.TestCase):
    def _write_record(
        self,
        project_root: pathlib.Path,
        rel_path: str,
        *,
        execution_id: str,
        status: str = "landed",
        created_at: str = "2026-01-01T00:00:00+00:00",
    ) -> None:
        path = project_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f"execution_id: {execution_id}\n"
            f"status: {status}\n"
            f"created_at: {created_at}\n"
            'pr: ""\n'
            "---\nbody\n",
            encoding="utf-8",
        )

    def test_no_bucket_directory_returns_no_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            matches = prompt_workflow_slug.find_local_matches(
                project_root=temp_dir, slug="my-slug"
            )
        self.assertEqual(matches, [])

    def test_unparseable_matching_file_is_preserved_not_dropped(self) -> None:
        # A trailing-segment filename match with malformed frontmatter must
        # not be silently discarded -- that would let a genuine prior
        # record be missed entirely and permit minting a duplicate.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            path = (
                project_root
                / "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("not valid frontmatter at all\n", encoding="utf-8")

            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].status, "unparseable")
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug", work_item="AD_HOC", matches=matches
        )
        self.assertTrue(result.blocking)
        self.assertTrue(result.unresolved_status)

    def test_matches_trailing_segment_only_not_bare_substring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md",
                execution_id="2026_01_01_00_00_00_MY_SLUG",
            )
            # Should NOT match: MY_SLUG is only a substring here, and it is
            # the review-suffixed sibling, not a bare re-occurrence.
            self._write_record(
                project_root,
                "project/executions/AD_HOC/2026_01_02_00_00_00_MY_SLUG_REVIEW.md",
                execution_id="2026_01_02_00_00_00_MY_SLUG_REVIEW",
            )
            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")
        self.assertEqual(
            matches[0].path,
            "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md",
        )
        self.assertEqual(matches[0].source, "local")


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


class CrossPrDiscoveryGitSimulationTest(unittest.TestCase):
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

    def test_cat_file_unexpected_failure_raises_not_treated_as_not_inherited(
        self,
    ) -> None:
        # A `git cat-file -e` failure whose stderr does NOT match git's
        # ordinary "path does not exist" message (e.g. a corrupted repo or
        # bad object database) must fail loudly, not be silently treated
        # as "not inherited, proceed as a genuine new match."
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
                if args[:2] == ["cat-file", "-e"]:
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


class CheckSlugIntegrationTest(unittest.TestCase):
    def test_check_slug_local_only_skips_remote_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            record_path = (
                project_root
                / "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
            )
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(
                "---\n"
                "execution_id: 2026_01_01_00_00_00_MY_SLUG\n"
                "status: landed\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                'pr: ""\n'
                "---\nbody\n",
                encoding="utf-8",
            )

            def _unexpected_gh_runner(argv: list[str]) -> object:
                raise AssertionError("gh must not be called when include_remote=False")

            result = prompt_workflow_slug.check_slug(
                project_root=project_root,
                slug="my-slug",
                include_remote=False,
                gh_runner=_unexpected_gh_runner,
            )

        self.assertEqual(len(result.matches), 1)
        self.assertTrue(result.blocking)

    def test_format_text_result_reports_no_match(self) -> None:
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug", work_item="AD_HOC", matches=[]
        )
        text = prompt_workflow_slug.format_text_result(result)
        self.assertIn("No prior execution record found", text)


if __name__ == "__main__":
    unittest.main()
