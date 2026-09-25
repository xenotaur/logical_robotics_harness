---
execution_id: 2026_09_24_21_32_22_LRH_EXPORT_SESSION_ID_SKILL_FAMILIES
prompt_id: PROMPT(AD_HOC:LRH_EXPORT_SESSION_ID_SKILL_FAMILIES)[2026-09-24T21:21:30+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/722
commit: 
created_at: 2026-09-24T21:32:22+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
session_transcript: claude-app:763ebf42-1a3c-4186-bf9f-baf6ba1dd72f
---

# Summary

Ran `/lrh-proposal` to capture a design for unifying LRH's transcript-export
and session-identity skills under one `lrh-<verb>-<vendor>` naming scheme. The
scheme has two dispatcher skills, `/lrh-export` and `/lrh-session-id`. This run
followed an audit, in the same session, of the shipped exporter and
session-pointer skills and of the planning artifacts, open PRs and Claude
sessions touching them.

# Result

- Wrote
  `project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md`
  (`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`, `status: proposed`,
  `implementation_status: not_started`).
- Six decisions: verb-first naming; delegating dispatchers that detect the
  vendor from an argument, then the environment, then by asking; renames of
  `lrh-codex-export`, `lrh-antigravity-export` and `lrh-codex-session`, with
  deprecated stubs; CLI names left unchanged; an Antigravity session-ID
  investigation before any resolver; installation to every target.
- The user chose the deprecated-stub, leave-CLI-as-is and
  Antigravity-investigate-first options at the interview step.
- Research findings recorded in the proposal:
  - The export manifest already supports all three `source_tool` values, so
    the backlog's Codex-only blocker is stale.
  - The skills installer never removes a skill folder once its source is
    gone, which is why the old names become stubs rather than disappearing.
  - `lrh-antigravity-export` is the only canonical skill missing from
    `.gemini/plugins/lrh/skills/`.
  - Antigravity has no `session_transcript:` pointer format and no known
    environment variable exposing the current conversation ID.
- The companion workstream and work items are added to the same branch and PR
  at the user's request.

# Validation

- `lrh prompt check-execution --slug lrh-export-session-id-skill-families --work-item AD_HOC`:
  no prior record.
- `lrh validate` (worktree source via `PYTHONPATH=src`): 0 errors, 0 warnings
  after writing the proposal.

# Follow-up

- `WS-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` and its work items (same PR).
- Once this lands, send a handoff to the "LRH session-sync/export ecosystem
  audit" session: `WI-SKILLS-LRH-CLAUDE-SESSION` now targets
  `lrh-session-id-claude`.
- Open questions in the proposal: when to remove the stubs, what to do with
  PR #542, and how the dispatcher handles a session that matches two vendors.
