---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CHAIN-DEFAULTS-INCREMENT-3
title: Implement Increment 3 of PROP-LRH-CHAIN-DEFAULTS -- policy-derived profile fields and a semantic staleness watch
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
  - WS-LRH-CHAIN-DEFAULTS
related_design:
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on:
  - WI-LRH-CHAIN-DEFAULTS-INCREMENT-1
  - WI-GATE-POLICY-CASCADE-STAGE3
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - ship_skip_if_opted_in_as_default
acceptance:
  - The closeout_with_merge profile field is implemented so /lrh-land presents the merge command and the closeout plan in one ask, with closeout still executed after merge
  - Post-merge divergence is surfaced as an alert about a new condition, never as a re-ask of the same question the human already answered
  - The staleness check watches gate definitions semantically rather than whole files, closing both the over-watch and under-watch defects documented in PROP-INVOCATION-AND-GATE-RESET Decision 9
  - The staleness check covers the gate-bearing skills /lrh-land inlines -- /lrh-confirm-fixes, /lrh-review-response, /lrh-closeout -- which the current file list omits
  - chain_init_confirmation is not shipped as skip_if_opted_in, preserving DEC-CHAIN-INIT-SKIP-CONSENT's two-step human consent requirement
  - New Python carries unit tests
  - lrh validate reports 0 errors
  - diff -r between src/lrh/skills/ and .claude/skills/ reports no differences for every affected skill
required_evidence:
  - manual_review
  - lrh_validate
  - test_new_python
artifacts_expected:
  - project/config/chain-defaults.yaml
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - src/lrh/skills/lrh-closeout/SKILL.md
---

# Implement Increment 3 of `PROP-LRH-CHAIN-DEFAULTS` -- policy-derived profile fields and a semantic staleness watch

This item depends on `WI-GATE-POLICY-CASCADE-STAGE3` because Stage 3 must
produce the DEC record that narrows `PROP-LRH-CHAIN-DEFAULTS` Decision 3 before
`closeout_with_merge` can be implemented without contradicting a governing
document.

## Summary

Extend the chain-defaults mechanism with the profile fields the gate policy
requires, and repair the staleness check that decides when stored consent is
still valid. Two concrete deliverables: a `closeout_with_merge` field that
collapses the redundant "merge it?" / "close it out?" pair into one ask, and a
semantic redesign of the Decision 5 staleness watch, which measurement showed is
wrong in both directions.

## Problem / Context

`PROP-INVOCATION-AND-GATE-RESET` identifies two defects that belong to the
chain-defaults mechanism rather than to the invocation reset, and therefore to
this workstream rather than `WS-INVOCATION-AND-GATE-RESET`.

### Defect 1 — the merge and closeout questions are one question asked twice

`/lrh-land` Step 6 requires a live merge authorization, and Step 7 then inlines
`/lrh-closeout`, whose own Step 4 plan-confirm gate requires a **second**
separate reply before touching any files. Both are needed today; neither is
redundant on its own terms.

They are nonetheless the same question. `project/config/chain-defaults.yaml`'s
own steelmanned completion condition defines done as a single unit — *"PR
merged, its execution records landed, and any linked work item resolved"* — and
`/lrh-land` Step 7 is an unconditional chain step, not a branch point. A chain
that merges without closing out has not met its completion condition; it is
unfinished, not awaiting a fresh decision.

The cost is not only friction. A human who answers what they believe is the
final question and steps away returns to find the run paused on a second,
essentially identical one.

### Defect 2 — the staleness watch is wrong in both directions

`_shared/chain-defaults.md`'s Decision 5 check watches four files:

```
src/lrh/skills/lrh-land/SKILL.md
src/lrh/skills/lrh-land/references/land-workflow.md
src/lrh/skills/lrh-execute/SKILL.md
src/lrh/skills/_shared/chain-defaults.md
```

- **Over-watch.** The list is file-granular, so a typo fix in
  `lrh-land/SKILL.md` invalidates stored consent identically to a gate
  redesign — making the mechanism self-defeating during exactly the periods of
  active skill development when it is most needed.
- **Under-watch.** `/lrh-land` inlines `/lrh-confirm-fixes`,
  `/lrh-review-response`, and `/lrh-closeout` — all gate-bearing — and **none**
  is watched. Verified by inspection. A real gate change in any of them,
  including this work item's own `closeout_with_merge` behavior, would not
  invalidate consent even though it materially changes what the human consented
  to.

### Why this belongs to `WS-LRH-CHAIN-DEFAULTS`

Both defects are properties of the defaults mechanism `WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`
shipped. `WS-LRH-CHAIN-DEFAULTS` already owns
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`; placing Increment 3 alongside it keeps
mechanism work in one place. `WS-INVOCATION-AND-GATE-RESET` supplies the policy
these fields encode but does not own them, avoiding duplicate ownership.

### Prior Art Check

**Duplication search**

- In-repo: No existing work item implements `closeout_with_merge` or revises the
  staleness check. `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` is the sibling increment
  covering `confirm_fixes_batch` — adjacent, not overlapping.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

**Demand search**

- Work items: `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` is the sibling; no work item
  requests this scope.
- Proposals: `PROP-LRH-CHAIN-DEFAULTS` is the governing design;
  `PROP-INVOCATION-AND-GATE-RESET` Decisions 7 and 9 specify these two changes.
- Backlog: No matching entries.
- Recommendation: No action; both proposals are the demand.

## Scope

The `closeout_with_merge` profile field and its `/lrh-land` and `/lrh-closeout`
integration, plus the Decision 5 staleness check in
`_shared/chain-defaults.md` and its inlined copies.

Out of scope: `confirm_fixes_batch` (Increment 2), `chain_init_confirmation`'s
consent contract (unchanged), and activation of the mechanism itself, which is
`WS-INVOCATION-AND-GATE-RESET` Stage 3.5.

## Required Changes

1. Add a `closeout_with_merge` field to the chain-defaults profile, reusing
   Increment 1's existing storage, staleness, and override mechanics rather than
   duplicating them.
2. Implement the single-ask flow in `/lrh-land`: present the SHA-locked merge
   command together with the computed closeout plan, take one live
   authorization, execute the merge, verify the PR actually reached `MERGED`,
   then execute the previewed closeout without a second ask.
3. Fold `/lrh-closeout` Step 4's two human-judgement inputs into that single
   presentation — the WI `resolution:` text and the WS exit-criteria
   confirmation. The exit-criteria list must be **displayed**, not inferred; a
   workstream must never close on an assumption.
4. Handle post-merge divergence as an alert, not a re-ask. Where the actual
   merge commit differs from what was anticipated, read and use the real value;
   reserve human contact for genuine failure states.
5. Replace the file-granular staleness watch with a semantic gate-definition
   watch covering the inlined gate-bearing skills, per Defect 2.
6. Mirror every `src/lrh/skills/` change into `.claude/skills/` exactly.

## Non-Goals

- Does not implement autopilot for the closeout gate. This is ask-once, not
  ask-never; `PROP-LRH-CHAIN-DEFAULTS` Decision 3's categorical exclusion of
  `/lrh-closeout` from the autopilot tier is narrowed in form, not abandoned,
  and that narrowing requires the DEC record from
  `WS-INVOCATION-AND-GATE-RESET` Stage 3 to land first.
- Does not commit closeout content to the PR branch before merge. Execution
  records cite the merge commit, and that value would have to be baked into file
  content *inside the branch being merged* — a write that necessarily precedes
  the value's existence. Pushing to the PR branch would also break the
  `--match-head-commit` SHA lock by design.

  **This does not mean the single-ask plan cannot be shown before the merge.**
  The plan the human approves carries a placeholder where the SHA goes, which is
  fine: the write happens after the merge, when the value can be read, and the
  SHA is not a decision variable — it is a mechanical consequence of the merge
  being authorized, not something anyone chooses or reviews. The constraint is
  on *committing* an unknown value, not on *displaying* a plan that will later
  contain a known one.
- Does not weaken merge authorization under `DEC-AGENT-EXECUTED-MERGE-GATE`.
- Does not change `chain_init_confirmation` or ship `skip_if_opted_in` as a
  default.
- Does not implement `confirm_fixes_batch` — that is Increment 2.

## Acceptance Criteria

- `closeout_with_merge` is implemented; `/lrh-land` presents merge and closeout
  in one ask, with closeout still executed after merge.
- Post-merge divergence surfaces as an alert about a new condition, never as a
  re-ask of the question already answered.
- The staleness check watches gate definitions semantically, closing both the
  over-watch and under-watch defects.
- The staleness check covers `/lrh-confirm-fixes`, `/lrh-review-response`, and
  `/lrh-closeout`.
- `chain_init_confirmation` is not shipped as `skip_if_opted_in`.
- New Python carries unit tests.
- `lrh validate` reports 0 errors.
- `diff -r` between `src/lrh/skills/` and `.claude/skills/` reports no
  differences for every affected skill.

## Validation

- `lrh validate`
- Unit tests for the staleness predicate, covering a typo-only edit (must not invalidate) and a gate-definition edit in an inlined skill (must invalidate)
- `for d in lrh-land lrh-closeout; do diff -r "src/lrh/skills/$d" ".claude/skills/$d"; done`
- Manual: drive one PR through `/lrh-land` and confirm exactly one live authorization is requested for merge plus closeout
- Manual: drive one PR where the WS exit criteria are not met, and confirm the criteria are displayed and the workstream is not closed

## Risk Notes

The primary risk is that the single-ask presentation becomes dense enough to
recreate the friction it removes — merge command, execution-record changes, WI
resolution text, and WS exit criteria all in one prompt. A wall of text that
gets skimmed is the same failure as a prompt asked so often it gets
rubber-stamped. The presentation needs deliberate layout, and reviewers should
judge it on whether a human can actually act on it in one pass.

Second, this work item depends on a governance change it does not itself make:
narrowing `PROP-LRH-CHAIN-DEFAULTS` Decision 3 requires the DEC record from
`WS-INVOCATION-AND-GATE-RESET` Stage 3. Implementing the field before that
record lands would leave the codebase contradicting its own governing document —
the exact drift this project has already caught and corrected once.
