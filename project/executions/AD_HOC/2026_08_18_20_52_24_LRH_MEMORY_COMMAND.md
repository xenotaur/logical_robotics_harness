---
execution_id: 2026_08_18_20_52_24_LRH_MEMORY_COMMAND
prompt_id: PROMPT(AD_HOC:LRH_MEMORY_COMMAND)[2026-08-18T20:48:53+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/563
commit: 1f4eb7bca5f8bcc40dfa12038336d65d335359dd
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
(status: proposed, implementation_status: not_started), then expanded it
across two further passes on the same PR. The proposal now specifies a
full ten-command `lrh memory` surface: `write`/`list`/`validate`
(write-side, new `authored_by`/`applies_to` frontmatter fields, reusing
the existing `project_slug_for_path()` helper from
`prompt_workflow_sessions.py:515`), `sync` (archive-side,
snapshot-before-overwrite mirroring — deliberately not reusing
`mirror_transcript`'s never-shrink invariant, since memory files are
legitimately edited/shrunk by things like the `consolidate-memory`
skill), `read`/`search` (read-side, following the existing `lrh search`
deterministic-substring precedent rather than semantic ranking),
`export`/`import`/`transfer` (portability, following the existing
`sessions sync --exports-dir` precedent), and `repair` (Decision 9,
retroactive structural fix-up for memories already on disk, modeled on
`lrh work-items/workstreams/design organize`'s existing "conservatively
repair" pattern, preserving the original `authored_by` unless explicitly
overridden). The portability surface was added after empirically
confirming, against live `~/.claude/projects/` state, that fresh
workstream subdirectories and git worktrees (including this session's own
worktree) get wholly separate, empty memory corpora by construction — the
concrete gap `export`/`import`/`transfer` close. Design Decision 8
evaluates and rejects a symlink-based alternative as disqualified
(collides with the 200-line `MEMORY.md` truncation ceiling and with
`authored_by`/`applies_to` scoping), and defers automatic
transfer-on-bucket-creation as a follow-on question rather than committing
to it here. `repair` was added last, after which the Non-Goals section's
original "retroactive cleanup is entirely out of scope" line had to be
revised to reflect that `repair` now supplies the tool for it (cleanup
execution itself remains out of scope). Added a `## API Sketch` section
specifying concrete CLI flags for all ten commands, citing precedent flag
conventions from `lrh sessions`/`lrh search`/`lrh work-items organize` for
each. Implementation is staged by risk across the Implementation Plan,
with `repair` explicitly marked a fast follow-up to the write-side stage
rather than a blocking dependency; v1 need not implement all ten commands
at once. Per explicit user instruction, the proposal was first committed
locally only, then pushed on a fresh `xenotaur/feat/lrh-memory-command`
branch with a PR opened for review, then amended twice more on that same
PR (the full read/search/export/import/transfer expansion, then the
`repair` addition) before proceeding to `/lrh-land`.

# Validation

`lrh validate` — 0 errors, 0 warnings, after each of the three commits
(initial proposal, expansion, `repair` addition).

# Follow-up

- Resolve the proposal's Open Questions before drafting work items,
  including the automatic-transfer trigger point, default-selection
  policy for `transfer`, and export bundle format.
- Once scope is settled, draft the staged work items (WI-A write-side plus
  its `repair` fast follow-up, WI-B archive-side, WI-C read-side, WI-D
  portability) per the Implementation Plan section, and offer to
  close/link the `project/design/backlog.md` entry this proposal answers.
- Address PR review feedback via `/lrh-review-response` and
  `/lrh-confirm-fixes` before merge, then `/lrh-closeout` after.
