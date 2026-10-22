---
execution_id: 2026_10_08_18_32_12_LOCAL_AGENT_ALLOW_FLAGGED_IMPL
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED_IMPL)[2026-10-08T18:15:12+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/799
commit: a2951d2442181b655327ca9795f0faf5497dd247
created_at: 2026-10-08T18:32:12+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner asked to start the --allow-flagged implementation PR after the control-plane change (PR 791) merged
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Implements the `--allow-flagged` owner override in `experimental/local_agent`.
It follows PROP-LOCAL-AGENT-DOGFOOD Decision 3 and WI-LOCAL-AGENT-001, as
amended in PR 791, under the Experimental PR Process.

# Result

- **`sources`:** `high_findings` returns structured high-severity findings,
  with start and end lines and no values. `make_source(..., allow=...)` lifts
  exactly the named categories, and is refused for missing or extra
  categories. Only findings in the sent lines are listed.
- **`ask.build_context(..., allow_flagged=...)`:**
  - it works with `--files` only;
  - it refuses unrequested files, and files excluded by path, budget, or
    category; an override never degrades into an exclusion;
  - duplicate entries are merged;
  - the final scan skips only the allowed body lines, and the header is
    still scanned;
  - `allowed_flagged` is structured and recorded;
  - the summary lists each finding as `ALLOWED DESPITE`.
- **CLI:** `--allow-flagged PATH=CATEGORY[,...]`. A typed `yes` on stderr
  and stdin terminals is required before any adapter is built. The override
  is refused with `--yes` or without a terminal, and declines are logged as
  `cancelled`.
- **README:** documents the override.
- **Self-review:** 1 medium, 4 low, and 4 nits, all fixed, and the branch was
  rebased. See `*LOCAL_AGENT_ALLOW_FLAGGED_IMPL_SELFREVIEW`.

# Validation

- `experimental/local_agent/test`: 170 tests OK.
- Lint and format clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors.

# Follow-up

- Deferred items 2 and 3 from PR 791 (WI-001 test-bullet wording) are for
  WI-001's closeout.
- The owner can now ask about `recorder.py` live.
