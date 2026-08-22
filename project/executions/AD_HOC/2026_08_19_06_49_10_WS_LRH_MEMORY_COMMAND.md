---
execution_id: 2026_08_19_06_49_10_WS_LRH_MEMORY_COMMAND
prompt_id: PROMPT(AD_HOC:WS_LRH_MEMORY_COMMAND)[2026-08-19T04:34:31+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/565
commit: b733e3ef75eda6d7a41ff51dcc5f5f4dff20a960
created_at: 2026-08-19T06:49:10+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-memory-command/00_proposal.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Drafted `WS-LRH-MEMORY-COMMAND` (planning node) and all four of its work
items in one combined PR, carrying `PROP-LRH-MEMORY-COMMAND` (merged in
PR #563) from design into staged implementation scope.

# Result

Created five files, all `status: proposed`:
- `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md` — groups the
  four work items below, `stage: planned`, exit criteria mirroring each
  WI's resolution plus the backlog-entry close/link and proposal adoption.
- `project/work_items/proposed/WI-LRH-MEMORY-WRITE-SIDE.md` — write/list/
  validate/repair, the `metadata.authored_by`/`applies_to` schema with
  its malformed/legacy grandfathering split, the memory-file-before-index
  write ordering, atomic-write helper extraction, and the `lrh-closeout`
  migration. `depends_on: []`.
- `project/work_items/proposed/WI-LRH-MEMORY-ARCHIVE-SIDE.md` —
  `lrh memory sync` with snapshot-before-overwrite mirroring, generalizing
  `mirror_transcript`. `depends_on: [WI-LRH-MEMORY-WRITE-SIDE]` (shares
  the extracted atomic-write helper).
- `project/work_items/proposed/WI-LRH-MEMORY-READ-SIDE.md` — `read`/
  `search`, reusing `lrh search`'s deterministic-substring design.
  `depends_on: []` — no new schema or write path required, per the
  proposal's own Implementation Plan text.
- `project/work_items/proposed/WI-LRH-MEMORY-PORTABILITY.md` —
  `export`/`import`/`transfer`. `depends_on: [WI-LRH-MEMORY-WRITE-SIDE]`
  (needs `write`'s validation path for `import`'s per-record checks); body
  carries forward the proposal's two unresolved Open Questions
  (default-selection policy, bundle format) rather than guessing answers.

Each work item's Problem/Context section runs its own prior-art check
(duplication + demand) against the current repo state, not just quoting
the proposal's — confirmed no existing workstream or work item duplicates
this scope, and each demand search correctly finds the same backlog entry
and governing proposal, with a shared offer to close/link the backlog
entry tracked once at the workstream level (not duplicated four times).

Pushed on branch `xenotaur/feat/ws-lrh-memory-command`, opened as PR #565.

# Validation

`lrh validate` — 0 errors, 0 warnings across all five files together
(the workstream's `work_items:` cross-references all resolve correctly
against the four newly-created WI files in the same commit).

# Follow-up

- WI-LRH-MEMORY-PORTABILITY's two Open Questions (default-selection
  policy, bundle format) should be resolved before that item is refined
  toward `lrh request ready-work-item`/`prompt-from-work-item`.
- Once PR #565 merges, offer to close/link `project/design/backlog.md`'s
  "lrh memory command" entry (demand-search verdict, all five artifacts).
- Address PR review feedback via `/lrh-review-response` and
  `/lrh-confirm-fixes` before merge, then `/lrh-closeout` after.
