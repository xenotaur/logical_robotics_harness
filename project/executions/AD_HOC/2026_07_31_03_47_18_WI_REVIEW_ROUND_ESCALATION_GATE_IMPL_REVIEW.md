---
execution_id: 2026_07_31_03_47_18_WI_REVIEW_ROUND_ESCALATION_GATE_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_REVIEW_ROUND_ESCALATION_GATE_IMPL_REVIEW)[2026-07-31T03:46:54-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_31_03_25_45_WI_REVIEW_ROUND_ESCALATION_GATE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/445
commit: eac6284537435bd252fed48f5965263b7a5eeac7
created_at: 2026-07-31T03:47:18-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/445
session_transcript: claude-app:b1f7a963-e611-4bcd-9d8c-a6a80d633a47
---

# Summary

Address PR #445's first review round: 2 P2 comments from Codex, both real
gaps in the round-cap state design (not the planning WI this time — the
actual implementation).

# Result

Both valid and fixed:

- **"Preserve reviewer progress until the whole batch settles":**
  confirmed the original design cleared `pending_attempt` entirely on the
  first confirmed submission, losing track of any other reviewer in the
  same batch whose call failed/timed out/was interrupted — a later
  invocation had no way to know that reviewer's mention was still
  outstanding, either dropping it forever or miscounting a resumed
  mention as a new batch. Redesigned `pending_attempt` to track each
  reviewer's status individually (`pending`/`submitted`/`failed`),
  promoting `completed_count` exactly once (on the first submission) but
  keeping the marker open until every reviewer in the batch has a
  terminal status.
- **"Key round state by immutable PR identity":** confirmed the state
  file was keyed by branch-derived slug, which can collide across a
  reused branch name (post-merge) or two fork PRs sharing a head branch
  name. Rekeyed to `<owner>-<repo>-pr<N>.json` from the PR URL itself,
  plus a defensive check that a loaded file's `pr` field matches the
  target PR — stop and report on mismatch rather than guess.

Updated `SKILL.md` Step 8, `round-cap-gate.md`, and the
`project/executions/README.md` note consistently. Re-checked all
cross-references between the renumbered round-cap steps by hand before
pushing (this class of self-inflicted dangling-reference bug recurred
several times on the planning PR #444).

# Validation

- `lrh validate`: 0 errors, 1 pre-existing warning unrelated to this file.
- `scripts/format --check --diff`, `scripts/lint`: clean.
- `scripts/test`: 808 tests, OK.
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`: no differences.
- Pushed directly to the open PR branch.

# Follow-up

- `/lrh-confirm-fixes` should run next to verify and resolve these
  threads.
- `session_transcript: pending` should be updated once resolvable.
