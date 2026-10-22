---
execution_id: 2026_10_09_23_51_30_WI_LOCAL_AGENT_001_T1_BRIEF_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_T1_BRIEF_SELFREVIEW)[2026-10-09T23:51:29+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/809
commit: f360acd9eb71cd028c253430e6ce5688952fa8cb
created_at: 2026-10-09T23:51:30+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(AD_HOC:WI_LOCAL_AGENT_001_T1_BRIEF)[2026-10-09T18:30:04+00:00]
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Diff-mode `/lrh-self-review` of T1 `brief` (WI-LOCAL-AGENT-001 step 3),
before the first push. `rerun_of` is empty by design. It was report-only; the
implementing session applied the fixes.

# Result

A cold subagent confirmed:

- `--allow-flagged` cannot reach `brief`;
- the requirement that the work item itself be included applies;
- every pre-model failure records kind `brief` and the `work_item_id`;
- existing `ask` runs are unchanged.

Findings, all fixed:

1. **High (privacy/regression): export routed only `kind == "ask"` to the
   ask path.** Brief runs fell into the pilot path, which exported the
   rating note and question by default and never exported the answer. The
   main session re-verified this at `export.py:345`. **Fixed:** `ask` and
   `brief` runs share the ask path, with a test of a rated brief exported
   with and without `--include-output`.
2. **Medium: the readiness regex rejected common Markdown wrappers.** Bold,
   code, list, quote, heading, and a trailing period all failed, so correct
   briefings were flagged. **Fixed:** light Markdown is now normalized away,
   with a test for each wrapper.
3. **Low:** brief failure records kept `prompt_version` `ask_v1`. **Fixed:**
   `record_failure` takes the prompt version, and the CLI passes `brief_v1`.
4. **Low:** a mid-answer line could pass the "ends with" rule. **Fixed:** a
   new `misplaced` status covers an agreeing line that is not last, and it
   is flagged. The README notes that the prose is not checked.
5. **Low:** the `pilot` default and the label change were untested.
   **Fixed:** a `summarize` and `inspect` test was added.
6. **Nit:** `inspect` now shows `readiness_check`.
7. **Nit:** the README lists the absent options and how brief runs export.

The new tests fail against the pre-fix code.

# Validation

- `experimental/local_agent/test`: 195 tests OK.
- Lint and format clean.

# Follow-up

None.
