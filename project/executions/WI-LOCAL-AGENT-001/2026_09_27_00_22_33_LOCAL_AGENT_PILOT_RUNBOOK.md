---
execution_id: 2026_09_27_00_22_33_LOCAL_AGENT_PILOT_RUNBOOK
prompt_id: PROMPT(WI-LOCAL-AGENT-001:LOCAL_AGENT_PILOT_RUNBOOK)[2026-09-26T22:07:47+00:00]
work_item: WI-LOCAL-AGENT-001
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/745
commit: 
created_at: 2026-09-27T00:22:33+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner-requested runbook PR for WI-LOCAL-AGENT-001's pre-registered pilot
session_transcript: pending
---

# Summary

A small, owner-requested PR before the live pilot for `WI-LOCAL-AGENT-001`. It
makes the pre-registered protocol in
`experiments/01_local_agent_briefing/README.md` runnable command by command. It
is partial progress: `WI-LOCAL-AGENT-001` stays `active`, and closeout of this
PR must not resolve it.

# Result

The owner asked whether a README documented the pilot procedure. The review
found five gaps:

1. No way to select a prompt version, although the protocol requires `v1`–`v3`.
2. No B0 capture path.
3. No scores example.
4. No task-to-packet mapping.
5. No runbook-level export or freeze instructions.

This PR closes all five without changing any pre-registered content:

- `run --prompt-version`;
- the `task` and `b0` subcommands, with a `condition` of B0 or B1 on every
  run;
- a null-placeholder scores template that `evaluate` refuses when unfilled;
- a numbered Runbook, including the counterbalanced order table.

The diff-mode self-review found seven issues, and all were fixed. See
`project/executions/AD_HOC/2026_09_27_00_21_24_LOCAL_AGENT_PILOT_RUNBOOK_SELFREVIEW.md`.

# Validation

- `scripts/version tools`: Python 3.11.16, ruff 0.15.12, black 26.3.1.
- `scripts/format --check --diff` and `scripts/lint`, both default and on
  `experimental/local_agent`: clean.
- `scripts/test --log`: Ran 1806 tests, OK.
- `experimental/local_agent/test`: Ran 78 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.
- A `task` dry run built packets for all 12 tasks.
- An end-to-end CLI check of `b0`, `evaluate`, and `export`.

# Follow-up

- **PR C:** the live pilot, following the Runbook.
- **Still deferred to PR C:**
  - recovery restoring `usage`/`citations`;
  - hash-checked `inspect`;
  - a hard wall-time cut-off.
