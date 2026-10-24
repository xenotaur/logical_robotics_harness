---
execution_id: 2026_10_22_06_54_49_WI_LRH_DURABLE_MANUAL_RUN_STATE
prompt_id: PROMPT(AD_HOC:WI_LRH_DURABLE_MANUAL_RUN_STATE)[2026-10-22T06:46:09+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/849
commit:
agent: codex_app
instruction_source: project/work_items/proposed/WI-LRH-DURABLE-MANUAL-RUN-STATE.md
session_transcript: pending
created_at: 2026-10-22T06:54:49+00:00
---

# Summary

Create the next execution-framework planning artifact for durable manual run
state. The work item defines the `project/runs/<RUN-ID>/` contract, manual
lifecycle and recovery semantics, durable events, reuse of existing run
readiness/packet/report contracts, and the implementation acceptance tests.
Runtime implementation and workstream activation are intentionally deferred.

# Result

Created `WI-LRH-DURABLE-MANUAL-RUN-STATE` as a proposed deliverable on the
dedicated branch and opened PR #849. The governing
`WS-EXECUTION-FRAMEWORK` remains proposed/planned and was not modified.

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate` — 0 errors; one owner
  warning for `anthony` not being listed in contributors.
- `scripts/version tools` — pinned tools verified after environment bootstrap.
- `scripts/format --check --diff` — passed.
- `scripts/lint` — passed.
- `scripts/test` — passed, 2366 tests.
- `git diff --check` — passed.

# Follow-up

- Obtain review and readiness for `WI-LRH-DURABLE-MANUAL-RUN-STATE`.
- Reconcile the proposed/planned execution-framework workstream only after
  explicit approval of the workstream update.
- Use the ready work item as the input to the later implementation workflow;
  do not infer authorization for runtime implementation from this planning PR.
