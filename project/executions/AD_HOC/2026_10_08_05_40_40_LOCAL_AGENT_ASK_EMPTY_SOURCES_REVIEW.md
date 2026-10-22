---
execution_id: 2026_10_08_05_40_40_LOCAL_AGENT_ASK_EMPTY_SOURCES_REVIEW
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ASK_EMPTY_SOURCES_REVIEW)[2026-10-08T05:39:48+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_08_04_57_07_LOCAL_AGENT_ASK_EMPTY_SOURCES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/788
commit: f95464c38e0a9a6961e7567d6afd4c7034fa63f9
created_at: 2026-10-08T05:40:40+00:00
agent: claude_app
instruction_source: lrh-land Step 4 review-response for PR 788; owner confirmed the fix
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Review-response round 1 for PR #788. One Codex thread; Copilot left no
comments.

# Result

1. **`PRRT_kwDOR7l1D86qND5C` (Codex P2): refused CLI runs lost context
   provenance.** `record_failure` stored only the question and outcome, so
   `inspect` showed `source commit: None`. **Fixed:**
   - a new `ask.context_fields(ctx)` is shared by `run_ask` and
     `record_failure`;
   - `record_failure` takes an optional `ctx`, which every CLI refusal after
     context assembly passes (no sources, declined, adapter errors);
   - the CLI test asserts mode, commit, sources, exclusions, and the
     `inspect` commit line. It fails against the previous code.

# Validation

- `experimental/local_agent/test`: 155 tests OK.
- Lint and format clean.
- `lrh validate`: 0 errors.

# Follow-up

None.
