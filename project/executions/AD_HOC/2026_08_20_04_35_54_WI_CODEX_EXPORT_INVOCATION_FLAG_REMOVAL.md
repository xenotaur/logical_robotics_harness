---
execution_id: 2026_08_20_04_35_54_WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL
prompt_id: PROMPT(AD_HOC:WI_CODEX_EXPORT_INVOCATION_FLAG_REMOVAL)[2026-08-20T04:34:28+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/571
commit: e27caf103ed78bbac7450028ec4ac9d594b9f8f3
agent: claude_code
instruction_source: project/work_items/proposed/WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL.md
session_transcript: claude-app:local_dd7df709-1e50-4e78-a5bf-802d06e31d50
created_at: 2026-08-20T04:35:54+00:00
---

# Summary

Created `WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL` — planning artifact only,
no implementation yet. Captures a gap surfaced while landing PR #566
(`lrh-self-review`'s recursion guard): `lrh-codex-export` still carries
`disable-model-invocation: true`, and unlike the 4 skills
`WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` closed out, this skill was
never in scope for either it or the original
`WI-DELIBERATE-MODEL-INVOCATION` — added later (PR #532), after both items'
scope was fixed. Nobody has evaluated whether it needs the flag.

# Result

- `project/work_items/proposed/WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL.md`
  written, interviewed and confirmed with the user before writing.
- Prior art check: no duplicate work item; `lrh-codex-export`'s origin
  workstream (`WS-LRH-CODEX-APP-SERVER-EXPORT`) is resolved and never
  mentioned the flag; no backlog entry.
- Opened as PR #571.

# Validation

- `PYTHONPATH=src PATH=/Users/centaur/anaconda3/envs/LRH/bin:$PATH python -m lrh.cli.main validate` — 0 errors, 0 warnings

# Follow-up

Implementation (the actual assessment and, if warranted, flag removal) is
separate scope for `/lrh-implement` or `/lrh-execute` against this work
item once it's ready.
