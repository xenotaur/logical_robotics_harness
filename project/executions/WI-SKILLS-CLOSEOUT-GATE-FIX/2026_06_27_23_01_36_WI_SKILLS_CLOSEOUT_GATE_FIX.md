---
execution_id: 2026_06_27_23_01_36_WI_SKILLS_CLOSEOUT_GATE_FIX
prompt_id: PROMPT(WI-SKILLS-CLOSEOUT-GATE-FIX:WI_SKILLS_CLOSEOUT_GATE_FIX)[2026-06-27T22:58:13-04:00]
work_item: WI-SKILLS-CLOSEOUT-GATE-FIX
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/343
commit: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-CLOSEOUT-GATE-FIX.md
session_transcript: pending
created_at: 2026-06-27T23:01:36-04:00
---

# Summary

Surface the WS `exit_criteria:` list in `/lrh-closeout` Step 2 and require
explicit human confirmation of each criterion at the Step 4 gate before WS
closeout proceeds. Fixes the premature WS closure gap identified 2026-06-27.

# Result

- `SKILL.md` Step 2 WS block: reads `exit_criteria:` when structural check
  passes; includes full list in plan output
- `SKILL.md` Step 4 confirm gate: enumerates exit criteria and asks user
  to confirm all are met before WS closeout is included in confirmed plan
- `SKILL.md` "What This Skill Does Not Do": updated bullet to reflect new
  surfacing behavior (still no programmatic enforcement of prose criteria)
- `references/closeout-workflow.md` readiness check: notes structural check
  is necessary but not sufficient; exit_criteria must be confirmed at Step 4
- `.claude/skills/lrh-closeout/` mirrored byte-for-byte

# Validation

- `lrh validate` — 0 errors, 0 warnings
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` — identical
- `scripts/version tools` / `scripts/format` / `scripts/lint` / `scripts/test` —
  unavailable outside conda env; N/A for Markdown-only changes

# Follow-up

- Merge PR #343
- Run `/lrh-closeout` to resolve WI-SKILLS-CLOSEOUT-GATE-FIX and update session_transcript
