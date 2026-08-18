---
execution_id: 2026_08_18_20_52_24_LRH_MEMORY_COMMAND
prompt_id: PROMPT(AD_HOC:LRH_MEMORY_COMMAND)[2026-08-18T20:48:53+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/563
commit: 79ce5d259bd4d95a524ada9448ec6247f6aa2edc
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
(status: proposed, implementation_status: not_started), then expanded it in
a second pass on the same PR. The proposal now specifies a full nine-command
`lrh memory` surface: `write`/`list`/`validate` (write-side, new
`authored_by`/`applies_to` frontmatter fields, reusing the existing
`project_slug_for_path()` helper from `prompt_workflow_sessions.py:515`),
`sync` (archive-side, snapshot-before-overwrite mirroring — deliberately
not reusing `mirror_transcript`'s never-shrink invariant, since memory
files are legitimately edited/shrunk by things like the
`consolidate-memory` skill), `read`/`search` (read-side, following the
existing `lrh search` deterministic-substring precedent rather than
semantic ranking), and `export`/`import`/`transfer` (portability, following
the existing `sessions sync --exports-dir` precedent). The portability
surface was added after empirically confirming, against live
`~/.claude/projects/` state, that fresh workstream subdirectories and git
worktrees (including this session's own worktree) get wholly separate,
empty memory corpora by construction — the concrete gap `export`/`import`/
`transfer` close. Design Decision 8 evaluates and rejects a symlink-based
alternative as disqualified (collides with the 200-line `MEMORY.md`
truncation ceiling and with `authored_by`/`applies_to` scoping), and defers
automatic transfer-on-bucket-creation as a follow-on question rather than
committing to it here. Added a `## API Sketch` section specifying concrete
CLI flags for all nine commands, citing precedent flag conventions from
`lrh sessions`/`lrh search` for each. Implementation is staged by risk
across four stages in the Implementation Plan; v1 need not implement all
nine commands at once. Per explicit user instruction, the proposal was
first committed locally only, then — after this expansion — pushed on a
fresh `xenotaur/feat/lrh-memory-command` branch with a PR opened for
review.

# Validation

`lrh validate` — 0 errors, 0 warnings (both after the initial write and
after the expansion).

# Follow-up

- Resolve the proposal's Open Questions before drafting work items,
  including the newly added automatic-transfer trigger point,
  default-selection policy for `transfer`, and export bundle format.
- Once scope is settled, draft the four staged work items (WI-A write-side,
  WI-B archive-side, WI-C read-side, WI-D portability) per the
  Implementation Plan section, and offer to close/link the
  `project/design/backlog.md` entry this proposal answers.
- Address PR review feedback via `/lrh-review-response` and
  `/lrh-confirm-fixes` before merge, then `/lrh-closeout` after.
