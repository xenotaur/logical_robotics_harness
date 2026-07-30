---
execution_id: 2026_07_30_02_19_53_CODIFY_SLUG_BASED_IDEMPOTENCE_EXCEPTION
prompt_id: PROMPT(AD_HOC:CODIFY_SLUG_BASED_IDEMPOTENCE_EXCEPTION)[2026-07-30T02:19:45-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/440
commit: 
agent: claude_app
instruction_source: follow-up item #3 from harness PR #438's final report (project/design/backlog.md "Filename-slug idempotence search drives blocking, contrary to PROMPTS.md")
session_transcript: claude-app:3fcab22f-9ebe-4392-bf31-2103fce507f2
created_at: 2026-07-30T02:19:53-04:00
---

# Summary

Resolve the deferred design question from PR #438: `PROMPTS.md`'s "Soft
idempotence before execution" section says exploratory search must never
drive blocking, but `lrh-review-response`, `lrh-proposal`, `lrh-work-item`,
and `lrh-workstream` all use a filename-slug `find` against
`project/executions/AD_HOC/` to do exactly that, before minting a new
prompt ID (since `lrh prompt label` always mints a fresh timestamped one,
so there's no existing ID to check with `check-execution`). Presented the
user 3 options (codify the exception in docs; make it non-blocking
everywhere; build real CLI tooling for slug-based lookup) with a
recommendation; user chose the lightest option.

# Result

Added a "Pre-mint duplicate detection by slug" subsection to `PROMPTS.md`'s
"Soft idempotence before execution" section, naming filename-slug-by-bucket
search (matched to the complete trailing filename segment, not a
substring) as authoritative for this specific pre-mint case — distinct
from the still-non-authoritative general exploratory/fuzzy search the
original rule was warning about. No code changes to any skill or the CLI:
this documents behavior that was already correct and already applied
consistently across all 4 skills, closing the gap between documented
policy and actual practice rather than changing practice. Updated
`project/design/backlog.md`'s "Filename-slug idempotence search drives
blocking, contrary to `PROMPTS.md`" entry to record the resolution, the
two options not taken, and a concrete revisit trigger for the
more-complete CLI-tooling option (a real incident, or a 5th skill needing
the same pattern).

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- Docs-only change (`PROMPTS.md`, `project/design/backlog.md`) — no skill
  or CLI code touched, so no skill-behavior or CLI test suite affected

# Follow-up

- Revisit the CLI-tooling option (option 3) per the backlog entry's
  revisit trigger, not on a schedule.
