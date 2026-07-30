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
this documents behavior that was already correct in `lrh-proposal`,
`lrh-work-item`, and `lrh-workstream`, closing the gap between documented
policy and actual practice rather than changing practice. Updated
`project/design/backlog.md`'s "Filename-slug idempotence search drives
blocking, contrary to `PROMPTS.md`" entry to record the resolution, the
two options not taken, and a concrete revisit trigger for the
more-complete CLI-tooling option (a real incident, or a 5th skill needing
the same pattern).

Review on this PR surfaced 5 findings, all addressed:
- Codex/Copilot: the new subsection cited `lrh-review-response` as
  applying the same pattern, but that skill actually uses an earlier,
  less complete version (broader substring glob, no per-match status
  inspection) — reworded to describe the divergence honestly instead of
  claiming equivalence, and added item 5 to the "Idempotence-check
  refinements deferred from PR #438" backlog entry to bring it up to the
  same standard.
- Codex: the packaged client bootstrap template
  (`src/lrh/templates/project_bootstrap/prompt_workflow/PROMPTS.md`) still
  presented only the old exact-ID-only rule with no pre-mint exception —
  added a condensed, self-contained version of the same exception there
  too, so newly bootstrapped client repos get current policy.
- Codex: the new subsection claimed identical status handling to the
  exact-ID rule, but silently dropped the "continue only if the prompt
  indicates rerun or follow-up" condition for `failed`/`reverted`/
  `superseded` matches (present in the exact-ID rule and
  `project/executions/README.md:139`) — reworded to explicitly name this
  as a deliberate divergence with its own rationale (no pre-existing
  "rerun of X" declaration mechanism exists before a slug's history is
  even known), rather than misrepresenting it as the same rule.
- Copilot: this record's own Validation section claimed the change was
  limited to `PROMPTS.md` and `backlog.md`, omitting the execution record
  itself and (once found) the bootstrap template — corrected below.

A second review round on the fix commit surfaced 2 more findings, both
addressed: Codex found a third copy of this same rule —
`project/executions/README.md`'s own "Soft idempotence guidance" section,
which the earlier fix missed entirely — added the equivalent "Pre-mint
duplicate detection by slug" subsection there too, matching that file's
existing depth, and added a short exception note to the bootstrap
template's own terser `project/executions/README.md` stub for the same
reason. Copilot (low-confidence, correct) found the bootstrap template's
condensed wording said `rerun_of` links "either way" on any match, which
is wrong — a blocked `landed`/`in_progress` match with no explicit rerun
produces no new record to link at all; reworded to only link `rerun_of`
when a new record is actually created (an explicit rerun of a block, or
continuing past a non-blocking match).

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- No skill or CLI *code* touched (only documentation: `PROMPTS.md`,
  `project/executions/README.md`, `project/design/backlog.md`, the
  bootstrap template's `PROMPTS.md` and `project/executions/README.md`
  stubs, and this execution record) — no skill-behavior or CLI test suite
  affected

# Follow-up

- Revisit the CLI-tooling option (option 3) per the backlog entry's
  revisit trigger, not on a schedule.
- Bring `lrh-review-response`'s idempotence check up to the same standard
  as the other 3 skills — tracked as item 5 in the "Idempotence-check
  refinements deferred from PR #438" backlog entry.
