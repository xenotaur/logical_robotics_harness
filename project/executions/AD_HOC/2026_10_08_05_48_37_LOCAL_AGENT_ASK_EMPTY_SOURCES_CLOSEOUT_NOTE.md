---
execution_id: 2026_10_08_05_48_37_LOCAL_AGENT_ASK_EMPTY_SOURCES_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ASK_EMPTY_SOURCES_CLOSEOUT_NOTE)[2026-10-08T05:48:37+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_08_04_57_07_LOCAL_AGENT_ASK_EMPTY_SOURCES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/788
commit: f95464c38e0a9a6961e7567d6afd4c7034fa63f9
created_at: 2026-10-08T05:48:37+00:00
agent: claude_app
instruction_source: lrh-land Step 7 closeout for PR 788; owner approved merge and closeout in one reply
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Closeout note for PR #788, which fixes the owner-reported T0 `ask` bug where
the model was called with no usable source. The primary record body is
immutable, so the chain note lives here.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[chain-auth, review-disposition, merge+closeout]; friction=none; note="one Codex P2 (refused-run provenance) fixed; substitute review clean"`

- **Merge:** `f95464c38e0a9a6961e7567d6afd4c7034fa63f9`, using
  `--match-head-commit f1078d8f92d86ad1858b522ca164cf72648ed79f`. CI was
  green (5/5).
- **Deferred, named at the merge gate:**
  1. Only the no-sources refusal asserts the recorded context fields; the
     declined and adapter-error refusals do not.
  2. Overview mode is sendable even with no README and an empty listing.
  3. "sending N of M" counts unique `--files` paths.
- **WI-LOCAL-AGENT-001 stays active.**

# Validation

- `lrh validate` was run after the closeout edits.

# Follow-up

- A control-plane PR: the (c1) `--allow-flagged` amendment to Decision 3 and
  WI-LOCAL-AGENT-001, plus a (c3) work item for the shared scanner's
  type-annotation false positive.
- Then the (c1) implementation PR.
