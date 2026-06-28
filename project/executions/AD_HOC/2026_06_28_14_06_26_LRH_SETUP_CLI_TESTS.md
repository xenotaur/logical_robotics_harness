---
execution_id: 2026_06_28_14_06_26_LRH_SETUP_CLI_TESTS
prompt_id: PROMPT(AD_HOC:LRH_SETUP_CLI_TESTS)[2026-06-28T14:03:25-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/346
commit: 
agent: claude_app
instruction_source: ad_hoc — add CLI subprocess tests for lrh setup command
session_transcript: pending
created_at: 2026-06-28T14:06:26-04:00
---

# Summary

Add CLI subprocess tests for `lrh setup` command. The library-level installer
was already tested in `tests/skills_installer_test.py`; the CLI wiring layer
was untested.

# Result

Created `tests/cli_tests/setup_test.py` with 4 tests:
- `test_setup_help_exits_zero` — `lrh setup --help` exits 0, surfaces `--dry-run` and `--force`
- `test_setup_dry_run_exits_zero` — `lrh setup --dry-run` exits 0
- `test_setup_dry_run_reports_would_install` — output contains `"would install"`
- `test_setup_dry_run_suppresses_restart_note` — dry-run suppresses `"Restart Claude Code"`

# Validation

- 4/4 new tests pass
- `lrh validate` — 0 errors, 0 warnings
- `black --check` + `ruff check` — clean

# Follow-up

- Merge PR #346
- Run `/lrh-closeout` to land this record; close WS-SKILLS-CLOSEOUT
