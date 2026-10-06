---
execution_id: 2026_09_28_08_01_48_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS)[2026-09-28T06:37:08+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/753
commit: 6aec589a9b9a942cc1f8812ca9e28282e12d848b
created_at: 2026-09-28T08:01:48+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS.md
session_transcript: claude-app:708f8a5c-20da-4910-bafb-fdecde18e51e
---

# Summary

Created work item `WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS` via `/lrh-work-item`.
The work item was seeded by a suggestion from another session about the
chain-defaults fingerprint persistence gap, which was observed in the LCATS
project. This session first ran a read-only assessment of that suggestion, then
a `/lrh-design` pass. The work item captures the resulting design: an explicit,
separately confirmed `lrh chain-defaults record-fingerprints` action offered by
`/lrh-config-gates`, with clone-local storage in the git common dir.

# Result

- Wrote `project/work_items/proposed/WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS.md`
  (`status: proposed`, `WS-INVOCATION-AND-GATE-RESET`).
- Opened PR #753.
- The assessment confirmed that `gate_staleness.record_fingerprints()` has no
  non-test caller: `git grep -n "record_fingerprints(" -- src` matches only
  its definition at `src/lrh/gate_staleness.py:469`. Wiring it in is the
  deferred follow-up named in
  `WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT`'s resolution.
- The assessment also found a latent bug: unresolved targets make
  `record_fingerprints` write `{}` successfully.
- The seeding suggestion cited `_shared/chain-defaults.md:113-128`. That
  citation was inaccurate: the file never mentions fingerprints.

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings. It
  was run against the worktree source because the installed `lrh` points at a
  different checkout.
- `lrh prompt check-execution --slug wi-chain-defaults-record-fingerprints --work-item AD_HOC`:
  no prior record.
- `scripts/test tests/gate_staleness_test.py`: 31 tests, OK. This includes
  `test_untracked_target_missing_fingerprint_fails_closed` and
  `test_unresolvable_target_fails_closed`, which reproduce the existing
  fail-closed behaviour. The first assessment ran a pytest `-k` selection;
  it was rerun with the canonical runner during PR #753 review.

# Follow-up

- The design was revised during PR #753 review (see the `_REVIEW` record).
  Codex P1 was accepted: fingerprint recording now happens only as part of
  a `confirmed_commit` re-stamp, through `lrh chain-defaults restamp`, and
  `/lrh-config-gates` becomes a second sanctioned re-stamp point. It is no
  longer a standalone record action.

- Implement the work item via `/lrh-execute WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS`
  or `/lrh-implement`.
- Adding the WI to `WS-INVOCATION-AND-GATE-RESET`'s `work_items:` list was
  offered at creation and is awaiting the user's decision.
- Deferred by design: gate-text snapshots for "show what changed", and
  marker-scoped fingerprinting.
