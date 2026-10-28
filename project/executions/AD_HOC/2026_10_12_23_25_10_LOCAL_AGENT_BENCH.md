---
execution_id: 2026_10_12_23_25_10_LOCAL_AGENT_BENCH
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_BENCH)[2026-10-12T23:04:20+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/837
commit:
created_at: 2026-10-12T23:25:10+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/local-agent-bench/00_proposal.md
session_transcript: pending
---

# Summary

Created design proposal PROP-LOCAL-AGENT-BENCH via /lrh-proposal, following the /lrh-design pass in this session on turning LRH Console into a project browser with local-model toy access and follow-up chat. The owner chose to capture the toy and chat part as a new, design-only proposal rather than amend PROP-LOCAL-AGENT-DOGFOOD while WI-LOCAL-AGENT-001's evidence is being collected.

# Result

- Wrote `project/design/proposals/proposed/local-agent-bench/00_proposal.md` (status proposed, implementation_status not_started).
- Opened PR #837. Companion work item: PR #836 (WI-LRH-CONSOLE-WORK-ITEM-BROWSER).
- Did not touch `experimental/local_agent/`, WI-LOCAL-AGENT-001, WS-LOCAL-AGENT-DOGFOOD, or PROP-LOCAL-AGENT-DOGFOOD.

# Validation

- `lrh validate`: 0 errors, 0 warnings. It was run in the per-worktree conda env `LrhConsoleBrowser`, which is bound to this worktree.
- Re-verified the cited claims against origin/main 9178953e: the serve.py line ranges, the desktop-server-protocol auth and Host notes, the console proposal's lines 218 and 222-223, the 64 KiB `MAX_MESSAGE_BYTES`, the `brief_v2` prompt version, and the `ModelRequest` single-prompt shape.

# Follow-up

- Implementation is gated on the owner's next proceed decision on WI-LOCAL-AGENT-001. No bench work item yet.
- Open questions are listed in the proposal: `ask` support, how the console learns the bench URL, ratings, and context budget.
- Update `session_transcript` to the `claude-app:` pointer at closeout.
