---
execution_id: 2026_10_07_16_00_40_WI_LOCAL_AGENT_001_T0_ASK_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_T0_ASK_REVIEW)[2026-10-07T15:57:46+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_06_03_57_55_WI_LOCAL_AGENT_001_T0_ASK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/777
commit: 
created_at: 2026-10-07T16:00:40+00:00
agent: claude_app
instruction_source: lrh-land Step 4 review-response round 5 for PR 777 (findings from the round-4 PR-mode substitute self-review); owner chose option (a), fix first
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Review-response round 5 for PR #777. It addresses the two lower findings of
the round-4 substitute self-review
(`2026_10_06_06_22_24_WI_LOCAL_AGENT_001_T0_ASK_PR_SELFREVIEW`). The owner
chose to fix rather than defer the safety-category low.

# Result

1. **Low (safety): extra URL parts could be echoed.** A `--base-url` with a
   path, params, query, or fragment was accepted, and the transport error
   echoed it into stderr and the private run record. An opaque value the
   scanner does not recognize could also survive export. **Fixed:**
   `check_loopback_url` accepts only `http://<loopback-host>[:<port>]`, with
   an empty or `/` path. Anything else is refused without being echoed.
2. **Nit: the non-loopback error named the host.** **Fixed:** it now says
   only that the host is not loopback.

Both new tests were confirmed to fail against the previous `model.py`.

# Validation

- `experimental/local_agent/test`: 143 tests OK.
- Format and lint clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

None.
