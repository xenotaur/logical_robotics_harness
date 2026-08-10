---
resolution: null
blocked_reason: null
blocked: false
id: WI-FRONT-OF-RUN-GATE-COLLAPSE
title: Collapse the front-of-run gate pair into one fully-specified /lrh-execute gate
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-INVOCATION-AND-GATE-RESET
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
depends_on:
  - WI-DELIBERATE-MODEL-INVOCATION
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - activate_skip_if_opted_in
  - weaken_merge_authorization
acceptance:
  - A single /lrh-execute gate presents the completion and stop-work conditions together with the plan, prompt ID, branch name, expected file changes, validation commands, and any readiness or prior-art warning, before any of those is asked for separately
  - /lrh-implement Step 4, when reached through /lrh-execute, fires only on material divergence from the approved run plan; an unchanged plan produces no second ask
  - lrh-execute/SKILL.md's does-not-exempt clause and its corresponding Quality Checklist item are rewritten to match the new behaviour rather than left contradicting it
  - The amending DEC record carries both ends of the run -- Decision 7's merge/closeout collapse and Decision 11's front-of-run collapse -- and states explicitly that this is a single-ask change, not a no-ask change
  - /lrh-execute Step 1 runs a readiness check for a WI-ID input, closing the ordering defect where readiness is first evaluated after the chain has already been authorized
  - The collapse does not extend to /lrh-implement invoked on a free-form description, where the plan is not derivable from a static file
  - lrh skills install is run and the collapsed gate is verified present in the installed corpus at ~/.claude/skills/, not only in the source tree
  - lrh validate reports 0 errors and diff -r reports no differences between src/lrh/skills/ and .claude/skills/ for every affected skill
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-execute/SKILL.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - .claude/skills/lrh-execute/SKILL.md
  - .claude/skills/lrh-implement/SKILL.md
  - project/memory/decisions/
---

# Collapse the front-of-run gate pair into one fully-specified /lrh-execute gate

## Summary

Implement `PROP-INVOCATION-AND-GATE-RESET` Decision 11 under Stage 3: hoist
`/lrh-implement`'s deterministic Steps 1-3 ahead of `/lrh-execute`'s Step 2
chain-authorization gate, so one gate carries the conditions *and* the plan;
and make `/lrh-implement`'s Step 4 gate fire only when the plan has materially
diverged from what was approved. Decision 7 already collapsed the merge/closeout
pair at the back of the run; this is the same shape applied to the front.

## Problem / Context

A `/lrh-execute` run authorizes the chain at `/lrh-execute` Step 2
(`src/lrh/skills/lrh-execute/SKILL.md:138-177`), runs four deterministic steps,
then blocks on `/lrh-implement` Step 4
(`src/lrh/skills/lrh-implement/SKILL.md:145-157`). A human who reads the first
gate as *the* gate -- a reasonable reading, since it presents the whole planned
chain -- can step away and return to find the run idle. That happened on
2026-08-10 on a deadline, costing roughly two hours of wall-clock.

The second gate is a restatement, not a decision point. Every field it displays
is derivable before the first gate fires: task summary, expected file changes,
and validation commands come from the work item's own static sections; the
prompt ID needs only the WI-ID; the branch name needs `gh api user` plus the
WI's `type`; readiness warnings come from `lrh work-items readiness`. Of the
four intervening steps, only the prior-art check
(`src/lrh/skills/lrh-implement/SKILL.md:95-115`) can yield genuinely new
information, and only when the work item lacks a check of its own. Two others
are stops, not questions — the readiness check (Step 1) and the idempotence
check (Step 3) — and the fourth, reading the work item (Step 2), only
summarizes a static file.

This is not a lapse in the skill. `/lrh-execute` requires it
(`SKILL.md:179-181`, with a Quality Checklist item at `:286` making a bypass a
defect), implementing `DEC-DELIBERATE-CHAIN-INITIATION` principle 1 (`:75-76`):
"chain initiation never satisfies a skill's own internal confirmation gate."
Fixing the behaviour therefore requires amending the rule, not just the skill.

### Prior-art check

**Duplication search -- no duplicate; one adjacent item with a real collision
surface.** `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` collapses the *back* of the run
(`closeout_with_merge`) and redesigns the staleness watch; it is owned by
`WS-LRH-CHAIN-DEFAULTS` and does not touch the front-of-run pair.
`WI-DELIBERATE-MODEL-INVOCATION` resolves flag-vs-guidance, CHAIN-NOTE
placement, and record-less PRs -- a different axis. Neither covers this. The
collision to manage is that both this item and Increment 3 may want a
chain-defaults profile field for their respective collapses; they should agree
on one schema rather than adding two unrelated fields.

**Demand search -- demand exists and is recorded.**
`PROP-INVOCATION-AND-GATE-RESET` Background section 3 names this as the fourth
symptom of confirmation fatigue, and Decision 11 records the chosen option. This
work item is that decision's implementation, not a fresh request.

### Why activating the defaults mechanism is not the fix

`chain_init_confirmation: skip_if_opted_in` is scoped to the chain gate's
*conditions* (`src/lrh/skills/_shared/chain-defaults.md:70-82`);
`/lrh-implement` Step 4 is untouched by it. Applied to the motivating incident,
skip mode would have skipped the gate the human answered and left the one that
blocked them. Stage 3.5 owns activation and is unaffected by this item; this
item must not activate it.

## Scope

In scope: `/lrh-execute`'s Step 1 and Step 2, `/lrh-implement`'s Steps 1-4 as
reached through `/lrh-execute`, the two `.claude/skills/` mirrors, the amending
decision record, and the interim label-only patch.

Out of scope: `/lrh-implement` invoked directly on a free-form description
(`src/lrh/skills/lrh-implement/SKILL.md:92-93`), where forming a plan requires
reading the codebase and the gate is a genuine decision point; `/lrh-land`'s own
gates; and activation of `skip_if_opted_in`.

## Required Changes

1. **Interim patch first (Decision 11 option A).** Add one sentence to
   `/lrh-execute` Step 2's presentation naming what will still be asked and
   roughly when. This ships ahead of the structural change, costs no policy
   amendment, and makes the current trap legible if the rest slips.
2. **Hoist.** Move `/lrh-implement` Steps 1, 1.5, 2, and 3 to run before
   `/lrh-execute` Step 2, and fold their outputs into that gate's presentation.
3. **Close the readiness ordering defect.** Add a readiness check to
   `/lrh-execute` Step 1's WI-ID branch, which has none today (verified: zero
   occurrences of "readiness" in `SKILL.md:79-91`).
4. **Divergence-only second gate.** Define the approved run plan as a structured
   object and have `/lrh-implement` Step 4 compare against it, asking only on
   material divergence. Define "material" mechanically -- a diff against the
   approved object -- rather than leaving it to agent judgement.
5. **Rewrite the contradicting text.** `lrh-execute/SKILL.md:179-181` and the
   Quality Checklist item at `:286`.
6. **Amend the decision record.** One DEC record covering both Decision 7 and
   Decision 11, stating explicitly that both are single-ask, not no-ask.
7. **Propagate.** Run `lrh skills install` and verify against
   `~/.claude/skills/`, per the proposal's Implementation Plan.

## Non-Goals

- Does not activate `chain_init_confirmation: skip_if_opted_in` -- Stage 3.5.
- Does not change merge authorization; `DEC-AGENT-EXECUTED-MERGE-GATE` stands.
- Does not remove any gate. The human approves more at the surviving gate than
  they do today, in one reply instead of two.
- Does not add a timeout-and-proceed path on any gate.
- Does not restructure `/lrh-land`'s gates beyond what Decision 7 already
  specifies.

## Acceptance Criteria

Consult the `acceptance:` frontmatter field, which is the authoritative list.

## Validation

- lrh validate
- scripts/test
- diff -r src/lrh/skills/lrh-execute .claude/skills/lrh-execute
- diff -r src/lrh/skills/lrh-implement .claude/skills/lrh-implement
- grep -rl "does not exempt" ~/.claude/skills/lrh-execute/ (expect no match after propagation)
- A dogfood /lrh-execute run on a low-stakes work item, confirming exactly one front-of-run ask

## Risk Notes

**Sequencing.** This is Stage 3 work and the proposal's Implementation Plan
makes Stages 1 to 3 strictly sequential. `depends_on` carries that constraint
rather than prose, so a chain runner cannot start this before Stage 2's scope
is resolved.

**Schema collision with Increment 3.** Both this item and
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` may introduce a chain-defaults profile field
for a gate collapse. Agree on one schema across both before either lands.

**The mechanical-divergence definition is the load-bearing part.** If "material
divergence" ends up agent-judged, this reintroduces the self-grading problem the
structured run plan exists to avoid. A change to a validation command or an
added file must count; reformatting must not.

**Propagation, not merge, is what changes behaviour.** Landing on `main` leaves
every session running the stale installed corpus. The acceptance criteria
require verification against `~/.claude/skills/` for this reason.

**The workstream-body duplication convention needs one answer, not two.**
`src/lrh/skills/lrh-workstream/references/workstream-body-guide.md:96` says a
workstream's `## Exit Criteria` body section "mirrors and expands" the
`exit_criteria:` frontmatter list, and `lrh-workstream/SKILL.md:107-109`
instructs authors to produce both. Practice already diverges: five workstreams
across every bucket carry a populated `exit_criteria:` with no body restatement
(`WS-EXECUTION-FRAMEWORK`, `WS-CI-CAPABILITY-SCAFFOLDING`, `WS-LRH-ASSISTANTS`,
`WS-PRIOR-ART-CHECK`, `WS-SKILLS`), and `WS-INVOCATION-AND-GATE-RESET` replaced
its body copy with a pointer after the duplication drifted twice. Decide the
convention and make the skill say it, rather than leaving authors to choose per
file. Related but distinct from the
`## Acceptance Criteria` case in this work item, which already points at
frontmatter and relies on `parse_work_item_markdown`'s documented fallback.
