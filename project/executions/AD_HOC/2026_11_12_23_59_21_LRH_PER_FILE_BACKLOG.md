---
execution_id: 2026_11_12_23_59_21_LRH_PER_FILE_BACKLOG
prompt_id: PROMPT(AD_HOC:LRH_PER_FILE_BACKLOG)[2026-11-12T05:59:14+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/868
commit: e0bdf699
created_at: 2026-11-12T23:59:21+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-per-file-backlog/00_proposal.md
session_transcript: claude-app:dbbdc478-f222-49ba-a42a-0b03587fdd69
---

# Summary

Create design proposal `PROP-LRH-PER-FILE-BACKLOG` via `/lrh-proposal`,
capturing a cross-repo assessment of backlog formats (LRH, Taurworks, LCATS,
prosoc) and recommending one Markdown file per backlog entry under
`project/backlog/{open,closed}/` with minimal frontmatter.

# Result

- Wrote `project/design/proposals/proposed/lrh-per-file-backlog/00_proposal.md`
  (`status: proposed`, `implementation_status: not_started`) with nine design
  decisions, non-goals, five open questions, and a four-stage implementation
  plan.
- Grounding gathered in-session: LRH `project/design/backlog.md` structure
  (46 heading entries, zero table rows, free-prose `**Status:**`); Taurworks,
  LCATS, and prosoc backlog files read from their default branches on GitHub
  (local checkouts were stale feature branches); LCATS duplicate entry
  (`backlog.md:178` / `:845`); Backlog.md (`MrLesk/Backlog.md`) task-file
  format as external prior art.
- Prior-art check: duplication search found no existing LRH backlog tooling
  (recommendation: proceed); demand search found no matching work item or
  proposal, with prosoc's in-flight `WI-CARD-AUDIT-BACKLOG-SYNC` noted for
  linking once it lands.
- Interview step answered from the preceding in-session assessment; the full
  draft was shown and confirmed by the user before writing.
- Opened PR #868.

# Validation

- `lrh prompt check-execution --slug lrh-per-file-backlog --work-item AD_HOC`:
  no prior record.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Review the proposal's open questions (location, `deferred` status,
  legacy-file fallback, migrating resolved entries, committed index).
- On adoption, create a workstream for the four implementation stages.
- Link prosoc `WI-CARD-AUDIT-BACKLOG-SYNC` when it lands.
