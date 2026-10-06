---
execution_id: 2026_09_30_23_41_39_LOCAL_AGENT_SENSITIVITY_THRESHOLD
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_SENSITIVITY_THRESHOLD)[2026-09-30T23:40:25+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/761
commit: a857103256cfc39126b44038809c825f26e543c1
created_at: 2026-09-30T23:41:39+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner chose option 2 (exclude on high-severity scanner findings only; medium as warnings), control-plane PR before the T0 ask PR
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

A control-plane amendment to `PROP-LOCAL-AGENT-DOGFOOD` Decision 3, made at the
owner's request. It narrows source exclusion to sources with high-severity
sensitivity-scanner findings. Medium findings (email, IP address, phone) become
category-only warnings in the source summary.

While implementing T0 `ask`, a fake-backend run excluded the prototype README
for `127.0.0.1`. Across 1,146 tracked text files, the any-finding rule excluded
58, including the repository README; the high-only rule excludes 23.

# Result

- **Proposal Decision 3:** the high-severity exclusion list is named. Medium
  findings are warned by category only. The text states that the relaxation
  relies on the local-only adapter checks. Exports and the `report` summary
  still withhold text on any finding.
- **WI-LOCAL-AGENT-001:** the acceptance entry, step 2, step 7, and the
  Definition of Done are aligned.
- **WI-LOCAL-AGENT-002:** the T2 read rejection is aligned.

The diff-mode self-review found five issues (one medium, three low, one nit),
all fixed. See `2026_09_30_23_40_29_LOCAL_AGENT_SENSITIVITY_THRESHOLD_SELFREVIEW`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- The T0 `ask` PR implements the threshold, with category-only warnings and a
  test.
