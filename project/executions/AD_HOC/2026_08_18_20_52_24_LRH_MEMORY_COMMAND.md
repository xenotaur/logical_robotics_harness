---
execution_id: 2026_08_18_20_52_24_LRH_MEMORY_COMMAND
prompt_id: PROMPT(AD_HOC:LRH_MEMORY_COMMAND)[2026-08-18T20:48:53+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-08-18T20:52:24+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-memory-command/00_proposal.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Wrote `PROP-LRH-MEMORY-COMMAND`, a design proposal covering two independent
gaps identified during the `experimental/rescue_claude_sessions/` migration:
(1) agents write malformed, unindexed, or wrong-path Claude Code memory
files with no validation, and (2) `lrh sessions sync` archives zero memory
files, leaving the corpus single-copy outside a durable archive. Preceded
by an `/lrh-design` session that ran the prior-art check, surveyed the
existing `lrh sessions`/`prompt_workflow_sessions.py` precedent, and
produced the high/low-level design this proposal formalizes.

# Result

Created `project/design/proposals/proposed/lrh-memory-command/00_proposal.md`
(status: proposed, implementation_status: not_started). The proposal
defines an `lrh memory write`/`list`/`validate` write-side surface (new
`authored_by`/`applies_to` frontmatter fields, reusing the existing
`project_slug_for_path()` helper from `prompt_workflow_sessions.py:515`)
and an independent `lrh memory sync` archive-side command using a
snapshot-before-overwrite mirroring invariant — deliberately not reusing
`mirror_transcript`'s never-shrink invariant, since memory files are
legitimately edited/shrunk (e.g. by the `consolidate-memory` skill) unlike
append-only transcripts. Per explicit user instruction, the proposal is
committed locally only — no PR opened yet, pending further design
discussion to resolve the Open Questions section (MCP-tool delivery,
enforcement vs. convention, `authored_by` provenance, archive retention
strategy, and possible broader scope beyond this one corpus).

# Validation

`lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Resolve the proposal's Open Questions before drafting work items.
- Once scope is settled, draft WI-A (write-side) and WI-B (archive-side)
  per the Implementation Plan section, and offer to close/link the
  `project/design/backlog.md` entry this proposal answers.
- Open a PR for this proposal when the user is ready to proceed (held back
  intentionally this session).
