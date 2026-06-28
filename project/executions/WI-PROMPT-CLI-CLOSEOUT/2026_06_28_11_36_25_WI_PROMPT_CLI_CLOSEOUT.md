---
execution_id: 2026_06_28_11_36_25_WI_PROMPT_CLI_CLOSEOUT
prompt_id: PROMPT(WI-PROMPT-CLI-CLOSEOUT:WI_PROMPT_CLI_CLOSEOUT)[2026-06-28T11:30:26-04:00]
work_item: WI-PROMPT-CLI-CLOSEOUT
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/345
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-PROMPT-CLI-CLOSEOUT.md
session_transcript: pending
created_at: 2026-06-28T11:36:25-04:00
---

# Summary

Implement `lrh prompt update-execution` CLI subcommand (Phase 2 of
WS-SKILLS-CLOSEOUT). Upgrade `/lrh-closeout` Step 5 from edit-in-place to
call the CLI. Add 4 new tests, update skill docs and reference files.

# Result

- `src/lrh/prompt_workflow.py`: added `update-execution` subparser,
  `_replace_or_insert_frontmatter_field` helper, `find_execution_record_by_id`,
  and handler. Validates `in_progress → landed` transition; requires `--commit`;
  inserts `session_transcript:` after `commit:` if absent.
- `tests/cli_tests/prompt_test.py`: 4 new tests (success path,
  session_transcript insertion, missing --commit error, unknown ID returns 1).
- `src/lrh/skills/lrh-closeout/SKILL.md`: Step 5 now calls
  `lrh prompt update-execution`; description updated; Phase 1 caveat removed.
- `src/lrh/skills/lrh-closeout/references/closeout-workflow.md`: pending update
  example uses `lrh prompt update-execution`.
- `src/lrh/skills/lrh-implement/references/execution-session-reference.md`:
  `update-execution` command section added.
- `.claude/skills/lrh-closeout/` mirrored byte-for-byte.

# Validation

- `lrh validate` — 0 errors, 0 warnings
- 14/14 tests pass (10 existing + 4 new)
- `black --check` + `ruff check` — clean
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` — identical

# Follow-up

- Merge PR #345
- Run `/lrh-closeout` to resolve WI-PROMPT-CLI-CLOSEOUT; close WS-SKILLS-CLOSEOUT;
  adopt PROP-LRH-CLOSEOUT
