---
execution_id: 2026_10_09_02_04_47_LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS_SELFREVIEW)[2026-10-09T02:04:46+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-10-09T02:04:47+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS)[2026-10-09T01:57:41+00:00]
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Diff-mode `/lrh-self-review` of the follow-up fixes for the three lows
deferred from PR 799, run before the first push. `rerun_of` is empty by
design. It was report-only; the implementing session applied the fixes.

# Result

A cold subagent found the three fixes correct. Each new test fails against
the previous code, and surrogate-escaped names never reach an encoder. It
reported:

1. **Low (pre-existing, adjacent): an excluded `--files` path with control
   characters was echoed raw.** The path appeared unquoted in the prompt's
   "Excluded sources" block and in the summary, so it could forge a line in
   the model prompt. The main session re-verified this in `ask._assemble`.
   **Fixed:** excluded entries store `sources.shown_path(path)`, with a test
   for both the prompt and the summary.
2. **Nit: `_shown` duplicated the path-safety predicate.** **Fixed:** a shared
   `sources.unsafe_path_char` and `shown_path` now also cover C1 controls,
   and `check_path_allowed` rejects C1 too, with a test.
3. **Nit: the message referred to a hidden global `--max-packet-bytes`.**
   **Fixed:** it now says the option is global and goes before `ask`.
4. **Nit: the branch was behind `origin/main`.** **Fixed:** rebased before
   the push.

# Validation

- `experimental/local_agent/test`: 175 tests OK.
- Lint and format clean.

# Follow-up

None.
