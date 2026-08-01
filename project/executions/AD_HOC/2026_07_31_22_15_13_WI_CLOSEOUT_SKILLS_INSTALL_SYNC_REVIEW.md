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
session_transcript: claude-app:local_20d16dd9-a465-4d31-b39f-280db14488ef
---

# Summary

Addressed 2 open review comments on PR #454
(`WI-CLOSEOUT-SKILLS-INSTALL-SYNC`): a grammar nit from
`copilot-pull-request-reviewer` and a P1 substantive finding from
`chatgpt-codex-connector` that the work item's proposed non-force
`lrh skills install` step cannot actually refresh a stale skill. A
follow-up Copilot review of the fix commit raised 3 more findings (as a
summary body, 0 new inline comments); 1 was valid and fixed, 2 were
checked against this skill's own documented conventions and found false.

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

**Follow-up round** — a second Copilot review (bound to commit
`3443565`, triggered by re-requesting Copilot review) raised 3 findings
as suppressed/summary comments (0 new inline threads):
- "`status: in_progress` is an outlier vs. other `_REVIEW` records" —
  **checked and found false**: all 98 other `_REVIEW` records under
  `project/executions/AD_HOC/` show `status: landed` only because
  `/lrh-closeout` has already landed them; a freshly created,
  not-yet-closed-out record is supposed to be `in_progress` per this
  skill's own Step 7 (`--status in_progress`). Not changed.
- "`session_transcript: pending` should be a concrete value like other
  records" — the literal value this skill's Step 7 instructs
  (`session_transcript: pending`), so the finding's stated premise is
  wrong, but the underlying suggestion is a genuine improvement:
  `$CLAUDE_CODE_HOST_SESSION_ID` is available and stable for this session
  (already used to populate the sibling creation record), so filled in
  `session_transcript: claude-app:local_20d16dd9-a465-4d31-b39f-280db14488ef`
  here too for consistency, and dropped the now-stale "update later"
  follow-up note.
- "`lrh-create-skill` is not the only skill documenting `lrh skills
  install`" — **confirmed valid**: `lrh-implement`'s reference doc
  (`references/lrh-implement-workflow.md`) has its own `### lrh skills
  install` section, and `_shared/lifecycle-chain.md`'s table also
  mentions it (in `lrh-create-skill`'s own row). Reworded the WI's
  `## Problem / Context` claim from "the only skill that documents..." to
  precisely state that `lrh-create-skill` is the only skill whose *own
  execution steps* direct the agent to run it, and dropped the brittle
  line-number citations per the review's secondary point.
- Pushed as commit (this record's `commit:` field, populated at push
  time).

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

- Next: `/lrh-confirm-fixes` against PR #454 to verify these fixes and
  resolve the review threads before merge.
