---
execution_id: 2026_09_26_07_04_11_WI_LOCAL_AGENT_001_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_REVIEW)[2026-09-26T06:54:40+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_05_19_23_WI_LOCAL_AGENT_001
pr: https://github.com/xenotaur/logical_robotics_harness/pull/735
commit: 
created_at: 2026-09-26T07:04:11+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/735
session_transcript: pending
---

# Summary

Review-response round 1 for PR #735 (WI-LOCAL-AGENT-001 PR B), run inline from
`/lrh-execute` → `/lrh-land`. The owner confirmed all eight dispositions at the
Step 4 gate. Fix commit: `8a5a4eb6`.

# Result

1. **Codex P2, recovery ignored a durable outcome event.** Valid, fixed.
   `recover_run` restores the last logged `outcome` event before falling back
   to `incomplete`. Test added.
2. **Codex P2, export did not re-hash the packet.** Valid, fixed. Export
   verifies `packet_sha256` against the stored manifest and text, and refuses
   on mismatch. Test added.
3. **Codex P2, host-dependent proxy test.** Valid, fixed. The proxy
   environment is cleared (`clear=True`) inside the test.
4. **Copilot, endpoint credentials (user info) accepted and recorded.** Valid,
   fixed. Such URLs are refused. Test added.
5. **Copilot (high), "`extractall(filter=)` requires 3.12".** Partly
   incorrect: the filter was backported in 3.11.4, and this environment runs
   3.11.16. The edge case is real for 3.11.0–3.11.3, since `requires-python`
   is `>=3.11`. Guarded: extraction now refuses with a clear error when
   `tarfile.data_filter` is missing, and never extracts unfiltered. Test
   added, and the README notes Python ≥ 3.11.4.
6. **Copilot, hard-coded layer digest.** Valid, fixed. The layer digest is
   recorded only for the pre-registered model and manifest digest; otherwise
   it is `null`. Test added.
7. **Copilot (high), wall time not enforced.** Valid, fixed. Elapsed time is
   compared with the budget after the call, and an overrun is a `timeout`.
   Test with an injected clock.
8. **Copilot, returned output tokens not enforced.** Valid, fixed. A count
   over `max_output_tokens` ends the run as `budget_exhausted`. Test added.

# Validation

- `experimental/local_agent/test`: Ran 65 tests, OK.
- `scripts/test --log`: Ran 1795 tests, OK.
- `scripts/format --check --diff` and `scripts/lint`, both default and on
  `experimental/local_agent`: clean.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Confirm-fixes resolves the eight threads.
