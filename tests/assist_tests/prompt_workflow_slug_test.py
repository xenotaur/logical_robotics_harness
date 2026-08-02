import pathlib
import tempfile
import unittest

from lrh import prompt_workflow_slug


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

    def test_tied_unresolved_status_message_names_the_offending_match(self) -> None:
        # Regression test: when matches tie at the latest instant and one
        # has a recognized blocking status (in_progress) while another
        # has an unrecognized one (planned), the report must name the
        # actually-unresolved match, not `most_recent`'s representative
        # pick -- `most_recent` prefers any non-terminal candidate, so it
        # could return the in_progress one even though that match isn't
        # the source of the ambiguity.
        tied_in_progress = self._match(
            "LOCAL", "in_progress", "2026-01-01T00:00:00+00:00"
        )
        tied_planned = self._match("REMOTE", "planned", "2026-01-01T00:00:00+00:00")
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[tied_in_progress, tied_planned],
        )

        self.assertTrue(result.unresolved_status)
        self.assertEqual(result._unresolved_status_match, tied_planned)

        text = prompt_workflow_slug.format_text_result(result)
        self.assertIn("REMOTE", text)
        self.assertIn("status='planned'", text)
        self.assertNotIn("status='in_progress'", text)

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

    def test_missing_execution_id_falls_back_to_filename_stem(self) -> None:
        # A match with a valid terminal status/created_at but a blank or
        # missing execution_id must not silently hand back an empty ID --
        # that would let a rerun lose its rerun_of lineage even though
        # the match is otherwise perfectly resolvable. The filename stem
        # (always present) is a safe fallback.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            path = (
                project_root
                / "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\n"
                "status: failed\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                'pr: ""\n'
                "---\nbody\n",
                encoding="utf-8",
            )

            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")

    def test_non_string_execution_id_falls_back_to_filename_stem(self) -> None:
        # Regression test: a bare-digit YAML scalar (e.g. `execution_id:
        # 123`) parses as an int, not a string. The record-loading layer
        # (_frontmatter_string) coerces it to "123" via str(value) before
        # this module ever sees it, so a naive isinstance(..., str) check
        # on the already-coerced value can't tell it apart from a
        # genuinely authored string ID -- it must instead be checked
        # against the *raw* frontmatter mapping, where the type is still
        # int, to correctly trigger the filename-stem fallback (matching
        # the remote path, which drops non-string fields outright).
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            path = (
                project_root
                / "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.md"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\n"
                "execution_id: 123\n"
                "status: failed\n"
                "created_at: 2026-01-01T00:00:00+00:00\n"
                'pr: ""\n'
                "---\nbody\n",
                encoding="utf-8",
            )

            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")

    def test_matches_are_case_insensitive_like_the_shell_check_it_replaced(
        self,
    ) -> None:
        # The shell-based idempotence check this module replaces used
        # `grep -i`; a non-canonically-cased filename (hand-written, or
        # migrated from an older convention) must still be found.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/2026_01_01_00_00_00_my_slug.md",
                execution_id="2026_01_01_00_00_00_my_slug",
            )

            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_my_slug")

    def test_uppercase_md_extension_is_still_matched(self) -> None:
        # Regression test: `bucket.glob("*.md")` is case-sensitive
        # regardless of the underlying filesystem's own case-sensitivity
        # (confirmed empirically: it does not match a `.MD`-suffixed file
        # even on a case-insensitive-by-default filesystem) -- so a
        # hand-written or migrated record ending in `.MD` was silently
        # filtered out before the already-case-insensitive trailing-
        # segment regex ever got a chance to match it.
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = pathlib.Path(temp_dir)
            self._write_record(
                project_root,
                "project/executions/AD_HOC/2026_01_01_00_00_00_MY_SLUG.MD",
                execution_id="2026_01_01_00_00_00_MY_SLUG",
            )

            matches = prompt_workflow_slug.find_local_matches(
                project_root=project_root, slug="my-slug"
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].execution_id, "2026_01_01_00_00_00_MY_SLUG")

    def test_absolute_output_root_outside_project_root_raises(self) -> None:
        # Regression test: an absolute --output-root cannot be expressed
        # as a git pathspec for remote discovery. When it also isn't a
        # subpath of project_root at all, there is no sensible
        # relativization -- fail loudly rather than silently searching
        # the wrong location or crashing with a raw ValueError.
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            tempfile.TemporaryDirectory() as unrelated_dir,
        ):
            with self.assertRaises(prompt_workflow_slug.SlugCheckError):
                prompt_workflow_slug.find_remote_matches(
                    slug="my-slug",
                    project_root=temp_dir,
                    output_root=pathlib.Path(unrelated_dir) / "executions",
                    gh_runner=_FakeGh([]),
                )


class _FakeGh:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> object:
        self.calls.append(argv)
        return self.payload


class SlugRemoteMatchesRunnerErrorHandlingTest(unittest.TestCase):
    """Runner-injection error handling, using fakes only (no real git/gh).

    The real-git-subprocess cross-PR discovery scenarios (stacked-PR
    merge-base exclusion, force-push handling, structural tree checks,
    etc.) live in
    tests/smoke/prompt_workflow_slug_cross_pr_smoke.py instead -- kept
    out of this hermetic unit suite per AGENTS.md. These three tests
    never reach a real `git`/`gh` call (the fakes raise, or the PR list
    is empty, before the per-PR loop body ever executes), so they stay
    here as genuinely fast, deterministic unit tests.
    """

    def test_gh_pr_list_requests_far_beyond_a_realistic_open_pr_count(self) -> None:
        # Regression test: `gh pr list --limit N` paginates internally to
        # satisfy any requested N, so a too-small hardcoded cap silently
        # omits PRs beyond it in a repo that legitimately has more open
        # PRs than that -- and since this list is authoritative for the
        # slug check, a blocking match hiding past the cutoff would
        # produce a false "no prior record" (exit 0). Assert the limit
        # requested is comfortably beyond any plausible real open-PR
        # count, not a specific small number like the previous 1,000.
        gh_runner = _FakeGh([])
        prompt_workflow_slug.find_remote_matches(slug="my-slug", gh_runner=gh_runner)

        self.assertEqual(len(gh_runner.calls), 1)
        argv = gh_runner.calls[0]
        limit_index = argv.index("--limit") + 1
        self.assertGreaterEqual(int(argv[limit_index]), 10_000)

    def test_malformed_gh_pr_list_entry_raises_not_silently_dropped(self) -> None:
        # Regression test: this list is authoritative for the blocking
        # decision, so a malformed entry (missing/wrong-typed field, or a
        # non-object entry) must raise SlugCheckError, not be silently
        # skipped (a false "no prior record" if that PR held a real
        # match) or crash with a raw KeyError/TypeError/ValueError.
        for bad_payload in (
            [{"baseRefName": "main"}],  # missing "number"
            [{"number": "not-an-int", "baseRefName": "main"}],
            ["not-a-dict-entry"],
        ):
            with self.subTest(bad_payload=bad_payload):
                gh_runner = _FakeGh(bad_payload)
                with self.assertRaises(prompt_workflow_slug.SlugCheckError):
                    prompt_workflow_slug.find_remote_matches(
                        slug="my-slug", gh_runner=gh_runner
                    )

    def test_missing_git_executable_raises_slug_check_error_not_traceback(
        self,
    ) -> None:
        # Regression test: subprocess.run raises FileNotFoundError
        # directly (not a CompletedProcess with a nonzero code) when the
        # executable itself can't be launched -- e.g. `git` missing from
        # PATH. This must surface as SlugCheckError/exit 3 like every
        # other git failure in this module, not an unhandled traceback.
        gh_runner = _FakeGh([{"number": 1, "baseRefName": "main"}])

        def git_runner_without_git(args: list[str]):
            raise FileNotFoundError("[Errno 2] No such file or directory: 'git'")

        with self.assertRaises(prompt_workflow_slug.SlugCheckError):
            prompt_workflow_slug.find_remote_matches(
                slug="my-slug",
                gh_runner=gh_runner,
                git_runner=git_runner_without_git,
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
