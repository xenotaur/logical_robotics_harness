---
execution_id: 2026_10_06_04_33_55_WI_LOCAL_AGENT_001_T0_ASK_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_T0_ASK_REVIEW)[2026-10-06T04:29:46+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_06_03_57_55_WI_LOCAL_AGENT_001_T0_ASK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/777
commit: 3b9c194d80ae4197c6f399a9e93e603e02d39140
created_at: 2026-10-06T04:33:55+00:00
agent: claude_app
instruction_source: lrh-land Step 4 review-response for PR 777; owner confirmed all dispositions
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Review-response round 1 for PR #777 (T0 `ask`). Eight threads arrived on the
first push; all were fixed after the owner confirmed the dispositions. None
were dismissed.

# Result

1. **`PRRT_kwDOR7l1D86pUHAb` (Codex P1) and `PRRT_kwDOR7l1D86pUJB0`
   (Copilot): work-item diagnostics could carry a high-severity value.** A
   credential URL in an unresolved reference reached the prompt and
   `run.json` even when the work-item source itself was excluded.
   **Fixed:** `ask.build_context` scans the fully rendered context in every
   mode. A high-severity finding refuses the request with a category-only
   error, which the CLI logs as `missing_prerequisite`.
2. **`PRRT_kwDOR7l1D86pUJCK` (Copilot): default export carried unscanned
   failure text.** `outcome_detail` and event `detail` were exported as-is.
   **Fixed:** flagged details are replaced with `[withheld: <categories>]`,
   and a final whole-document scan refuses any export that still carries a
   finding.
3. **`PRRT_kwDOR7l1D86pUJCR` (Copilot): `delete ""` removed every run.**
   **Fixed:** `run_dir` rejects empty ids, backslashes, `/`, and leading `.`.
4. **`PRRT_kwDOR7l1D86pUJCk` (Copilot): nested private paths were admitted
   and listed.** **Fixed:** private subtrees are matched at any path depth.
5. **`PRRT_kwDOR7l1D86pUJDA` (Copilot): `no` still sent the context.**
   **Fixed:** only Enter, `y`, or `yes` sends; anything else declines and is
   logged as `cancelled`.
6. **`PRRT_kwDOR7l1D86pUJDK` (Copilot): an unreadable `--fake-response`
   file was not logged.** **Fixed:** it is logged as `missing_prerequisite`.
7. **`PRRT_kwDOR7l1D86pUHAg` (Codex P2): p90 was one sample too high.**
   **Fixed:** nearest rank, `ceil(0.9 n) - 1`.

Each fix has a regression test, for 129 tests in total.

# Validation

- `experimental/local_agent/test`: 129 tests OK.
- Format and lint clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors, 0 warnings.
- On the real repository, overview mode (README with `WARN: ip_address`) and
  `--wi WI-LOCAL-AGENT-001` (6 sources, 0 excluded) both still build.

# Follow-up

None beyond the deferred items in the self-review record.
