---
execution_id: 2026_09_23_01_19_46_WI_CLAUDE_EXPORT_MARKDOWN_USER_TURN_MISLABEL
prompt_id: PROMPT(AD_HOC:WI_CLAUDE_EXPORT_MARKDOWN_USER_TURN_MISLABEL)[2026-09-23T01:18:34+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/715
commit: 1991604fe298773fe4a03ea0b43c299400cdfbd7
created_at: 2026-09-23T01:19:46+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Created `WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL` via `/lrh-work-item`,
at the user's request, following up on an informal handoff from another
session that reviewed a real Claude export: `claude_export.py`'s Markdown
renderer gives a tool-execution-result reply the same `## User` heading
as a genuine human-typed message.

# Result

Wrote `project/work_items/proposed/WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL.md`
with full frontmatter and body. `type: deliverable`, `depends_on: []`,
`related_design` points at
`project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md`.

The handoff's core claim was independently verified directly against
`src/lrh/conversations/claude_export.py` before drafting the work item,
not taken on trust: `_render_claude_transcript()` calls
`_render_message_block("User", step)` unconditionally for every
`type == "user"` step (`claude_export.py:667-668`), while
`_is_genuine_human_turn()` (`claude_export.py:587-605`) — which correctly
distinguishes a genuine human turn from a tool-result delivery — is wired
only into the `turn_count` statistic (`_count_turns`,
`claude_export.py:608-616`), never into the render path. The tool-result
case renders `## User` followed by `### Tool Result`
(`claude_export.py:772-779`), visually identical in header shape to a
genuine human turn.

Also independently narrowed the scope beyond what the handoff speculated:
`turn_count`/`message_count` in `export_manifest.py` are unaffected
(already use `_is_genuine_human_turn` correctly); `export_inspector.py`
does not parse rendered headings (only splits YAML frontmatter from
body); no doc currently describes the Markdown header shape;
`antigravity_export.py` uses an already-disambiguated step-type scheme
and `codex_app_server_export.py` has no `## User` header at all — neither
sibling exporter shares this defect. All recorded in the WI's own
Problem/Context and Non-Goals.

Duplication search found no existing work item or proposal on this;
`WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER` and
`WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` (both resolved) touch
the same exporter but a different concern.

Opened https://github.com/xenotaur/logical_robotics_harness/pull/715, planning only, no implementation.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- This item is `prompt_ready` for `/lrh-implement` or `/lrh-execute` once
  the user wants it worked.
- Proceed to `/lrh-land` for PR #715 when ready.
