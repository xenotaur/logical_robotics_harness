---
execution_id: 2026_10_08_05_57_42_LOCAL_AGENT_ALLOW_FLAGGED
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_ALLOW_FLAGGED)[2026-10-08T05:51:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/791
commit:
created_at: 2026-10-08T05:57:42+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner chose A+B now (PR 788), c1 next, and c3 filed as a work item, after a T0 ask false positive on recorder.py
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

A control-plane change following the owner's decisions after a T0 `ask`
false positive. The sensitivity scanner read `token: Callable[[], str]` in
`experimental/local_agent/recorder.py` as a secret.

# Result

- **(c1)** PROP-LOCAL-AGENT-DOGFOOD Decision 3 gains an explicit,
  category-bound owner override, `--allow-flagged <path>=<category>[,...]`,
  for `--files` questions:
  - it is refused for other high-severity categories, unflagged files,
    unrequested files, or path-excluded files;
  - it never applies to `--wi`, `brief`, overview questions, or
    model-initiated T2 reads;
  - it is logged by path and category, and exports are unchanged;
  - WI-LOCAL-AGENT-001 and WI-LOCAL-AGENT-002 are aligned;
  - "Excluded always" becomes "Excluded by default", and the owner decision
    is recorded with its date.
- **Folded in:** the three wording fixes deferred from PR 761.
- **(c3)** A new proposed work item,
  `WI-SENSITIVITY-SECRET-ASSIGNMENT-CODE-FP`, to fix the shared
  secret-assignment rule's false positives on code-shaped values. Measured
  examples and every consumer are listed.
- **Self-review:** 1 high, 5 medium, 8 low, and 5 nits, all fixed. See
  `*LOCAL_AGENT_ALLOW_FLAGGED_SELFREVIEW`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- Both WIs are `prompt_ready`.

# Follow-up

- Implement `--allow-flagged` in `experimental/local_agent` (an experimental
  PR) after this lands.
- `WI-SENSITIVITY-SECRET-ASSIGNMENT-CODE-FP` stays proposed until the owner
  activates it.
