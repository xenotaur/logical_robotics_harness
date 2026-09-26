---
execution_id: 2026_09_26_02_41_01_WI_TEST_OUTPUT_SUPPRESSION_AUDIT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TEST_OUTPUT_SUPPRESSION_AUDIT_REVIEW)[2026-09-26T02:03:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_01_54_22_WI_TEST_OUTPUT_SUPPRESSION_AUDIT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/731
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/731
session_transcript: claude-app:42f65eea-a5d0-4b14-b12d-fdac79928916
created_at: 2026-09-26T02:41:01+00:00
---

# Summary

Addressed 4 open review comments on PR #731 (3 Codex P1, 1 Copilot),
all against `project/work_items/proposed/WI-TEST-OUTPUT-SUPPRESSION-AUDIT.md`.

# Result

All four comments passed presence/validity/feasibility and were fixed:

1. **Tracked-only search** (Codex P1, `r4109807180`) — both the
   migration-inventory grep and the follow-up audit grep now use
   `git grep -l '...' -- 'tests/**/*_test.py'` instead of a recursive
   filesystem `grep`, which could have picked up untracked files or
   nested checkouts outside the reviewed tree. Verified the suggested
   command actually returns the stated count (12 files).
2. **Route through scripts/test** (Codex P1, `r4109807184`) — the
   guardrails-test Validation bullet now reads
   `scripts/test tests.guardrails_tests.test_framework_guardrails_test -v`
   instead of bare `python -m unittest ...`.
3. **Keep the test-only helper out of the runtime package** (Codex P1,
   `r4109807186`) and the matching **artifacts_expected inconsistency**
   (Copilot, `r4109810123`, flagged at 4 occurrences) — both point at the
   same root cause: the work item hedged between `src/lrh/shared/test_capture.py`
   and an unnamed tests-only alternative. Committed definitively to
   `tests/testing_support.py` in `artifacts_expected` and in the Required
   Changes prose; no remaining mention of `src/lrh/shared` anywhere in the
   file (checked via grep after editing).

No comments were skipped.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `scripts/test` — 1730 tests, OK (Markdown-only change; run for
  regression safety, not because Python code changed).
- `scripts/lint` — fails only on the pre-existing, unrelated local
  ruff/black tool-version mismatch (documented in PR #725); not caused by
  and not relevant to this Markdown-only change.

# Follow-up

None. Recommend `/lrh-confirm-fixes` next per this skill's own guidance.
