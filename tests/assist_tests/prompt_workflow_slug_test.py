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

    def test_unrecognized_planned_status_does_not_block(self) -> None:
        # DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT leaves `planned` unresolved
        # centrally; this module's default leans non-blocking.
        result = prompt_workflow_slug.SlugCheckResult(
            slug="my-slug",
            work_item="AD_HOC",
            matches=[self._match("A", "planned", "2026-01-01T00:00:00+00:00")],
        )
        self.assertFalse(result.blocking)

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
