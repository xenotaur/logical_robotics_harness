---
execution_id: 2026_07_06_03_34_25_DECISION_TIER_DOC_CROSS_REFERENCES
prompt_id: PROMPT(AD_HOC:DECISION_TIER_DOC_CROSS_REFERENCES)[2026-07-06T03:30:25-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/377
commit: cd5d36b
created_at: 2026-07-06T03:34:25-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/377
session_transcript: claude-app:bbcb758a-f12c-44cf-ad69-3dc5cadf53b6
---

# Summary

Follow-up to `WI-DECISION-RECORD-CONVENTIONS`: four files cited
`project/memory/decisions/precedence_semantics.md` in isolation without
explaining why it's a standalone file rather than a `decision_log.md` entry.
Point each to `design.md` §14 ("Decision-record tiers").

# Result

Added a one-line pointer to `design.md` §14 in:

- `AGENTS.md:76`
- `project/design/architecture.md:104`
- `project/design/repository_spec.md:150`
- `docs/explanations/precedence-model.md` (intro, line 6-8, and the
  "Authoritative sources" list, line 99)

No behavior change; docs only. Nothing skipped.

# Validation

- `scripts/version tools` — lrh 0.2.5.dev673+g111f7ab13, Python 3.11.8, Ruff 0.15.12, Black 26.3.1
- `scripts/format --check --diff` — 175 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 696 tests OK
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

None deferred.
