---
execution_id: 2026_09_28_08_01_48_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS)[2026-09-28T06:37:08+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/753
commit: 
created_at: 2026-09-28T08:01:48+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS.md
session_transcript: pending
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
  non-test caller (`grep -rn "record_fingerprints(" src`). Its only use is the
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
- `tests/gate_staleness_test.py -k "fingerprint or unresolvable"`: 5 passed.
  This was run during the assessment, to confirm the existing fail-closed
  reproduction.

# Follow-up

- Implement the work item via `/lrh-execute WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS`
  or `/lrh-implement`.
- Adding the WI to `WS-INVOCATION-AND-GATE-RESET`'s `work_items:` list was
  offered at creation and is awaiting the user's decision.
- Deferred by design: gate-text snapshots for "show what changed", and
  marker-scoped fingerprinting.
