"""Unit tests for `lrh.confirm_fixes_batch`'s routine-batch predicate."""

from __future__ import annotations

import unittest

from lrh import confirm_fixes_batch


class IsRoutineBatchTest(unittest.TestCase):
    def test_empty_batch_is_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            (), ci_ok=True, had_prior_exception=False
        )
        self.assertTrue(result.routine)
        self.assertIn("no unresolved threads", result.reason)

    def test_all_clear_satisfied_is_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("clear_satisfied", "clear_satisfied", "clear_satisfied"),
            ci_ok=True,
            had_prior_exception=False,
        )
        self.assertTrue(result.routine)
        self.assertIn("3 thread(s)", result.reason)

    def test_single_unaddressed_thread_is_not_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("clear_satisfied", "unaddressed"),
            ci_ok=True,
            had_prior_exception=False,
        )
        self.assertFalse(result.routine)
        self.assertIn("unaddressed", result.reason)

    def test_partial_is_not_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("partial",), ci_ok=True, had_prior_exception=False
        )
        self.assertFalse(result.routine)

    def test_ambiguous_is_not_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("ambiguous",), ci_ok=True, had_prior_exception=False
        )
        self.assertFalse(result.routine)

    def test_problematic_resolution_is_not_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("problematic_resolution",), ci_ok=True, had_prior_exception=False
        )
        self.assertFalse(result.routine)

    def test_problematic_comment_is_not_routine(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("problematic_comment",), ci_ok=True, had_prior_exception=False
        )
        self.assertFalse(result.routine)

    def test_failing_ci_is_not_routine_even_if_all_clear(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("clear_satisfied",), ci_ok=False, had_prior_exception=False
        )
        self.assertFalse(result.routine)
        self.assertIn("CI", result.reason)

    def test_prior_exception_is_not_routine_even_if_all_clear_and_ci_ok(
        self,
    ) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("clear_satisfied",), ci_ok=True, had_prior_exception=True
        )
        self.assertFalse(result.routine)
        self.assertIn("earlier confirm-fixes round", result.reason)

    def test_prior_exception_checked_before_ci_and_buckets(self) -> None:
        # If multiple disqualifying conditions hold at once, the
        # prior-exception check should still be the one reported --
        # order matters for a clear, single-cause explanation.
        result = confirm_fixes_batch.is_routine_batch(
            ("unaddressed",), ci_ok=False, had_prior_exception=True
        )
        self.assertFalse(result.routine)
        self.assertIn("earlier confirm-fixes round", result.reason)

    def test_unknown_bucket_label_fails_safe(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("some_new_bucket_a_future_taxonomy_change_might_add",),
            ci_ok=True,
            had_prior_exception=False,
        )
        self.assertFalse(result.routine)
        self.assertIn("unrecognized bucket label", result.reason)

    def test_mixed_clear_and_unroutine_reports_all_hits(self) -> None:
        result = confirm_fixes_batch.is_routine_batch(
            ("clear_satisfied", "unaddressed", "partial", "clear_satisfied"),
            ci_ok=True,
            had_prior_exception=False,
        )
        self.assertFalse(result.routine)
        self.assertIn("unaddressed", result.reason)
        self.assertIn("partial", result.reason)


if __name__ == "__main__":
    unittest.main()
