---
execution_id: 2026_08_01_12_28_08_OUTDATED_THREAD_RECOVERY
prompt_id: PROMPT(AD_HOC:OUTDATED_THREAD_RECOVERY)[2026-08-01T12:20:46-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/457
commit: 041f0897cc14fd4b2df11b6c876f15dec2fb1261
created_at: 2026-08-01T12:28:08-04:00
agent: claude_app
instruction_source: project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Creates PROP-OUTDATED-THREAD-RECOVERY, the design proposal for the
outdated-thread recovery mechanism deferred from PR #453's landing (see
`project/design/backlog.md`). Follows directly from an `/lrh-design`
session on the same topic in this session.

# Result

Wrote `project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md`
with five design decisions: (1) `--include-thread <id>` over a broader
`--thread-state` override, for precision; (2) the recovery path is
always live-human-gated, never automatic, after PR #453's P1 governance
finding; (3) only Unaddressed/Partial/Problematic-resolution buckets are
ever eligible, as a hard rule; (4) the recovery fix routes through
`/lrh-review-response`'s full protocol including its own feasibility
check; (5) same-run idempotence is owned by `/lrh-review-response`
Step 3 itself, not patched around from the caller.

At the user's explicit direction, this proposal and its two companion
work items (WI-A mechanical, WI-B skill-flow) are being authored
together on one branch as a single set of planning-artifact changes, and
the PR is held pending a related discussion before being opened.

# Validation

lrh validate — 0 errors, 1 pre-existing unrelated warning
(`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- File WI-A and WI-B on this same branch.
- Populate `pr:`/`commit:` once the branch is pushed and the PR opened.
- Update `session_transcript` to the final host session id if it differs
  after the session ends.
