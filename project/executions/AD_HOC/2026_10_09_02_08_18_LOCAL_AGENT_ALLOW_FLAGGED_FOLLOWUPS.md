---
execution_id: 2026_10_09_02_08_18_LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS)[2026-10-09T01:57:41+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/803
commit: 3e55eb5e68e7480c2123cf737cb66ee794de6786
created_at: 2026-10-09T02:08:18+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner asked to start the small fix PR for the lows deferred from PR 799
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Fixes the three lows deferred from PR 799, plus an adjacent prompt-injection
gap found in the pre-push review, under the Experimental PR Process.

# Result

- **Non-UTF-8 tracked names:** `list_tracked_files` uses
  `surrogateescape`, and `check_path_allowed` rejects such names, so overview
  questions no longer crash. This was a regression from PR 799.
- **Unsafe paths:** a shared `sources.unsafe_path_char` / `shown_path`
  covers C0/C1 controls, DEL, and surrogates. It quotes paths in
  `--allow-flagged` refusals and in excluded-source entries in the prompt and
  summary, which could otherwise forge a prompt line. `check_path_allowed`
  now rejects C1 controls too.
- **Refusal message:** the "nothing to confirm" refusal is reworded and points
  at the global `--max-packet-bytes`.
- **Self-review:** 1 low and 3 nits, all fixed, and the branch was rebased.
  See `*LOCAL_AGENT_ALLOW_FLAGGED_FOLLOWUPS_SELFREVIEW`.

# Validation

- `experimental/local_agent/test`: 175 tests OK.
- Lint and format clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors.

# Follow-up

None.
