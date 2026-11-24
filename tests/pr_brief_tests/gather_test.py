import datetime
import json
import pathlib
import subprocess
import unittest
from unittest import mock

from lrh.integrations.github import pr_ref
from lrh.pr_brief import gather

_REF = pr_ref.PullRequestRef(owner="example", repo="widgets", number=7)


class CategorizePathTest(unittest.TestCase):
    def test_default_categories(self) -> None:
        cases = {
            "src/app/providers.py": "code",
            "tests/integration/fixture/.devcontainer/devcontainer.json": "tests",
            "pkg/foo_test.go": "tests",
            "web/button.spec.ts": "tests",
            "test_utils.py": "tests",
            "README.md": "docs",
            "docs/diagram.svg": "docs",
            "src/app/resources/shell/helper.sh": "scripts",
            ".gitignore": "config",
            ".github/workflows/ci.yml": "config",
            "pyproject.toml": "config",
            "Dockerfile": "config",
            "src/app/contest.py": "code",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(gather.categorize_path(path), expected)


class SummariesTest(unittest.TestCase):
    def test_summarize_checks_counts_check_runs_and_status_contexts(self) -> None:
        rollup = [
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"},
            {"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""},
            {"__typename": "StatusContext", "state": "SUCCESS"},
            {"__typename": "StatusContext", "state": "ERROR"},
        ]
        self.assertEqual(
            gather.summarize_checks(rollup),
            {"total": 5, "passing": 2, "failing": 2, "pending": 1},
        )
        self.assertEqual(gather.summarize_checks(None)["total"], 0)

    def test_summarize_reviews(self) -> None:
        reviews = [{"state": "APPROVED"}, {"state": "COMMENTED"}]
        summary = gather.summarize_reviews(reviews, "REVIEW_REQUIRED")
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["approvals"], 1)
        self.assertEqual(summary["comments"], 1)
        self.assertEqual(summary["decision"], "REVIEW_REQUIRED")


class MergeTreeTest(unittest.TestCase):
    def test_parse_clean_and_conflicted_output(self) -> None:
        self.assertEqual(
            gather.parse_merge_tree_output("abc123\n", 0),
            {"checked": True, "clean": True, "files": []},
        )
        self.assertEqual(
            gather.parse_merge_tree_output("abc123\nb.py\na.py\nb.py\n", 1),
            {"checked": True, "clean": False, "files": ["a.py", "b.py"]},
        )
        with self.assertRaises(RuntimeError):
            gather.parse_merge_tree_output("", 128)

    def test_trial_merge_fetches_by_sha_then_merges_in_memory(self) -> None:
        calls = []

        def run_git(argv, cwd):
            calls.append(argv)
            if argv[0] == "fetch":
                return subprocess.CompletedProcess(argv, 0, "", "")
            return subprocess.CompletedProcess(argv, 1, "tree\nsrc/x.py\n", "")

        result = gather.trial_merge(
            _REF, "base", "head", pathlib.Path("."), run_git=run_git
        )
        self.assertEqual(
            result, {"checked": True, "clean": False, "files": ["src/x.py"]}
        )
        self.assertEqual(
            calls[0],
            [
                "fetch",
                "--quiet",
                "--no-tags",
                "https://github.com/example/widgets.git",
                "base",
                "head",
            ],
        )
        self.assertEqual(
            calls[1][:4], ["merge-tree", "--write-tree", "--name-only", "--no-messages"]
        )

    def test_trial_merge_reports_fetch_failure_without_raising(self) -> None:
        def run_git(argv, cwd):
            return subprocess.CompletedProcess(argv, 128, "", "fatal: no access\n")

        result = gather.trial_merge(
            _REF, "base", "head", pathlib.Path("."), run_git=run_git
        )
        self.assertFalse(result["checked"])
        self.assertEqual(result["error"], "fatal: no access")


class ResolveRefTest(unittest.TestCase):
    def test_url_owner_repo_and_bare_number(self) -> None:
        self.assertEqual(
            gather.resolve_ref("https://github.com/example/widgets/pull/7"), _REF
        )
        self.assertEqual(gather.resolve_ref("example/widgets", 7), _REF)
        with mock.patch(
            "lrh.pr_brief.gather.gh_client.run_gh_json",
            return_value={"nameWithOwner": "example/widgets"},
        ):
            self.assertEqual(gather.resolve_ref("7"), _REF)
        with self.assertRaises(ValueError):
            gather.resolve_ref("example/widgets")


_VIEW = {
    "number": 7,
    "title": "Add providers",
    "url": "https://github.com/example/widgets/pull/7",
    "author": {"login": "octo", "name": "Octo Cat"},
    "state": "OPEN",
    "isDraft": False,
    "baseRefName": "main",
    "headRefName": "add-providers",
    "baseRefOid": "a" * 40,
    "headRefOid": "b" * 40,
    "additions": 12,
    "deletions": 3,
    "changedFiles": 2,
    "commits": [{"oid": "b" * 40, "messageHeadline": "Add providers"}],
    "createdAt": "2026-11-01T10:00:00Z",
    "updatedAt": "2026-11-02T10:00:00Z",
    "mergeable": "MERGEABLE",
    "mergeStateStatus": "CLEAN",
    "reviewDecision": "",
    "reviews": [],
    "statusCheckRollup": [],
    "body": "Body text",
    "labels": [{"name": "feature"}],
}

_FILE_LINES = "\n".join(
    json.dumps(item)
    for item in (
        {
            "filename": "src/app.py",
            "status": "modified",
            "additions": 10,
            "deletions": 3,
            "previous_filename": None,
            "patch": "@@ -1 +1 @@",
        },
        {
            "filename": "tests/app_test.py",
            "status": "added",
            "additions": 2,
            "deletions": 0,
            "previous_filename": None,
            "patch": "@@ +1 @@",
        },
    )
)


class GatherBriefingDataTest(unittest.TestCase):
    def _fake_gh(self, *, diff_fails: bool = False):
        def run_gh(argv, cwd=None):
            if argv[:2] == ["pr", "diff"]:
                if diff_fails:
                    raise RuntimeError("gh command failed (api): diff too large")
                return "diff --git a/src/app.py b/src/app.py\n"
            if argv[0] == "api" and argv[1].endswith("/files"):
                return _FILE_LINES + "\n"
            if argv[0] == "api" and argv[1].endswith("/git/ref/heads/main"):
                return "d" * 40 + "\n"
            raise AssertionError(f"unexpected gh call {argv}")

        def run_gh_json(argv, cwd=None):
            if argv[:2] == ["pr", "view"]:
                return _VIEW
            if argv[0] == "api" and "/compare/" in argv[1]:
                self.assertIn("main..." + "b" * 40, argv[1])
                return {
                    "ahead_by": 1,
                    "behind_by": 4,
                    "merge_base_sha": "c" * 40,
                    "merge_base_date": "2026-10-01T00:00:00Z",
                }
            raise AssertionError(f"unexpected gh json call {argv}")

        return run_gh, run_gh_json

    def test_collects_facts_and_seeds_briefing(self) -> None:
        run_gh, run_gh_json = self._fake_gh()
        now = datetime.datetime(2026, 11, 23, 12, tzinfo=datetime.timezone.utc)
        with (
            mock.patch("lrh.pr_brief.gather.gh_client.run_gh", side_effect=run_gh),
            mock.patch(
                "lrh.pr_brief.gather.gh_client.run_gh_json", side_effect=run_gh_json
            ),
        ):
            data, diff = gather.gather_briefing_data(_REF, now=now)
        self.assertEqual(diff, "diff --git a/src/app.py b/src/app.py\n")
        self.assertEqual(data["generated_at"], "2026-11-23T12:00:00+00:00")
        self.assertEqual(data["pr"]["repo"], "example/widgets")
        self.assertEqual(data["pr"]["author_name"], "Octo Cat")
        self.assertEqual(
            data["pr"]["commits"], [{"sha": "b" * 12, "headline": "Add providers"}]
        )
        self.assertEqual(data["pr"]["labels"], ["feature"])
        self.assertEqual(data["status"]["behind_by"], 4)
        # The base SHA is the branch's current tip, not the PR's stale baseRefOid.
        self.assertEqual(data["pr"]["base_sha"], "d" * 40)
        self.assertEqual(
            data["status"]["conflicts"], {"checked": False, "clean": None, "files": []}
        )
        self.assertEqual(
            [
                (item["path"], item["category"], item["status"])
                for item in data["files"]
            ],
            [
                ("src/app.py", "code", "modified"),
                ("tests/app_test.py", "tests", "added"),
            ],
        )
        self.assertEqual(
            set(data["briefing"]["files"]), {"src/app.py", "tests/app_test.py"}
        )
        self.assertEqual(data["briefing"]["review_notes"], [])

    def test_falls_back_to_file_patches_when_diff_is_refused(self) -> None:
        run_gh, run_gh_json = self._fake_gh(diff_fails=True)
        with (
            mock.patch("lrh.pr_brief.gather.gh_client.run_gh", side_effect=run_gh),
            mock.patch(
                "lrh.pr_brief.gather.gh_client.run_gh_json", side_effect=run_gh_json
            ),
        ):
            _, diff = gather.gather_briefing_data(_REF)
        self.assertIn("diff --git a/src/app.py b/src/app.py\n@@ -1 +1 @@", diff)
        self.assertIn("diff --git a/tests/app_test.py b/tests/app_test.py", diff)

    def test_runs_trial_merge_when_repo_dir_given(self) -> None:
        run_gh, run_gh_json = self._fake_gh()

        calls = []

        def run_git(argv, cwd):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "tree\n", "")

        with (
            mock.patch("lrh.pr_brief.gather.gh_client.run_gh", side_effect=run_gh),
            mock.patch(
                "lrh.pr_brief.gather.gh_client.run_gh_json", side_effect=run_gh_json
            ),
        ):
            data, _ = gather.gather_briefing_data(
                _REF, repo_dir=pathlib.Path("."), run_git=run_git
            )
        self.assertEqual(
            data["status"]["conflicts"], {"checked": True, "clean": True, "files": []}
        )
        self.assertEqual(calls[1][-2:], ["d" * 40, "b" * 40])


if __name__ == "__main__":
    unittest.main()
