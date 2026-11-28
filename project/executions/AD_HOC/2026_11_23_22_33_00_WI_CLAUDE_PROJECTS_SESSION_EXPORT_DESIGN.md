---
execution_id: 2026_11_23_22_33_00_WI_CLAUDE_PROJECTS_SESSION_EXPORT_DESIGN
prompt_id: PROMPT(AD_HOC:WI_CLAUDE_PROJECTS_SESSION_EXPORT_DESIGN)[2026-11-23T22:29:37+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/877
commit:
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN.md
session_transcript: claude-app:67830d77-705f-4389-a55e-77757767ff7e
created_at: 2026-11-23T22:33:00+00:00
---

# Summary

Created the proposed work item `WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN`
through `/lrh-work-item`. It is an investigation item asking for a design
session and a proposal on how LRH captures Claude Projects conversations:
the coordinator conversation, linked-folder threads, and Project cloud
threads. This record documents the creation of the work item, not its
implementation.

# Result

- Added `project/work_items/proposed/WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN.md`.
- Opened PR #877 from `xenotaur/spike/wi-claude-projects-session-export-design`.
- The duplication search found open PR #863 (`PROP-LRH-CLOUD-SESSION-CAPTURE`),
  which covers ordinary Claude Code cloud sessions. The item was narrowed,
  with the user's confirmation, to exclude that ground.
- The session that produced the item began in a different repository's
  checkout; the LRH checkout was added partway through.
- Evidence gathered in the session and recorded in the item: a linked-folder
  Project thread wrote an ordinary local transcript, and
  `lrh conversation export-claude-session --transcript-path` exported it
  with `inspect-export` reporting a matching source hash. No transcript text
  was printed or committed.

# Validation

- `lrh validate`: 0 errors, 1 warning. The warning (`OWNER_NOT_IN_CONTRIBUTORS`)
  is on the existing `WI-LRH-DURABLE-MANUAL-RUN-STATE`, not on this item.
- `lrh work-items readiness WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN`:
  `prompt_ready: yes`, no blockers, no warnings.
- `lrh prompt check-execution --slug wi-claude-projects-session-export-design`:
  no prior execution record.
- Commands were run as `PYTHONPATH=src python3 -m lrh.cli.main` from the
  checkout, because the installed `lrh` points at a different, older checkout.

# Follow-up

- No workstream was identified for this item, so no workstream update was
  offered.
- If PR #863 changes materially before it merges, recheck the boundary
  between it and this item.
- A separate question raised in the session, whether to run Projects on a
  dedicated always-on machine, is out of scope here and has no artifact.
