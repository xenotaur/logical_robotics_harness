"""Unit tests for `lrh.closeout_pr_verifier`'s pure conformance checks.

These target the hermetic, no-I/O functions (`classify_path`,
`check_allowed_paths`, `check_chain_defaults_lines`,
`check_execution_record`, `check_head_and_ci`, `verify_closeout_pr`,
`_classify_ci_checks`), plus `run_verify_pr_cli`'s own hermetic early-error
paths (plan-file read/parse failures, which raise before any subprocess
call) -- never its I/O-heavy body, which shells out to `git`/`gh` and is
exercised manually against a real checkout instead, per this module's own
docstring.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest

from lrh import closeout_pr_verifier as verifier


class ClassifyPathTest(unittest.TestCase):
    def test_executions_prefix_is_allowed(self) -> None:
        self.assertEqual(
            verifier.classify_path("project/executions/AD_HOC/foo.md"), "allowed"
        )

    def test_work_items_prefix_is_allowed(self) -> None:
        self.assertEqual(
            verifier.classify_path("project/work_items/proposed/WI-FOO.md"), "allowed"
        )

    def test_workstreams_prefix_is_allowed(self) -> None:
        self.assertEqual(
            verifier.classify_path("project/workstreams/proposed/WS-FOO.md"), "allowed"
        )

    def test_design_proposals_prefix_is_allowed(self) -> None:
        self.assertEqual(
            verifier.classify_path(
                "project/design/proposals/adopted/foo/00_proposal.md"
            ),
            "allowed",
        )

    def test_session_index_exact_path_is_allowed(self) -> None:
        self.assertEqual(
            verifier.classify_path("project/sessions/index.jsonl"), "allowed"
        )

    def test_chain_defaults_is_its_own_class(self) -> None:
        self.assertEqual(
            verifier.classify_path("project/config/chain-defaults.yaml"),
            "chain_defaults",
        )

    def test_source_file_is_disallowed(self) -> None:
        self.assertEqual(
            verifier.classify_path("src/lrh/skills/lrh-land/SKILL.md"), "disallowed"
        )

    def test_similarly_named_but_different_directory_is_disallowed(self) -> None:
        # project/executions-archive/ must not match the project/executions/
        # prefix by bare string prefix accident.
        self.assertEqual(
            verifier.classify_path("project/executions-archive/foo.md"), "disallowed"
        )


class CheckAllowedPathsTest(unittest.TestCase):
    def test_all_allowed_paths_produce_no_divergence(self) -> None:
        divergences = verifier.check_allowed_paths(
            [
                "project/executions/AD_HOC/foo.md",
                "project/sessions/index.jsonl",
                "project/config/chain-defaults.yaml",
            ]
        )
        self.assertEqual(divergences, [])

    def test_one_disallowed_path_is_flagged(self) -> None:
        divergences = verifier.check_allowed_paths(
            ["project/executions/AD_HOC/foo.md", "src/lrh/closeout_pr_verifier.py"]
        )
        self.assertEqual(len(divergences), 1)
        self.assertIn("src/lrh/closeout_pr_verifier.py", divergences[0].detail)

    def test_multiple_disallowed_paths_are_each_flagged(self) -> None:
        divergences = verifier.check_allowed_paths(["a.py", "b.py"])
        self.assertEqual(len(divergences), 2)


class CheckChainDefaultsLinesTest(unittest.TestCase):
    def test_only_allowed_field_lines_changed_is_clean(self) -> None:
        old = (
            "chain_init_confirmation: skip_if_opted_in\n"
            "confirmed_commit: aaa\n"
            "confirmed_at: 2026-01-01T00:00:00Z\n"
        )
        new = (
            "chain_init_confirmation: skip_if_opted_in\n"
            "confirmed_commit: bbb\n"
            "confirmed_at: 2026-01-02T00:00:00Z\n"
        )
        self.assertEqual(verifier.check_chain_defaults_lines(old, new), [])

    def test_disallowed_field_line_change_is_a_divergence(self) -> None:
        old = "confirmed_commit: aaa\nconfirm_fixes_batch: always_confirm\n"
        new = "confirmed_commit: bbb\nconfirm_fixes_batch: auto_unless_unusual\n"
        divergences = verifier.check_chain_defaults_lines(old, new)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].field, "chain_defaults_line")

    def test_no_changes_is_clean(self) -> None:
        text = "confirmed_commit: aaa\n"
        self.assertEqual(verifier.check_chain_defaults_lines(text, text), [])

    def test_comment_only_change_is_a_divergence(self) -> None:
        # This is the whole point of a line-level, not field-level, check:
        # a comment edit changes the file's blob hash (what binds stored
        # skip_if_opted_in consent) even though no field value changed.
        old = "# old comment\nconfirmed_commit: aaa\n"
        new = "# updated comment\nconfirmed_commit: aaa\n"
        divergences = verifier.check_chain_defaults_lines(old, new)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].field, "chain_defaults_line")

    def test_whitespace_only_change_on_a_disallowed_field_is_a_divergence(
        self,
    ) -> None:
        old = "chain_init_confirmation: skip_if_opted_in\n"
        new = "chain_init_confirmation:   skip_if_opted_in\n"
        divergences = verifier.check_chain_defaults_lines(old, new)
        self.assertEqual(len(divergences), 1)

    def test_whitespace_only_change_on_an_allowed_field_is_clean(self) -> None:
        # confirmed_commit is one of the two lines a legitimate re-stamp is
        # allowed to rewrite -- reformatting its own value is not a separate
        # violation on top of that.
        old = "confirmed_commit: aaa\n"
        new = "confirmed_commit:   bbb\n"
        self.assertEqual(verifier.check_chain_defaults_lines(old, new), [])

    def test_new_disallowed_field_line_appearing_is_a_divergence(self) -> None:
        old = "confirmed_commit: aaa\n"
        new = "confirmed_commit: aaa\na_new_field_nobody_authorized: value\n"
        divergences = verifier.check_chain_defaults_lines(old, new)
        self.assertEqual(len(divergences), 1)

    def test_deleted_line_with_nothing_on_new_side_is_a_divergence(self) -> None:
        old = "confirmed_commit: aaa\nsome_field: value\n"
        new = "confirmed_commit: aaa\n"
        divergences = verifier.check_chain_defaults_lines(old, new)
        self.assertEqual(len(divergences), 1)


class CheckExecutionRecordTest(unittest.TestCase):
    def test_no_change_is_clean(self) -> None:
        old = {"status": "in_progress", "commit": ""}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=dict(old),
            expected_fields={},
        )
        self.assertEqual(verifier.check_execution_record(expectation), [])

    def test_commit_placeholder_fill_matching_expected_commit_is_clean(self) -> None:
        old = {"status": "in_progress", "commit": ""}
        new = {"status": "in_progress", "commit": "abc123"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={},
            expected_commit="abc123",
        )
        self.assertEqual(verifier.check_execution_record(expectation), [])

    def test_commit_change_with_no_expected_commit_supplied_is_a_divergence(
        self,
    ) -> None:
        # The bug this guards against: accepting *any* new commit value
        # just because the plan didn't separately name one, rather than
        # requiring the caller to state the actual merge SHA to check
        # against.
        old = {"status": "in_progress", "commit": ""}
        new = {"status": "in_progress", "commit": "abc123"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={},
            expected_commit=None,
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 1)
        self.assertIn("commit", divergences[0].field)

    def test_commit_change_not_matching_expected_commit_is_a_divergence(self) -> None:
        old = {"status": "in_progress", "commit": ""}
        new = {"status": "in_progress", "commit": "wrong-sha"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={},
            expected_commit="abc123",
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 1)

    def test_commit_overwrite_of_non_placeholder_value_is_a_divergence(self) -> None:
        # The old value wasn't actually a placeholder -- overwriting a real
        # commit value is not the mechanical fill-in this exception exists
        # for, even if the new value happens to match expected_commit.
        old = {"status": "in_progress", "commit": "already-set-sha"}
        new = {"status": "in_progress", "commit": "abc123"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={},
            expected_commit="abc123",
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 1)

    def test_status_change_matching_expected_fields_is_clean(self) -> None:
        old = {"status": "in_progress"}
        new = {"status": "landed"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={"status": "landed"},
        )
        self.assertEqual(verifier.check_execution_record(expectation), [])

    def test_unexpected_field_change_is_a_divergence(self) -> None:
        old = {"status": "in_progress", "pr": ""}
        new = {"status": "in_progress", "pr": "https://example.com/pull/1"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/foo.md",
            old_frontmatter=old,
            new_frontmatter=new,
            expected_fields={},
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 1)
        self.assertIn("pr", divergences[0].field)

    def test_new_record_matching_expected_fields_is_clean(self) -> None:
        new = {"status": "in_progress", "commit": ""}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/new_closeout_note.md",
            old_frontmatter=None,
            new_frontmatter=new,
            expected_fields=new,
        )
        self.assertEqual(verifier.check_execution_record(expectation), [])

    def test_new_record_not_matching_expected_fields_is_a_divergence(self) -> None:
        new = {"status": "in_progress"}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/new_closeout_note.md",
            old_frontmatter=None,
            new_frontmatter=new,
            expected_fields={"status": "landed"},
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 1)

    def test_new_record_with_no_expectation_at_all_is_flagged_for_every_field(
        self,
    ) -> None:
        # An execution record the plan never mentioned appearing at all --
        # the "newly appeared execution record" material-divergence case.
        new = {"status": "in_progress", "commit": ""}
        expectation = verifier.ExecutionRecordExpectation(
            path="project/executions/AD_HOC/unplanned.md",
            old_frontmatter=None,
            new_frontmatter=new,
            expected_fields={},
        )
        divergences = verifier.check_execution_record(expectation)
        self.assertEqual(len(divergences), 2)


class CheckHeadAndCiTest(unittest.TestCase):
    def test_matching_head_clean_mergeable_green_ci_is_clean(self) -> None:
        divergences = verifier.check_head_and_ci(
            actual_head="abc",
            expected_head="abc",
            mergeable="MERGEABLE",
            ci_status="green",
        )
        self.assertEqual(divergences, [])

    def test_head_mismatch_is_a_divergence(self) -> None:
        divergences = verifier.check_head_and_ci(
            actual_head="abc",
            expected_head="def",
            mergeable="MERGEABLE",
            ci_status="green",
        )
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].field, "head_sha")

    def test_conflicting_mergeable_is_a_divergence(self) -> None:
        divergences = verifier.check_head_and_ci(
            actual_head="abc",
            expected_head="abc",
            mergeable="CONFLICTING",
            ci_status="green",
        )
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].field, "mergeable")

    def test_ci_not_green_is_a_divergence(self) -> None:
        divergences = verifier.check_head_and_ci(
            actual_head="abc",
            expected_head="abc",
            mergeable="MERGEABLE",
            ci_status="pending",
        )
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].field, "ci_status")

    def test_all_three_wrong_reports_all_three(self) -> None:
        divergences = verifier.check_head_and_ci(
            actual_head="abc",
            expected_head="def",
            mergeable="CONFLICTING",
            ci_status="not_green",
        )
        self.assertEqual(len(divergences), 3)


class ClassifyCiChecksTest(unittest.TestCase):
    def test_empty_checks_is_pending(self) -> None:
        self.assertEqual(verifier._classify_ci_checks([]), "pending")

    def test_all_pass_is_green(self) -> None:
        checks = [
            {"name": "tests", "bucket": "pass"},
            {"name": "lint", "bucket": "pass"},
        ]
        self.assertEqual(verifier._classify_ci_checks(checks), "green")

    def test_any_fail_is_not_green(self) -> None:
        checks = [
            {"name": "tests", "bucket": "pass"},
            {"name": "lint", "bucket": "fail"},
        ]
        self.assertEqual(verifier._classify_ci_checks(checks), "not_green")

    def test_any_pending_with_no_failures_is_pending(self) -> None:
        checks = [
            {"name": "tests", "bucket": "pass"},
            {"name": "lint", "bucket": "pending"},
        ]
        self.assertEqual(verifier._classify_ci_checks(checks), "pending")

    def test_fail_takes_priority_over_pending(self) -> None:
        checks = [
            {"name": "tests", "bucket": "fail"},
            {"name": "lint", "bucket": "pending"},
        ]
        self.assertEqual(verifier._classify_ci_checks(checks), "not_green")


class VerifyCloseoutPrTest(unittest.TestCase):
    def test_fully_conforming_pr_is_clean(self) -> None:
        result = verifier.verify_closeout_pr(
            changed_paths=["project/executions/AD_HOC/foo.md"],
            chain_defaults_old_text=None,
            chain_defaults_new_text=None,
            execution_records=[
                verifier.ExecutionRecordExpectation(
                    path="project/executions/AD_HOC/foo.md",
                    old_frontmatter={"status": "in_progress", "commit": ""},
                    new_frontmatter={"status": "landed", "commit": "sha123"},
                    expected_fields={"status": "landed"},
                    expected_commit="sha123",
                )
            ],
            actual_head="sha123",
            expected_head="sha123",
            mergeable="MERGEABLE",
            ci_status="green",
        )
        self.assertTrue(result.conforms)
        self.assertEqual(result.divergences, ())

    def test_disallowed_path_makes_it_not_conform(self) -> None:
        result = verifier.verify_closeout_pr(
            changed_paths=["src/lrh/some_module.py"],
            chain_defaults_old_text=None,
            chain_defaults_new_text=None,
            execution_records=[],
            actual_head="sha123",
            expected_head="sha123",
            mergeable="MERGEABLE",
            ci_status="green",
        )
        self.assertFalse(result.conforms)
        self.assertEqual(len(result.divergences), 1)

    def test_chain_defaults_changed_but_fields_not_supplied_is_a_divergence(
        self,
    ) -> None:
        result = verifier.verify_closeout_pr(
            changed_paths=["project/config/chain-defaults.yaml"],
            chain_defaults_old_text=None,
            chain_defaults_new_text=None,
            execution_records=[],
            actual_head="sha123",
            expected_head="sha123",
            mergeable="MERGEABLE",
            ci_status="green",
        )
        self.assertFalse(result.conforms)
        self.assertTrue(
            any(d.field == verifier.CHAIN_DEFAULTS_PATH for d in result.divergences)
        )

    def test_mismatched_old_and_new_none_ness_for_chain_defaults_raises(self) -> None:
        with self.assertRaises(ValueError):
            verifier.verify_closeout_pr(
                changed_paths=[],
                chain_defaults_old_text="a: b\n",
                chain_defaults_new_text=None,
                execution_records=[],
                actual_head="sha123",
                expected_head="sha123",
                mergeable="MERGEABLE",
                ci_status="green",
            )

    def test_multiple_divergence_sources_are_all_reported(self) -> None:
        result = verifier.verify_closeout_pr(
            changed_paths=["src/lrh/some_module.py"],
            chain_defaults_old_text=None,
            chain_defaults_new_text=None,
            execution_records=[],
            actual_head="sha123",
            expected_head="different-sha",
            mergeable="CONFLICTING",
            ci_status="not_green",
        )
        self.assertFalse(result.conforms)
        # 1 disallowed-path divergence + 3 head/mergeable/ci divergences.
        self.assertEqual(len(result.divergences), 4)


class RunVerifyPrCliHermeticErrorPathsTest(unittest.TestCase):
    """`run_verify_pr_cli` reads and parses its plan file before making any
    subprocess call, so these two failure paths are hermetic and testable
    directly, unlike the rest of the function's I/O-heavy body."""

    def test_missing_plan_file_raises_verification_run_error(self) -> None:
        with self.assertRaises(verifier.VerificationRunError):
            verifier.run_verify_pr_cli(
                pr_url="https://example.com/pull/1",
                expected_head="abc",
                expected_commit=None,
                plan_file="/nonexistent/path/plan.json",
                project_root=pathlib.Path("/tmp"),
            )

    def test_invalid_json_plan_file_raises_verification_run_error(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as handle:
            handle.write("{not valid json")
            path = handle.name
        try:
            with self.assertRaises(verifier.VerificationRunError):
                verifier.run_verify_pr_cli(
                    pr_url="https://example.com/pull/1",
                    expected_head="abc",
                    expected_commit=None,
                    plan_file=path,
                    project_root=pathlib.Path("/tmp"),
                )
        finally:
            os.unlink(path)

    def test_valid_plan_file_parses_without_error(self) -> None:
        # Sanity check that a *valid* plan file's JSON parses cleanly (the
        # hermetic portion this test class covers), independent of whatever
        # the non-hermetic subprocess portion of the function would do next.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as handle:
            json.dump({"execution_records": {"a/b.md": {"status": "landed"}}}, handle)
            path = handle.name
        try:
            plan_text = pathlib.Path(path).read_text(encoding="utf-8")
            plan = json.loads(plan_text)
            self.assertEqual(plan["execution_records"]["a/b.md"]["status"], "landed")
        finally:
            os.unlink(path)


class FormatTest(unittest.TestCase):
    def test_format_text_conforms(self) -> None:
        result = verifier.VerificationResult(conforms=True, divergences=())
        text = verifier.format_text(result)
        self.assertIn("conforms: yes", text)

    def test_format_text_diverges(self) -> None:
        result = verifier.VerificationResult(
            conforms=False,
            divergences=(verifier.Divergence(field="head_sha", detail="mismatch"),),
        )
        text = verifier.format_text(result)
        self.assertIn("conforms: no", text)
        self.assertIn("head_sha", text)

    def test_format_json_round_trips_shape(self) -> None:
        import json

        result = verifier.VerificationResult(
            conforms=False,
            divergences=(verifier.Divergence(field="head_sha", detail="mismatch"),),
        )
        parsed = json.loads(verifier.format_json(result))
        self.assertFalse(parsed["conforms"])
        self.assertEqual(parsed["divergences"][0]["field"], "head_sha")


if __name__ == "__main__":
    unittest.main()
