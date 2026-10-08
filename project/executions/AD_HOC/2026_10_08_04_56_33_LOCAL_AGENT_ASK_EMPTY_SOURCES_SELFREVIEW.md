---
execution_id: 2026_10_08_04_56_33_LOCAL_AGENT_ASK_EMPTY_SOURCES_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ASK_EMPTY_SOURCES_SELFREVIEW)[2026-10-08T04:56:33+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-10-08T04:56:33+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(AD_HOC:LOCAL_AGENT_ASK_EMPTY_SOURCES)[2026-10-08T02:23:22+00:00]
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Diff-mode `/lrh-self-review` of the fix for an owner-reported T0 `ask` bug.
Every requested source was excluded, yet the model was still called and
invented citations. The review ran before the first push, so `rerun_of` is
empty. It was report-only; the implementing session applied the fixes.

# Result

A cold subagent confirmed:

- `run_ask` refuses before preflight;
- the CLI refuses before the prompt and logs the run;
- the summary shows "sending N of M";
- the tests fail without the fix.

Findings:

1. **Medium (correctness): zero-byte sources still counted.** A file whose
   first line exceeded the remaining budget was kept as a zero-byte source,
   so the empty-context bug stayed reachable. The main session re-verified
   this in `ask._assemble`. **Fixed:** such a file is excluded as `budget`,
   with a test.
2. **Low:** the CLI's refused run did not record the exclusions. **Fixed:**
   the detail now lists each excluded path with its reason.
3. **Low:** work-item mode stayed sendable when the work item itself was
   excluded. **Fixed:** it now requires the work item itself, with a test.
4. **Nit:** duplicate `--files` entries were sent and counted twice.
   **Fixed:** they are de-duplicated in order, with a test.
5. **Nit:** in work-item mode, "requested" overstates what M counts. This is
   left as is; the count is consistent.

# Validation

- `experimental/local_agent/test`: 155 tests OK.
- Lint and format clean.
- `lrh validate`: 0 errors.

# Follow-up

None.
