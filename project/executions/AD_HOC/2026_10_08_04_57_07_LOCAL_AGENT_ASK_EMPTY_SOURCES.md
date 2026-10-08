---
execution_id: 2026_10_08_04_57_07_LOCAL_AGENT_ASK_EMPTY_SOURCES
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ASK_EMPTY_SOURCES)[2026-10-08T02:23:22+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/788
commit:
created_at: 2026-10-08T04:57:07+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner reported two hallucinated T0 ask answers and chose fixes A+B now, c1 next, c3 as a work item
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Fixes for the owner-reported T0 `ask` bug (WI-LOCAL-AGENT-001), under the
Experimental PR Process.

The owner's `--files experimental/local_agent/recorder.py` question excluded
the only file. The sensitivity scanner's keyword rule reads the
`token: Callable[...]` annotation as a secret. The model was called anyway
and invented an answer citing a nonexistent S1. Both runs were rated `b`.

# Result

- **(A) Refuse when nothing would be sent.** Files mode needs at least one
  included source, and work-item mode needs the work item itself.
  - `run_ask` refuses as `missing_prerequisite` before preflight.
  - The CLI refuses before the confirmation prompt and logs each exclusion.
  - A file whose first line exceeds the remaining budget is excluded.
  - Duplicate `--files` entries are sent once.
- **(B) Make it visible.** The summary shows `sending N of M` and a
  `NOT SENDING` line.
- **Self-review:** 1 medium, 2 low, and 1 nit fixed; 1 nit left. See
  `2026_10_08_04_56_33_LOCAL_AGENT_ASK_EMPTY_SOURCES_SELFREVIEW`.

# Validation

- `experimental/local_agent/test`: 155 tests OK.
- Lint and format clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors.

# Follow-up

- **(c1):** a control-plane amendment to PROP-LOCAL-AGENT-DOGFOOD Decision 3
  and WI-LOCAL-AGENT-001 for an explicit, logged `--allow-flagged <path>`
  override, followed by its implementation.
- **(c3):** a proposed work item to fix the shared scanner's
  `secret.keyword_assignment` false positive on Python type annotations
  (`src/lrh/shared/sensitivity_rules.py`).
