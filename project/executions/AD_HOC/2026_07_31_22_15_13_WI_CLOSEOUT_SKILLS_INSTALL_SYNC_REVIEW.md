---
execution_id: 2026_07_31_22_15_13_WI_CLOSEOUT_SKILLS_INSTALL_SYNC_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SKILLS_INSTALL_SYNC_REVIEW)[2026-07-31T21:56:12-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_31_21_38_13_WI_CLOSEOUT_SKILLS_INSTALL_SYNC
pr: https://github.com/xenotaur/logical_robotics_harness/pull/454
commit: ce5558a
created_at: 2026-07-31T22:15:13-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/454
session_transcript: pending
---

# Summary

Addressed 2 open review comments on PR #454
(`WI-CLOSEOUT-SKILLS-INSTALL-SYNC`): a grammar nit from
`copilot-pull-request-reviewer` and a P1 substantive finding from
`chatgpt-codex-connector` that the work item's proposed non-force
`lrh skills install` step cannot actually refresh a stale skill.

# Result

- Comment 1 (copilot-pull-request-reviewer, grammar): "found 6 diverged"
  read as ungrammatical. Fixed to "found 6 that had diverged" in
  `## Problem / Context`.
- Comment 2 (chatgpt-codex-connector, P1): confirmed valid —
  `_skill_differs_from_package` in `src/lrh/skills/installer.py`
  classifies any installed skill whose bytes differ from the current
  package as `USER_MODIFIED` and skips it, including a stale unmodified
  copy of the previous package revision. A plain non-force
  `lrh skills install` run after a skill-touching merge would therefore
  skip exactly the skills it's meant to fix — confirmed retroactively
  against the 6 skills found stale in the creation record's session, none
  of which would have been refreshed by a non-force run. Rescoped the
  work item's Scope, Required Changes, Non-Goals, Acceptance Criteria,
  Validation, and frontmatter `acceptance`/`artifacts_expected` from
  "blanket non-force install" to "targeted refresh of exactly the skill
  names the merged PR's diff touched," adding a Required Changes item for
  a new `installer.py` capability (force-install a named subset) with
  accompanying unit test coverage.
- Both fixes applied directly to
  `project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md`
  (planning-artifact text only — no code changed, since this PR only
  creates the work item, not its implementation).
- Pushed as commit `ce5558a`.

# Validation

- `scripts/version tools`: ruff 0.15.12, black 26.3.1, pylint 2.16.2,
  pyright not installed (pre-existing environment gap, unrelated to this
  change)
- `scripts/format --check --diff`: all 179 files unchanged
- `scripts/lint`: all checks passed
- `scripts/test`: OK
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- `session_transcript: pending` above should be updated to
  `claude-app:<host-uuid-stem>` after the session ends.
- Next: `/lrh-confirm-fixes` against PR #454 to verify these fixes and
  resolve the review threads before merge.
