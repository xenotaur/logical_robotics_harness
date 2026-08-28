---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-NEXT-STEP-REPORTING
title: Decide and implement a fix for agents suggesting downstream implementation while a WI/proposal/workstream's filing PR is unmerged
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "A documented decision matrix exists (options considered, pros/cons grounded in repo state with file:line citations, and a stated rationale for the chosen option) BEFORE any implementation commit -- this is a first-class deliverable of this WI, not a prerequisite done elsewhere and merely cited"
  - "The decision matrix explicitly includes, and does not foreclose, a mechanical CLI-computed next-step option (a command that determines the correct next action from live repo/PR state, which a skill or agent calls and reports verbatim) alongside lighter-weight options such as an AGENTS.md rule cited from each affected skill's reporting step"
  - "The chosen option is actually implemented and demonstrably fixes the failure mode: an agent must not name a work item's, proposal's, or workstream's downstream implementation action (/lrh-implement, /lrh-execute, or similar) as a 'next step' while that item's own filing PR is open and unmerged"
  - "PR #602 (`Document and enforce WI-creation-PR-merge ordering before /lrh-implement`, merged 2026-08-28) is read and explicitly accounted for in the decision matrix as related prior art -- it fixed a downstream execution-safety consequence of the same root confusion (silently dropping the WI file if /lrh-implement runs before its filing PR merges), not the reporting-accuracy problem itself; the matrix must state why it does or doesn't change the chosen approach"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - a decision-matrix write-up (location TBD by the executing session -- e.g. project/design/ or the execution record body)
  - AGENTS.md and/or new src/lrh/*.py CLI module, depending on which option the matrix selects
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-work-remains/SKILL.md
---

# Decide and implement a fix for agents suggesting downstream implementation while a WI/proposal/workstream's filing PR is unmerged

## Summary

Fixes a recurring, user-flagged reporting failure: an agent names a work
item's, proposal's, or workstream's downstream implementation action
(`/lrh-implement`, `/lrh-execute`, etc.) as a "next step" while that
item's own filing PR is still open and unmerged. Unlike a prior draft of
this work item, this one does **not** pre-select the fix. Its first
deliverable is a fresh, repo-grounded decision matrix across all
candidate fixes -- explicitly including a mechanical CLI-computed
next-step option, not just a documentation-level rule -- with
implementation following whichever option that matrix selects.

## Problem / Context

A session repeatedly reported `/lrh-implement`/`/lrh-execute <WI-ID>` as a
"next step" immediately after filing a WI, while its own filing PR sat
open and unreviewed -- despite the correct sequencing already being
documented in `/lrh-work-item`'s own reference doc
(`lrh-work-item-workflow.md:99-123`, "Path 1 -- PR lifecycle" vs. Path 2,
which states plainly that merging does not resolve the work item). The
failure wasn't missing information -- it was paraphrasing past that
material in a later, unstructured "what's next" answer, disconnected from
the skill invocation that had the details loaded.

This is structural, not a one-off: `/lrh-proposal` (`SKILL.md:373-380`)
and `/lrh-workstream` (`SKILL.md:357-364`) have the identical "Report to
the user -> Suggested next steps" terminal shape as `/lrh-work-item`.
`/lrh-work-remains` -- whose entire purpose is preventing exactly this
class of conversational-recall drift -- has the same gap in its own Step
4 ("state the single most logical next step",
`lrh-work-remains/SKILL.md:92-96`), with no rule connecting checklist
item 5 ("Open PRs not yet merged") to item 14 ("Open work items") when
both are true for the same item (`remains-checklist.md:9-25`).

**Related prior art, already landed, does not obviate this work:** PR #602
(merged 2026-08-28, `Document and enforce WI-creation-PR-merge ordering
before /lrh-implement`) fixed a *mechanical execution-safety* consequence
of the same root confusion -- if `/lrh-implement` is actually run before
its WI's filing PR merges, the WI file previously got silently dropped
from the implementation branch; PR #602 added a re-check in
`/lrh-implement` Step 5 to stop/warn instead. It touched only
`lrh-implement/SKILL.md`, `lrh-implement/references/lrh-implement-
workflow.md`, and `lrh-work-item/references/lrh-work-item-workflow.md`
(`gh pr view 602 --json files`) -- it never touched `AGENTS.md`,
`lrh-work-item/SKILL.md`'s own Step 11 reporting text, `lrh-proposal`,
`lrh-workstream`, or `lrh-work-remains`. It is a downstream safety net if
someone acts on a bad suggestion; it does not stop the bad suggestion
itself. This work item must read PR #602 and its execution records
(`project/executions/AD_HOC/2026_08_22_20_24_16_LRH_WORK_ITEM_ORDERING_
DEP_78BA8C_REVIEW.md`, `..._CONFIRM.md`) before proposing a fix, to avoid
duplicating or contradicting it.

### Prior Art Check

**Duplication search.** `git grep -liE "next-step-reporting|next step reporting" --
project/work_items project/design/backlog.md project/design/proposals`
returned no matches at filing time. **The executing session must re-run
this search** -- given the pace of concurrent sessions in this repo, a
match may have landed since.

**Demand search.** A user-flagged, recurring reporting mistake, analyzed
across two conversational passes (the second explicitly rejecting the
first's premature Non-Goals/Risk-Notes closure of the CLI-oracle option)
is the demand. A parallel backlog entry was added alongside this WI's
filing so the gap isn't lost if this WI isn't picked up immediately.

## Scope

- Produce a decision matrix, grounded in actual repo state with
  `file:line` citations (or reputable external sources where the
  question isn't repo-specific), covering at minimum:
  - A documentation-only fix: a rule in `AGENTS.md` (matching its
    existing convention of centralizing cross-cutting policy, e.g. its
    "Pull requests and merge authority" section at `AGENTS.md:142-155`),
    cited from each affected skill's own next-step-reporting step.
  - A mechanical CLI-computed fix: a command that determines the correct
    next action from live state (PR open/merged, WI/proposal/workstream
    status, execution record status) which a skill or agent must call and
    report verbatim, in the same architectural style this repo already
    uses for other gate-relevant computations (`gate_staleness.py` /
    `lrh chain-defaults check-staleness`, `confirm_fixes_batch.py` /
    `lrh confirm-fixes check-batch-routine`, `chain_defaults_status.py` /
    `lrh chain-defaults status`).
  - Any hybrid or other option the executing session identifies.
  - For each option: pros, cons, and whether it has a decisive advantage
    or disqualifying limitation, per this project's own established
    decision-matrix format (see recent examples in this repo's design
    history for the expected rigor).
- Implement whichever option the matrix selects, including mirroring any
  skill-text changes to `.claude/`, `.agents/` (installer), `.gemini/`
  (installer) per the established mirroring convention.

## Required Changes

1. Read PR #602 and its execution records in full before doing anything
   else.
2. Re-run the duplication/demand prior-art search against current `main`.
3. Produce and record the decision matrix (location is the executing
   session's call -- e.g. a `project/design/` note, or directly in this
   WI's own execution record body -- but it must exist as a readable
   artifact before implementation commits land).
4. Implement the selected option.
5. If the selected option touches any `SKILL.md` file, mirror it to
   `.claude/`, `.agents/`, `.gemini/`.

## Non-Goals

- Does not pre-select the fix -- see Summary. Any prior draft of this
  work item that closed off the CLI-oracle option in its own Non-Goals or
  Risk Notes should be treated as superseded by this version.
- Does not retroactively correct any already-completed session's reports.
- Does not change any skill's actual gate/confirm behavior beyond what's
  needed to report the correct next step (e.g. this is not a general
  license to redesign `/lrh-work-item`, `/lrh-proposal`, `/lrh-workstream`,
  or `/lrh-work-remains`).

## Acceptance Criteria

- A decision matrix exists as a readable artifact, grounded with
  `file:line` citations, covering at minimum the AGENTS.md-rule option and
  the CLI-computed-oracle option, with a stated rationale for whichever
  is chosen.
- PR #602 is read and explicitly accounted for in that matrix.
- The chosen option is implemented and fixes the described failure mode.
- `lrh validate` reports 0 errors.

## Validation

- lrh validate
- Manual review: the decision matrix is legible to someone with no prior
  context on this conversation, and the implementation matches what the
  matrix selected

## Risk Notes

The main risk is treating this WI's own Non-Goals/Scope as pre-deciding
the outcome a second time -- the whole point of this version is that the
executing session re-derives the decision from repo-grounded first
principles rather than inheriting a prior conversation's conclusion
un-examined. If the executing session finds itself skipping straight to
implementing the AGENTS.md-rule option without seriously evaluating the
CLI-computed alternative, that is a sign this WI's own instructions were
not followed.
