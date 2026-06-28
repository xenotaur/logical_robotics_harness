---
execution_id: 2026_06_28_14_25_10_LRH_SETUP_CLI_TESTS_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_SETUP_CLI_TESTS_REVIEW)[2026-06-28T14:16:23-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_06_28_14_06_26_LRH_SETUP_CLI_TESTS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/346
commit: 348b2f6074e327d314ebf7a97186ced7b9ac44f4
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/346
session_transcript: claude-app:6f9b846e-c6f9-45aa-9cf9-8c744ec57026
created_at: 2026-06-28T14:25:10-04:00
---

# Summary

Address 2 review comments (same issue) on PR #346: dry-run tests were not
hermetic because they hit the real `~/.claude/skills/` directory.

# Result

- Added `_run_isolated()` helper that sets `HOME` and `USERPROFILE` to a
  temp dir before running the subprocess, so `_DEFAULT_SKILLS_DIR` resolves
  to an empty path in the subprocess.
- Updated the three `--dry-run` tests to use `_run_isolated()`; kept `_run()`
  for `test_setup_help_exits_zero` (argparse --help runs before installer
  imports).

# Validation

- 4/4 tests pass
- `lrh validate` — 0 errors, 0 warnings
- `black --check` + `ruff check` — clean

# Follow-up

- Merge PR #346
- Run `/lrh-closeout` to land records; close WS-SKILLS-CLOSEOUT
