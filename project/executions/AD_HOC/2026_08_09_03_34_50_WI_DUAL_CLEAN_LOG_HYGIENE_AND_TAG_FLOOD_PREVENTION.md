---
execution_id: 2026_08_09_03_34_50_WI_DUAL_CLEAN_LOG_HYGIENE_AND_TAG_FLOOD_PREVENTION
prompt_id: PROMPT(AD_HOC:WI_DUAL_CLEAN_LOG_HYGIENE_AND_TAG_FLOOD_PREVENTION)[2026-08-08T22:32:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/529
commit: fdea8c43
agent: antigravity
instruction_source: project/work_items/proposed/WI-DUAL-CLEAN-LOG-HYGIENE-AND-TAG-FLOOD-PREVENTION.md
session_transcript: pending
created_at: 2026-08-09T03:34:50+00:00
---

# Summary

Implemented the Dual-Clean Pattern in helper scripts (`scripts/test`, `scripts/validate`) and skill templates (`.claude/skills/`, `src/lrh/skills/`) to eliminate XML/HTML tag cascades in agent UI renderers during test runs without suppressing test diagnostics or altering default streaming output for human maintainers.

# Result

- Minted prompt ID `PROMPT(AD_HOC:WI_DUAL_CLEAN-LOG_HYGIENE_AND_TAG_FLOOD_PREVENTION)[2026-08-08T22:32:31+00:00]`.
- Updated `scripts/test` and `scripts/validate` to support opt-in `--log` flag and `LRH_LOG_REDIRECT=1` environment variable while preserving 100% standard streaming stdout/stderr by default.
- Added unit test `tests/scripts_tests/scripts_log_redirection_test.py` covering default streaming and `--log` redirection.
- Updated skill references (`canonical-validation.md`, `lrh-execute/SKILL.md`, `lrh-self-review/SKILL.md`) under `.claude/skills/` and `src/lrh/skills/` with Markdown code-fencing rules and `--log` validation instructions.
- Committed change `fdea8c43` and pushed to PR #529 (`https://github.com/xenotaur/logical_robotics_harness/pull/529`).

# Validation

- Ran `scripts_log_redirection_test.py` unit tests (4 tests OK).
- Ran `lrh validate` (passed with 0 errors, 1 unrelated warning).
- Confirmed `diff -r src/lrh/skills/ .claude/skills/` skill Markdown copies are 100% byte-for-byte identical.

# Follow-up

- Ready for confirm-fixes and merge gate authorization (`/lrh-confirm-fixes` / `/lrh-land`).

