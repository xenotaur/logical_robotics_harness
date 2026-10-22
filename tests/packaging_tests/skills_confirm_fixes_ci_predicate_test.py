"""Behavioral coverage for the confirm-fixes `check_ci_predicate` bash function.

The reference documents the predicate as real, runnable code, so these tests
extract it verbatim from every committed copy and run it in bash against a
fake `gh` on PATH. Return codes: 0 green, 1 terminal failure, 2 pending.
A wiring check also pins SKILL.md Step 8's first CI read to the predicate.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REFERENCE = "lrh-confirm-fixes/references/confirm-fixes-workflow.md"
SKILL_ROOTS = (
    REPO_ROOT / "src" / "lrh" / "skills",
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".agents" / "skills",
    REPO_ROOT / ".gemini" / "plugins" / "lrh" / "skills",
)
PREDICATE = re.compile(
    r"^check_ci_predicate\(\) \{\n.*?^\}\n", re.MULTILINE | re.DOTALL
)
PR_URL = "https://github.com/example/repo/pull/1"

# Fake `gh`: `pr checks --required` prints $FAKE_REQUIRED and `pr checks`
# prints $FAKE_ALL; an empty value mimics real gh's "no (required) checks
# reported" error, which exits 1 with empty stdout rather than printing `[]`.
# `pr view` prints $FAKE_HEAD for headRefOid and the base branch otherwise;
# `api` prints $FAKE_RULES_COUNT.
FAKE_GH = """#!/usr/bin/env bash
case "$1 $2" in
  "pr checks")
    for arg in "$@"; do
      if [ "$arg" = "--required" ]; then
        if [ -z "$FAKE_REQUIRED" ]; then exit 1; fi
        printf '%s\\n' "$FAKE_REQUIRED"
        exit 0
      fi
    done
    if [ -z "$FAKE_ALL" ]; then exit 1; fi
    printf '%s\\n' "$FAKE_ALL"
    ;;
  "pr view")
    case "$*" in
      *headRefOid*) echo "$FAKE_HEAD" ;;
      *) echo main ;;
    esac
    ;;
  api*)
    if [ -z "$FAKE_RULES_COUNT" ]; then exit 1; fi
    echo "$FAKE_RULES_COUNT"
    ;;
esac
"""

PASS = '{"name":"test","state":"SUCCESS","bucket":"pass"}'
FAIL = '{"name":"test","state":"FAILURE","bucket":"fail"}'
PENDING = '{"name":"test","state":"IN_PROGRESS","bucket":"pending"}'


def _extract_predicate(root: pathlib.Path) -> str:
    match = PREDICATE.search((root / REFERENCE).read_text())
    if match is None:
        raise AssertionError(f"check_ci_predicate not found under {root}")
    return match.group(0)


@unittest.skipUnless(
    shutil.which("bash") and shutil.which("jq"), "requires bash and jq"
)
class ConfirmFixesCiPredicateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        bin_dir = pathlib.Path(self._tmp.name)
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH)
        fake_gh.chmod(0o755)
        self._path = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    def _run(
        self,
        predicate: str,
        *,
        required: str = "",
        all_checks: str = "",
        rules_count: str = "0",
        head: str = "",
        expected_sha: str = "",
    ) -> int:
        script = f'{predicate}\ncheck_ci_predicate "{PR_URL}" "{expected_sha}"\n'
        env = {
            **os.environ,
            "PATH": self._path,
            "FAKE_REQUIRED": required,
            "FAKE_ALL": all_checks,
            "FAKE_RULES_COUNT": rules_count,
            "FAKE_HEAD": head,
        }
        return subprocess.run(
            ["bash", "-c", script], env=env, capture_output=True, check=False
        ).returncode

    def _assert_all_roots(self, expected: int, **kwargs: str) -> None:
        for root in SKILL_ROOTS:
            with self.subTest(root=str(root.relative_to(REPO_ROOT))):
                self.assertEqual(
                    self._run(_extract_predicate(root), **kwargs), expected
                )

    def test_no_checks_reported_without_required_rules_is_pending(self) -> None:
        # Real gh's empty-rollup case: both lookups exit 1 with empty stdout.
        self._assert_all_roots(2, rules_count="0", all_checks="")

    def test_empty_unfiltered_check_list_is_pending_not_green(self) -> None:
        self._assert_all_roots(2, all_checks="[]")

    def test_empty_required_check_list_is_pending_not_green(self) -> None:
        self._assert_all_roots(2, required="[]")

    def test_unparseable_check_list_is_pending(self) -> None:
        self._assert_all_roots(2, all_checks="not json")

    def test_all_passing_checks_are_green(self) -> None:
        self._assert_all_roots(0, all_checks=f"[{PASS}]")
        self._assert_all_roots(0, required=f"[{PASS}]")

    def test_any_failing_check_is_terminal_failure(self) -> None:
        self._assert_all_roots(1, all_checks=f"[{PASS},{FAIL}]")

    def test_any_unfinished_check_is_pending(self) -> None:
        self._assert_all_roots(2, all_checks=f"[{PASS},{PENDING}]")

    def test_required_rules_without_posted_checks_are_pending(self) -> None:
        self._assert_all_roots(2, rules_count="1")

    def test_failed_rules_lookup_is_pending(self) -> None:
        self._assert_all_roots(2, rules_count="")

    def test_stale_pr_head_is_pending_even_when_checks_pass(self) -> None:
        self._assert_all_roots(
            2, all_checks=f"[{PASS}]", head="old-sha", expected_sha="new-sha"
        )

    def test_unreadable_pr_head_is_pending(self) -> None:
        self._assert_all_roots(2, all_checks=f"[{PASS}]", expected_sha="new-sha")

    def test_matching_pr_head_with_passing_checks_is_green(self) -> None:
        self._assert_all_roots(
            0, all_checks=f"[{PASS}]", head="new-sha", expected_sha="new-sha"
        )


class ConfirmFixesStep8WiringTest(unittest.TestCase):
    def test_step8_first_ci_read_uses_the_sha_aware_predicate(self) -> None:
        for root in SKILL_ROOTS:
            with self.subTest(root=str(root.relative_to(REPO_ROOT))):
                content = (root / "lrh-confirm-fixes" / "SKILL.md").read_text()
                step8 = content.split("### Step 8", 1)[1]
                self.assertIn(
                    'check_ci_predicate <pr-url> "$(git rev-parse HEAD)"', step8
                )
                self.assertNotIn("gh pr checks <pr-url> --required", step8)
                self.assertIn("is a shell function, not a command", step8)


if __name__ == "__main__":
    unittest.main()
