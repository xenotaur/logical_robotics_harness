---
execution_id: 2026_10_08_06_06_02_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_REVIEW)[2026-10-08T06:02:55+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_08_05_53_59_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_IMPL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/783
commit: 53b839a564a73f0b80ec24f0d0f5d6710baf2566
created_at: 2026-10-08T06:06:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/783
session_transcript: claude-app:708f8a5c-20da-4910-bafb-fdecde18e51e
---

# Summary

Review-response round 2 on PR #783, run inline from `/lrh-land` Step 5.

Confirm-fixes re-verified round 1 with a cold-context subagent:
- Four threads were Clear-satisfied, and were resolved with the user's
  approval.
- The Copilot `r4209428413` and Codex P2 `r4209472048` threads, which
  duplicate each other, were judged **Partial**, together with a P2 noting
  the test gave false confidence.

That fired the run's stop-work condition. The user lifted it for this single
fix round. The fix is in commit `e7e4033d`.

# Result

**The gap.** `check_target_staleness` had a second, unguarded
`read_bytes()`, at `src/lrh/gate_staleness.py:814` on the previous head.
I re-verified it directly. Once a fingerprint store existed, an unreadable
installed file escaped as a raw `OSError` through `status`,
`check-staleness`, and `restamp`, which runs the staleness check first.

**The fix.** That read is now guarded. An unreadable file reports
`stale: true` with the reason "installed target file unreadable -- failing
closed". `restamp` then refuses with exit 2 when it reaches the
already-guarded read in `plan_fingerprints`.

**The test.** `test_unreadable_target_with_existing_store_fails_closed` closes
the false-confidence gap. It records a store first, then asserts that
`status` reads stale with the "unreadable" reason and that `plan_restamp`
refuses with a clean error.

# Validation

Run with the LRH conda env:
- `scripts/format` and `scripts/lint`: clean.
- `scripts/test`: OK.
- `lrh validate`: 0 errors, plus 1 warning that predates this change.

# Follow-up

- Scoped re-verification of the two Partial threads must run before they
  are resolved.
- These P3s go to Follow-up under the agreed policy:
  - `--expect-digest` is opt-in for manual CLI use.
  - The digest omits the displayed target paths.
