---
execution_id: 2026_09_22_06_47_35_WI_LRH_CLOSEOUT_PR_VERIFIER
prompt_id: PROMPT(WI-LRH-CLOSEOUT-PR-VERIFIER:WI_LRH_CLOSEOUT_PR_VERIFIER)[2026-09-22T06:15:01+00:00]
work_item: WI-LRH-CLOSEOUT-PR-VERIFIER
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/710
commit: 
created_at: 2026-09-22T06:47:35+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CLOSEOUT-PR-VERIFIER.md
session_transcript: pending
---

# Summary

Implemented `WI-LRH-CLOSEOUT-PR-VERIFIER` via `/lrh-execute`: a read-only,
gate-owned `lrh closeout verify-pr <pr-url>` command that decides whether a
`/lrh-land` closeout PR conforms to the plan a human approved at Step 6.

# Result

Added `src/lrh/closeout_pr_verifier.py` (pure conformance predicates plus a
thin I/O wrapper), `tests/closeout_pr_verifier_test.py`, and CLI wiring in
`src/lrh/cli/main.py`, matching the existing `chain-defaults check-staleness`
/ `confirm-fixes check-batch-routine` pattern. Opened PR #710.

A proactive `/lrh-self-review` diff-mode pass (Step 7.5) before the first
push found and I independently re-verified two real gate-integrity gaps in
the first draft:

1. The `commit`-field placeholder-fill exception accepted any new commit
   value when the plan didn't separately name one, rather than requiring the
   caller to state the actual merge SHA. Fixed by adding an explicit
   `expected_commit` parameter (and CLI `--expected-commit` flag) that the
   exception now checks against.
2. The chain-defaults check compared parsed YAML fields, not raw text lines
   -- directly contradicting the work item's own Risk Notes ("must be
   line-level, because that file's blob hash binds stored skip-consent").
   Rewrote it as `check_chain_defaults_lines`, a raw-text sequence diff that
   flags any changed line other than the two allowed re-stamp fields'
   assignment lines, including a comment-only or whitespace-only edit.

Both fixes were applied before the first push, per Decision 4 ("this pass
never skips or replaces the PR's first real bot round").

# Validation

- 50 hermetic `unittest` tests, covering the pure predicates and the CLI's
  hermetic early-error paths (plan-file read/parse failures).
- Manual end-to-end smoke test against the real, merged PR #691: correctly
  reported conformance on allowed paths, the chain-defaults restriction, and
  execution-record fields (with `--expected-commit` supplied); correctly
  flagged the one expected divergence (`mergeable: UNKNOWN` on an
  already-merged PR).
- `scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`,
  `scripts/test`: all clean.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `WI-LRH-LAND-WORDING-AND-CLOSEOUT-PR` (which depends on this WI) wires this
  command into `/lrh-land` Step 6/7.
- `session_transcript` is `pending` until a durable pointer is available.
