---
execution_id: 2026_06_23_18_17_03_E_STRATEGY_EXECUTION_SESSIONS_DESIGN
prompt_id: PROMPT(AD_HOC:E_STRATEGY_EXECUTION_SESSIONS_DESIGN)[2026-06-23T18:02:58-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/317
commit: 8555593
created_at: 2026-06-23T18:17:03-04:00
agent: claude_app
session_transcript: claude-app:a31066c4-ea98-4663-b12d-97a08e4c3451
---

# Summary

Design the E-strategy execution session model as a formal LRH proposal.
The gap: Claude.app sessions are multi-turn conversations that produce PRs
but have no machine-readable reference in execution records. The preceding
session (PR #313) demonstrated the three-phase model (design → instruction →
execution) in practice; this session formalizes it.

# Result

PR #317 opened: https://github.com/xenotaur/logical_robotics_harness/pull/317

Proposal set created at
`project/design/proposals/proposed/lrh-execution-sessions/`:
- `README.md` — set index and reading order
- `00_proposal.md` — umbrella proposal (PROP-LRH-EXECUTION-SESSIONS)

Key design decisions:
- Three-phase model (design → instruction → execution) applies to all
  backends; Claude.app-driven sessions use an explicit restatement as
  the instruction-phase marker
- Three new optional execution-record fields: `agent`, `instruction_source`,
  `session_transcript` — backward-compatible; no validator changes required
  in Stage 1
- Session transcripts are observability artifacts (JSONL at
  `~/.claude/projects/<project-slug>/<session-id>.jsonl`), not control-plane
  artifacts; they reference rather than copy session content
- Taurcode meta-prompts belong in `src/lrh/skills/` for distribution once
  PROP-LRH-PROJECT-LOCAL-SKILLS ships; until then, user-local Taurcode is
  the valid resting place
- `lrh search executions "claude_app"` is sufficient for Stage 1 discovery;
  no new CLI command needed until Stage 3

Proposals README updated with index entry for the new proposal set.

# Validation

scripts/version tools  — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff  — 171 files unchanged
scripts/lint  — all checks passed
scripts/test  — 666 tests OK

# Follow-up

- Review and merge PR #317
- Update status to `landed` once merged
- Stage 1 work item: update `project/executions/README.md` and `PROMPTS.md`
  to document the three optional fields and the three-phase model
  (`WI-EXEC-SESSIONS-DOCS`)
- Update `session_transcript` from `pending` to `claude-app:<session-id>`
  once the session ID is known (look in `~/.claude/projects/` for the
  JSONL file from this session)
