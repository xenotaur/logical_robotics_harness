---
execution_id: 2026_08_24_00_07_31_LRH_CHAIN_DEFAULTS_INCREMENT_2
prompt_id: PROMPT(WI-LRH-CHAIN-DEFAULTS-INCREMENT-2:LRH_CHAIN_DEFAULTS_INCREMENT_2)[2026-08-23T23:13:25+00:00]
work_item: WI-LRH-CHAIN-DEFAULTS-INCREMENT-2
status: in_progress
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-2.md
session_transcript: pending
pr: https://github.com/xenotaur/logical_robotics_harness/pull/626
commit: 
created_at: 2026-08-24T00:07:31+00:00
---

# Summary

Implements `confirm_fixes_batch`'s `auto_unless_unusual` per-gate autopilot
predicate for `/lrh-confirm-fixes`, per `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`.
Third of the planned 1-2-3 PR sequence begun by the earlier gate-policy
audit conversation: housekeeping (#609), Stage 3.5 activation (#618),
Increment 3 (#623), and now Increment 2 (#626).

# Result

## Evidence survey (Required Change #1)

Dispatched a research agent to survey real `/lrh-confirm-fixes` execution
records produced since `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1` shipped
(2026-08-07T19:02:48, PR #512). 95 `*_CONFIRM.md` records exist after that
timestamp; read a representative sample of 36, spread across the full date
range through 2026-08-23, including five read in full where triage flagged
something non-routine.

**Findings, independently spot-verified by direct `grep` against the cited
files before use (not accepted on the subagent's word alone):**

- Roughly 80% of real rounds were fully routine (empty-thread or all
  Clear-satisfied, Green verdict) -- even when P0/P1 badges were present.
  Severity alone did not predict an unusual round.
- Bot-vs-human reviewer identity was not a distinguishing signal in the
  sampled data -- every reviewer observed was a bot.
- What did predict "unusual": a non-Clear-satisfied thread bucket, CI
  already failing, or a prior round on the same PR that already surfaced a
  non-Clear-satisfied finding.
- A recurring, severity-independent near-miss: `lrh request review_response`
  reporting "Nothing to resolve" while the authoritative `isResolved ==
  false` check found genuinely open, outdated threads -- confirmed directly
  in PR #549's record (`project/executions/AD_HOC/2026_08_13_14_22_28_WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL_CONFIRM.md:28-31`).

**Specific citations** (file paths under `project/executions/`, PR numbers
from their `pr:` field):

Routine (safe to auto-proceed):
- `AD_HOC/2026_08_07_19_11_00_WI_LRH_CHAIN_DEFAULTS_INCREMENT_1_CONFIRM.md` -- PR #512
- `AD_HOC/2026_08_14_02_20_56_FIX_GET_PULL_COMMENTS_PAGE_FLATTEN_CONFIRM.md` -- PR #555
- `AD_HOC/2026_08_20_22_16_28_WI_LRH_MEMORY_WRITE_SIDE_CONFIRM.md` -- PR #570 (8 threads, 3 P1, all Clear-satisfied, Green)
- `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3/2026_08_23_18_20_47_LRH_CHAIN_DEFAULTS_INCREMENT_3_CONFIRM.md` -- PR #623

Near-miss / tool-undercount (why `--bucket` must derive from the
authoritative list, never `lrh request review_response`'s filter):
- `AD_HOC/2026_08_13_14_22_28_WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL_CONFIRM.md` -- PR #549
- `AD_HOC/2026_08_21_06_41_52_WI_GATE_POLICY_CASCADE_STAGE3_CONFIRM.md` -- PR #577
- `AD_HOC/2026_08_22_04_50_29_LRH_MEMORY_CLI_AUDIT_CONFIRM.md` -- PR #598

Genuinely unusual (why the prior-round-exception condition exists):
- `AD_HOC/2026_08_10_00_07_15_SELF_REVIEW_COMMAND_PREFS_68C9F9_CONFIRM.md` -- PR #535, 3 verification rounds, explicit "not a Green verdict by the skill's own definition"
- `AD_HOC/2026_08_10_07_01_20_FRONT_OF_RUN_GATE_COLLAPSE_WI_CONFIRM.md` -- PR #536, same stale-bot-review-vs-HEAD class
- `AD_HOC/2026_08_11_00_55_07_RETRIGGER_REMOVAL_STAGE1_WI_CONFIRM.md` -- PR #541, non-thread finding classified Partial
- `AD_HOC/2026_08_08_04_56_02_DISABLE_MODEL_INVOCATION_REGRESSION_82CAD9_CONFIRM.md` -- PR #518, 4-round escalation

## Implementation

`src/lrh/confirm_fixes_batch.py`: pure predicate `is_routine_batch`,
gate-owned per `PROP-LRH-CHAIN-DEFAULTS` Decision 2. Routine iff: no
prior-round exception on this PR (checked first, per the escalation
evidence above), CI not failing, and every unresolved thread classifies
Clear-satisfied (or the batch is empty). `lrh confirm-fixes
check-batch-routine` CLI wires it in. Wired into `/lrh-confirm-fixes`
Step 2 (empty-thread gate) and Step 4 (confirm gate) -- both gated behind
`confirm_fixes_batch: auto_unless_unusual` (ships `always_confirm`,
unchanged, per this WI's non-goals), both always display the batch summary
even when auto-proceeding. `closeout_plan` untouched anywhere in this
change, per `DEC-DELIBERATE-CHAIN-INITIATION`'s categorical exclusion.

`/lrh-self-review` diff-mode pass (execution record:
`2026_08_24_00_05_50_LRH_CHAIN_DEFAULTS_INCREMENT_2_SELFREVIEW`) flagged
that this file and the skill text both referenced "the WI's execution
record" for evidence before that record existed -- correctly observed, but
not a defect: this record, created at Step 9 per `/lrh-implement`'s own
step order, is that record. Also caught and fixed a genuine pre-existing
gap: `round-cap-gate.md`'s `GATE-DEFINITION` markers (added by PR #623)
had never propagated to `.agents/`/`.gemini/` mirrors.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `tests/confirm_fixes_batch_test.py`: 12/12 passing.
- `tests/` (excluding `tests/smoke`): 1403/1403 passing.
- Mirror parity: `diff -r` clean for `lrh-confirm-fixes` across `src/`,
  `.claude/`, `.agents/`, `.gemini/`; `land-workflow.md` byte-identical
  across all four locations.

# Follow-up

- `confirm_fixes_batch` ships off (`always_confirm`); opting in to
  `auto_unless_unusual` is a separate, deliberate repo-level decision, same
  as `chain_init_confirmation`'s own opt-in.
- Report restart requirement: any in-flight `/lrh-confirm-fixes` session
  must restart to pick up this change.
