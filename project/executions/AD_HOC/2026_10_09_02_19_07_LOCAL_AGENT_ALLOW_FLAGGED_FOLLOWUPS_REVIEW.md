---
execution_id: 2026_10_09_02_19_07_LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS_REVIEW
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS_REVIEW)[2026-10-09T02:18:04+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_09_02_08_18_LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/803
commit: 3e55eb5e68e7480c2123cf737cb66ee794de6786
created_at: 2026-10-09T02:19:07+00:00
agent: claude_app
instruction_source: lrh-land Step 4 review-response for PR 803; owner confirmed the fix
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Review-response round 1 for PR #803. One Copilot thread; Codex completed
with no comments.

# Result

1. **`PRRT_kwDOR7l1D86qnvZJ` (Copilot, `ask.py:230`): work-item omissions
   were not quoted.** `context.build_packet` stored a rejected related path
   verbatim in `omitted_sources`. That path was then rendered raw into the
   packet's omitted block and copied into the `ask` summary, so a tracked
   file name containing a newline could forge prompt and terminal lines.
   **Fixed:**
   - all three omission appends in `build_packet` now store
     `sources.shown_path(rel_path)`;
   - a work-item regression test, with a `related_design` file name
     containing a newline, checks both the packet text and the summary;
   - the test fails against the previous `context.py`.

# Validation

- `experimental/local_agent/test`: 176 tests OK.
- Lint and format clean.
- `lrh validate`: 0 errors.

# Follow-up

None.
