---
execution_id: 2026_07_30_02_19_53_CODIFY_SLUG_BASED_IDEMPOTENCE_EXCEPTION
prompt_id: PROMPT(AD_HOC:CODIFY_SLUG_BASED_IDEMPOTENCE_EXCEPTION)[2026-07-30T02:19:45-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/440
commit: b9b710f4b36f68d004cda4ce68ad943abbddaee5
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

A third review round on the fix commit surfaced 2 more findings, both
Codex, and both structural rather than typos: (1) the universal
status-handling matrix contradicted `lrh-confirm-fixes/SKILL.md:177-187`'s
already-documented **deliberate** deviation — prior `_CONFIRM` records are
warning-only, never blocking, because live review-thread state changes
between rounds (Decision 12), which the matrix's "landed/in_progress
blocks" language overrode without acknowledging; (2) the `planned` status
exists in the vocabulary but fit none of the matrix's three buckets
(blocking / non-blocking / ambiguous). Per user direction, ran `/lrh-design`
on this rather than patching the matrix a 4th time: the design concluded
the matrix itself was the wrong shape — trying to centrally enumerate
every skill's behavior for every status is what kept finding gaps, when
`lrh-confirm-fixes` already demonstrates the working alternative (state a
default, let a skill deviate and cite why locally).

Restructured `PROMPTS.md`'s subsection (and its `project/executions/README.md`
mirror and both bootstrap stubs) into an **invariant** (filename-slug
search matched to the complete trailing segment is authoritative for this
narrow question) plus a **default** (explicitly labeled as a default, not
a mandate — the same landed/in_progress-blocks,
failed/reverted/superseded-continues shape as before, but no longer
claimed as binding on every skill). Per user direction, the rationale is
captured in the control plane, not just in the doc prose: promoted
`project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md` (with
a `decision_log.md` stub entry), following this repo's own
decision-record-tier convention (`design.md` §14) and citing it from
`PROMPTS.md`/`README.md` rather than re-deriving the reasoning in each
copy. Updated both backlog entries to reflect the final state:
`lrh-review-response` and `lrh-confirm-fixes` are both item 5 in
"Idempotence-check refinements deferred from PR #438" (predate the
invariant, tracked as a follow-up, not touched here); the `planned`-status
gap is explicitly not resolved centrally — deferred to whichever skill
first needs a concrete answer.

A fourth review round on this commit found 2 more real issues in the
decision record itself and 5 low-confidence-but-correct Copilot nitpicks,
all addressed: Codex — the decision record's Consequences claimed
`lrh-confirm-fixes` "needs no change," but that conflated its (correct,
deliberate) status-handling deviation with its glob, which still uses the
same unanchored substring match as `lrh-review-response` and doesn't meet
the new trailing-segment invariant either — corrected the claim and
retitled backlog item 5 to cover both skills' glob-anchoring, not just
`lrh-review-response`'s. Codex — the decision record's own Consequences
said this was "the second promoted decision file," contradicting the
already-corrected backlog count of three — fixed to match. Copilot (5x,
low-confidence, all correct) — three ambiguous `lrh-*/SKILL.md` path
references missing the `src/lrh/skills/` prefix (this repo has both
canonical and `.claude/skills/` mirror trees); a subject/verb mismatch in
the bootstrap stub ("`landed`/`in_progress` blocks" read as the status
values being the subject, not a match with that status); and the PR
description being stale (still listed only the original 2 files while the
diff had grown to 8) — fixed the first four inline, and updated the PR
description separately.

While cross-linking, noticed the `/lrh-decision` skill backlog entry
(unrelated to this PR) was stale — written when only one promoted decision
file existed, never updated after `DEC-DELIBERATE-CHAIN-INITIATION.md` was
promoted 2026-07-24. This record is a third data point. Corrected that
entry's status to note its own revisit trigger already fired, since
noticing it in passing was cheap and leaving it silently stale would have
been worse than fixing an unrelated small thing while already in the file.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS` no actionable leaf)
- No skill or CLI *code* touched (only documentation: `PROMPTS.md`,
  `project/executions/README.md`, `project/design/backlog.md`,
  `project/memory/decision_log.md`,
  `project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md`, the
  bootstrap template's `PROMPTS.md` and `project/executions/README.md`
  stubs, and this execution record) — no skill-behavior or CLI test suite
  affected

# Follow-up

- Revisit the CLI-tooling option (option 3) per the decision record's
  revisit conditions, not on a schedule.
- Bring `lrh-review-response`'s idempotence check up to the default (or
  document its own deviation) — tracked as item 5 in the
  "Idempotence-check refinements deferred from PR #438" backlog entry.
- The `/lrh-decision` skill backlog entry now has 3 real data points and
  its deferral trigger has fired — actually revisiting whether to build it
  is separate, unstarted work.
