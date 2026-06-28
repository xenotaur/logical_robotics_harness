---
execution_id: 2026_06_28_12_11_55_WI_PROMPT_CLI_CLOSEOUT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PROMPT_CLI_CLOSEOUT_REVIEW)[2026-06-28T11:57:04-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_06_28_11_36_25_WI_PROMPT_CLI_CLOSEOUT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/345
commit: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/345
session_transcript: pending
created_at: 2026-06-28T12:11:55-04:00
---

# Summary

Address 10 review comments on PR #345 (WI-PROMPT-CLI-CLOSEOUT): frontmatter
scoping bug, hard-coded lrh path, status transition guard, test fixture format,
and documentation section ordering.

# Result

- **Bug fix (chatgpt-codex + copilot):** `_replace_or_insert_frontmatter_field`
  now scopes replacement to the leading `---` frontmatter block only; regex
  changed to `^field:.*$` (matches `pr:` with or without trailing space).
  Added body-field safety regression test.
- **Bug fix (copilot):** Status transition guard restricted to `in_progress`
  only; `landed` removed from allowed set.
- **Test fix (copilot ×2):** Test fixtures updated to use `pr:` / `commit:`
  without trailing space, matching the real format of older execution records.
- **Doc fix (chatgpt-codex + copilot ×3):** Replaced hard-coded
  `/Users/centaur/anaconda3/envs/LRH/bin/lrh` with bare `lrh` in SKILL.md
  Step 5, `closeout-workflow.md`, and `execution-session-reference.md`.
  Mirrored to `.claude/skills/lrh-closeout/`.
- **Doc fix (copilot):** Restored `check-execution` description ("If this
  returns a `landed` or `in_progress` record...") to its correct position
  above the new `update-execution` section; added output description to
  `update-execution` section.

# Validation

- `lrh validate` — 0 errors, 0 warnings
- 15/15 tests pass (10 existing + 5 new)
- `black --check` + `ruff check` — clean
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` — identical

# Follow-up

- Merge PR #345
- Run `/lrh-closeout` to resolve WI-PROMPT-CLI-CLOSEOUT; close WS-SKILLS-CLOSEOUT;
  adopt PROP-LRH-CLOSEOUT
