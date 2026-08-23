---
execution_id: 2026_08_23_17_57_00_LRH_CHAIN_DEFAULTS_INCREMENT_3_REVIEW
prompt_id: PROMPT(WI-LRH-CHAIN-DEFAULTS-INCREMENT-3:LRH_CHAIN_DEFAULTS_INCREMENT_3_REVIEW)[2026-08-23T17:56:54+00:00]
work_item: WI-LRH-CHAIN-DEFAULTS-INCREMENT-3
status: in_progress
rerun_of: 2026_08_23_17_37_32_LRH_CHAIN_DEFAULTS_INCREMENT_3
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/623
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/623
commit: 
created_at: 2026-08-23T17:57:00+00:00
---

# Summary

Review-response round for PR #623 (`/lrh-land` Step 4, inlining
`/lrh-review-response`). Six comments: four from
`copilot-pull-request-reviewer`, two P1 from `chatgpt-codex-connector`.

# Result

All six valid, all fixed:

1. `_show_file_at()` misclassified an invalid `confirmed_commit` (a bad git
   error) as "file added since confirmation" rather than failing the check.
   Fixed: `check_gate_staleness` now validates `confirmed_commit` up front
   via `git rev-parse --verify <commit>^{commit}`, which raises
   `GateStalenessError` (exit 2) for an unresolvable commit before any
   per-file `_show_file_at` call can misread the failure. Regression test
   added (`test_invalid_confirmed_commit_raises_not_stale`).
2. + 2 (duplicate report): the skill-text doc said exit status `2` covers
   "added/removed watched file," but the implementation treats that case as
   `stale: true` (exit `1`) -- a real doc/implementation mismatch. Fixed:
   corrected the doc text in both `_shared/chain-defaults.md` and
   `lrh-land/references/land-workflow.md` to state that an added/removed
   watched file is a stale *result* (exit 1), and exit 2 is reserved for
   the check itself failing to run at all.
3. `--format json` printed errors to stdout, which breaks machine parsing
   of the JSON output on the error path. Fixed: routed to `sys.stderr` in
   `src/lrh/cli/main.py`'s dispatch.
4. **P1, most serious finding.** The merge-reply classifier treated any
   generic merge-affirmative reply ("merge it," "approved," "yes") as also
   authorizing an offered WS closeout, bypassing `/lrh-closeout`'s own
   requirement that the exit-criteria question get its own explicit `y`.
   Fixed: `/lrh-land` Step 6 now requires the reply to affirm the
   exit-criteria question in a way that cannot be read as answering the
   merge question alone before WS closeout (or a dependent proposal
   adoption) executes; a bare merge-affirmative reply still executes the
   merge and the closeout plan's non-branching parts, but withholds WS
   closeout and reports it as an unconfirmed offer rather than silently
   granting it. Step 7's re-derivation logic updated to match (does not
   execute WS closeout Step 6 withheld, even if the real state would
   otherwise allow it).
5. **P1.** The closeout preview omitted each execution record's resolved
   `session_transcript` value, so the no-divergence satisfaction path
   could commit those values without their ever having appeared in the
   approved payload -- the exact provenance gap `/lrh-closeout` Step 4's
   own "enumerated by execution ID, not a single summary value" rule
   exists to close. Fixed: Step 6's presented summary now lists every
   record's transcript value explicitly, and a differing value at Step 7
   is added to the materiality list (fires a fresh live ask, not silently
   absorbed).

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `tests/gate_staleness_test.py`: 20/20 passing (19 prior + 1 new
  regression test for finding 1).
- `tests/cli_tests/`: 304/304 passing.
- Mirror parity re-verified: `diff -r` clean for `lrh-land` between
  `src/lrh/skills/` and `.claude/skills/`; `land-workflow.md` byte-identical
  across `src/`, `.claude/`, `.agents/`, `.gemini/`; canonical/inlined
  shared-section parity between `_shared/chain-defaults.md` and
  `lrh-land/references/land-workflow.md` re-confirmed after the doc fixes.

# Follow-up

None -- proceeding to `/lrh-confirm-fixes`.
