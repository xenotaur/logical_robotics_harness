---
execution_id: 2026_07_18_02_46_34_WI_SKILLS_PLANNING_SKILLS_COMPOSABLE
prompt_id: PROMPT(WI-SKILLS-PLANNING-SKILLS-COMPOSABLE:WI_SKILLS_PLANNING_SKILLS_COMPOSABLE)[2026-07-18T02:43:20-04:00]
work_item: WI-SKILLS-PLANNING-SKILLS-COMPOSABLE
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/399
commit: 67c1230e2e6f36c3266c03537ba27c41c20537e0
created_at: 2026-07-18T02:46:34-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-PLANNING-SKILLS-COMPOSABLE.md
session_transcript: claude-app:49a80683-68ef-40ff-a81c-28253a11ca8e
---

# Summary

Make `/lrh-proposal` and `/lrh-workstream` composable per
`WI-SKILLS-PLANNING-SKILLS-COMPOSABLE`, extending the treatment already
applied to `/lrh-work-item` (`WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE`, PR #331).

# Result

Edited `src/lrh/skills/lrh-proposal/SKILL.md` and
`src/lrh/skills/lrh-workstream/SKILL.md`: removed
`disable-model-invocation: true` from both frontmatter blocks, replaced with
a `when_to_use` field restricting auto-trigger to explicit creation contexts
and naming plausible orchestrating callers (`/lrh-design` for `lrh-proposal`;
`/lrh-design` and `/lrh-proposal` for `lrh-workstream`).

Added an "Orchestration: invoking this skill from other skills" section to
`src/lrh/skills/lrh-proposal/references/proposal-body-guide.md` and
`src/lrh/skills/lrh-workstream/references/workstream-body-guide.md`,
mirroring `lrh-work-item-workflow.md`'s precedent section: the Step 4 confirm
gate — not the invocation flag — is the write protection, per OWASP LLM08.

Mirrored all four edits to `.claude/skills/`. The Step 4 confirm gate in
both skills is unchanged.

Confirmed the change is functionally live in this session's own harness:
the skill listing surfaced by the system immediately after the edit showed
both `/lrh-proposal` and `/lrh-workstream` without the invocation block.

No workstream to update (`related_workstreams: []` — standalone WI by
design, matching the `WI-SKILLS-LRH-WORK-ITEM-COMPOSABLE` precedent).

# Validation

```
scripts/version tools  — lrh 0.2.5.dev83, Ruff 0.15.12, Black 25.11.0 confirmed
scripts/format --check --diff  — skipped: no Python files changed (markdown-only skill edits)
scripts/lint  — skipped: no Python files changed
scripts/test  — skipped: no Python files changed
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-proposal/ .claude/skills/lrh-proposal/  — identical
diff -r src/lrh/skills/lrh-workstream/ .claude/skills/lrh-workstream/  — identical
```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after the
  session ends.
- Does not wire `/lrh-design` (or any other skill) to actually *call*
  `/lrh-proposal` or `/lrh-workstream` — this WI only removed the invocation
  block. Orchestration logic in a calling skill is separate follow-on work
  (explicitly out of scope per the WI's Non-Goals).
