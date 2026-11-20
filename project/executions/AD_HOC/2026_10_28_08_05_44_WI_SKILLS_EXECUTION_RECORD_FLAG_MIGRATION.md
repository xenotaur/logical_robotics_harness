---
execution_id: 2026_10_28_08_05_44_WI_SKILLS_EXECUTION_RECORD_FLAG_MIGRATION
prompt_id: PROMPT(AD_HOC:WI_SKILLS_EXECUTION_RECORD_FLAG_MIGRATION)[2026-10-27T05:19:58+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/858
commit:
created_at: 2026-10-28T08:05:44+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION.md
session_transcript: claude-app:c5f26330-07dd-4169-bb76-4dbbf2e696e0
---

# Summary

Created work item WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION, the skill-text follow-up deferred out of PR #794: migrate the skills that create execution records to pass `--agent`, `--instruction-source`, and `--session-transcript` instead of instructing a hand-edit.

# Result

Added `project/work_items/proposed/WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION.md` and opened PR #858. Before drafting, the repo was re-checked after a two-week pause: the CLI flags are intact on `main`, 13 canonical skill files still carry the hand-edit instruction, `lrh-self-review` still sets none of the three fields, and the mirrors now include `.gemini/plugins/lrh/skills`, so each edit lands in four copies. Commit ae11e699 (PR-linking for `/lrh-implement`) had already fixed one of the two friction points seen in the PR #794 run, so it is not in scope. PR #824 merged between drafting and filing, so the risk note names only the still-open #854 and #856. The item is `prompt_ready: yes`. This record was created with the new flags, with no hand-edit of the three fields.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-EXECUTION-RECORD-FLAG-MIGRATION`: `prompt_ready: yes`, no blocking items or warnings.

# Follow-up

- `/lrh-land` PR #858 before any execution of this work item; do not run `/lrh-execute` or `/lrh-implement` on it until it is on `main`.
- Execute only after open PRs #854 and #856 land, or rebase onto them.
- No workstream was identified, so no workstream update was offered.
