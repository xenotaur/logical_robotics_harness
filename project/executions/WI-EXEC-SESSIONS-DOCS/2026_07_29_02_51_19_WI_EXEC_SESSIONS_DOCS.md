---
execution_id: 2026_07_29_02_51_19_WI_EXEC_SESSIONS_DOCS
prompt_id: PROMPT(WI-EXEC-SESSIONS-DOCS:WI_EXEC_SESSIONS_DOCS)[2026-07-29T02:46:14-04:00]
work_item: WI-EXEC-SESSIONS-DOCS
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/432
commit: c7f41e1
created_at: 2026-07-29T02:51:19-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXEC-SESSIONS-DOCS.md
session_transcript: claude-app:f1e9c968-f61d-4618-979c-29f8b08bfb0c
---

# Summary

Implement WI-EXEC-SESSIONS-DOCS — the last open piece of
PROP-LRH-EXECUTION-SESSIONS. Docs-only.

# Result

Investigated first: the WI's `project/executions/README.md` acceptance
criterion was already satisfied by PR #411 (full field grammar, `none`/
`pending` sentinels). `PROMPTS.md` had zero mentions — the genuinely open
half.

Added a `## Claude.app execution sessions` section to `PROMPTS.md` (between
"Execution record format" and "Rerun, revert, and supersession handling"):

- Three-phase model (design → instruction → execution), copied faithfully
  from `project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md`
  §"Design" rather than paraphrased from memory.
- Instruction-phase workflow for Claude.app (`lrh prompt label`,
  `lrh prompt check-execution`), pointing to the existing "Installed CLI
  commands (preferred)" section instead of re-deriving flags — verified
  against real `--help` output.
- Three optional fields summarized, with `project/executions/README.md`
  named canonical for their grammar (avoids a second copy that goes stale
  independently — the same staleness `WI-EXEC-SESSIONS-SCHEMA` had before
  its own refresh).
- `pending` → `claude-app:<host-uuid-stem>` pattern, noting `/lrh-closeout`
  now automates this (PR #431).

Self-caught two accuracy slips before commit: a decision-log entry title
quoted imprecisely, and a "see above" reference to a section that actually
follows (fixed to "below").

Branch used an `-impl` suffix to avoid colliding with the already-merged
`/lrh-work-item` branch name for this WI.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS`)
- `grep -n "agent\|session_transcript\|instruction_source" project/executions/README.md`
  — 6 matches
- `grep -ni "three.phase\|claude.app\|claude_app" PROMPTS.md` — 11 matches
- `scripts/format --check` / `scripts/lint` — clean

# Follow-up

- WI stays `proposed` until this PR merges and closeout resolves it.
- This closes the documentation half of `PROP-LRH-EXECUTION-SESSIONS`;
  Stages 1 (docs, this PR) and 2 (validator, PR #421) are now both done.
