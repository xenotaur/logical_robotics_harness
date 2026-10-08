---
execution_id: 2026_10_08_06_16_32_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_CONFIRM
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_CONFIRM)[2026-10-08T05:54:30+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_07_16_28_36_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/783
commit: 
created_at: 2026-10-08T06:16:32+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/783
session_transcript: pending
---

# Summary

Confirm-fixes for PR #783, run inline from `/lrh-land` Step 5 within
`/lrh-execute`. The fixes were written in this session, so a cold-context
subagent did the verification, and was then resumed for one scoped re-check.

# Result

**Pass 1, against `6fa0258d`.** Four threads were Clear-satisfied:
- Copilot r4209428245: a failed staleness check now refuses.
- Copilot r4209428318: an identical-stamp re-stamp now refuses.
- Copilot r4209428539: a real test now covers a profile-write failure.
- Codex P1 r4209472029: the dry-run preview is bound to the applied re-stamp
  by a digest.

Two threads were **Partial**: Copilot r4209428413 and Codex P2 r4209472048,
which duplicate each other. The staleness check still had an unguarded
`read_bytes()` at `gate_staleness.py:814`. The verifier also raised a P2:
the new test gave false confidence because it never covered an existing
store.

This fired the run's stop-work condition. The user lifted it for one fix
round and approved resolving the four Clear-satisfied threads, which were
resolved.

**Pass 2, against `8899ba98`** (fix `e7e4033d`, scoped re-check). Both Partial
threads and the P2 were now Clear-satisfied. The verifier re-ran its probe
(an existing store plus an unreadable target): `plan_restamp` refuses
cleanly, and `compute_status` reports stale with "unreadable -- failing
closed". It found no new P1, P2, or P3.

The autopilot check returned "unusual" because of the earlier exception, so
I asked live. The user approved, and the two threads were resolved.

**Final state:** 0 of 6 threads unresolved.

**Step 6 thread-resolution verdict: green.**

# Validation

- `lrh validate`: 0 errors.
- `scripts/test`: OK.
- `scripts/lint` and `scripts/format`: clean, using the LRH conda env.

# Follow-up

These P3s were deferred under the agreed policy:
- `restamp --expect-digest` is opt-in for manual CLI use. Every skill
  re-stamp site passes it.
- The digest omits each fingerprint entry's displayed absolute path.
