---
execution_id: 2026_10_11_04_39_48_LOCAL_AGENT_REVISE_PROTOTYPE
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_REVISE_PROTOTYPE)[2026-10-11T04:38:54+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/826
commit:
created_at: 2026-10-11T04:39:48+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner chose "revise" for WI-LOCAL-AGENT-001 and asked for the follow-up PRs first; this is the prototype PR
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Prototype follow-ups to the owner's 2026-10-10 "revise" decision on
WI-LOCAL-AGENT-001. The control-plane changes merged in PR 823.

# Result

- **T1 `brief`:** the readiness block is stored as the output's `preamble`;
  diagnostic values are collapsed to one line; the docs no longer claim the
  briefing prose is checked.
- **Prompts:** `ask_v2` and `brief_v2` put the sources before the question.
- **Partial answers:** an interrupt after the final write keeps the final
  answer; export carries `answer_partial` and `preamble`, and scans the
  preamble.
- **`log`:** `--since YYYY-MM-DD` (UTC) and repeatable `--kind`.
- **README:** no high-severity scanner findings.

The live timing check of the prompt reorder was inconclusive. Baseline
`ask_v1` took 146 s and 163 s. The two `ask_v2` runs (171 s, 225 s) ran
under heavy machine load, 88 minutes apart, after the model had unloaded.

# Validation

- `experimental/local_agent/test`: 210 tests OK; the new and changed tests
  fail against `main`'s code.
- `scripts/lint experimental/local_agent`: clean.
- `lrh validate`: 0 errors, 0 warnings.
- Diff-mode self-review: 1 medium, 4 lows, and nits fixed; 1 nit left as is.

# Follow-up

- Rerun the before/after timing back to back under normal load.
- The owner uses the toys further, then records WI-LOCAL-AGENT-001's
  resolution.
