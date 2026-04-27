---
execution_id: 2026_04_27_06_43_20_RELEASE_WORKFLOW_FIXES_REVIEW_FEEDBACK
prompt_id: PROMPT(AD_HOC:RELEASE_WORKFLOW_FIXES_REVIEW_FEEDBACK)[2026-04-27T06:35:00+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_04_27_06_15_06_RELEASE_WORKFLOW_FIXES
pr: 
commit: 
created_at: 2026-04-27T06:43:20+00:00
---

# Summary

Address PR review feedback on release smoke robustness and release workflow documentation prerequisites.

# Result

Updated `src/lrh/dev/release_smoke.py` so `_run()` now handles execution exceptions as `ReleaseSmokeError` and resolves default cwd at call time from current `REPO_ROOT`. Added tests covering these behaviors and updated README release steps with explicit `pip install -e ".[dev]"` prerequisite.

# Validation

- Ran `scripts/format --check` (fails due pre-existing unrelated formatting in `tests/control_tests/parser_test.py`).
- Ran `scripts/lint` (ruff passes; black check fails due same pre-existing formatting issue).
- Ran `scripts/test` (passes).
- Ran `python -m unittest tests.dev_tests.release_smoke_test` (passes).

# Follow-up

None.
