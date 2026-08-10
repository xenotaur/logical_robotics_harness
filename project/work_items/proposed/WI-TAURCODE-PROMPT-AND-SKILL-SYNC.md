---
resolution: null
blocked_reason: null
blocked: false
id: WI-TAURCODE-PROMPT-AND-SKILL-SYNC
title: Synchronize Taurcode's land/execute prompts and installed LRH skills with the invocation-and-gate reset
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-CROSS-REPO-CODE-HEALTH
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - sync_before_stages_1_and_2_land
acceptance:
  - Taurcode's installed LRH skills are refreshed from LRH main after Stages 1 and 2 land, and no installed copy retains disable-model-invocation or the retrigger commands
  - prompts/taurcode/land.md Step 1's wait-for-automated-review flow is reconciled with the post-reset review model, in which bot review fires only on PR open and every subsequent round is a self-review pass
  - prompts/taurcode/execute.md is reconciled on the same basis
  - Any gate or round-cap language in the Taurcode prompts matches the policy the Stage 3 DEC record establishes, or explicitly documents a deliberate Taurcode-specific divergence
  - A decision is recorded on whether Taurcode should continue vendoring LRH skills at all, given it maintains parallel prompts for the same workflows
  - The Taurcode changes are verified against its installed corpus, not only its source tree
required_evidence:
  - manual_review
artifacts_expected:
  - prompts/taurcode/land.md
  - prompts/taurcode/execute.md
---

# Synchronize Taurcode's land/execute prompts and installed LRH skills with the invocation-and-gate reset

## Summary

Taurcode maintains its own `:land` and `:execute` prompts encoding the same
lifecycle this project is changing, plus vendored copies of thirteen LRH skills.
Both are stale against `PROP-INVOCATION-AND-GATE-RESET`, in two different ways.
Reconcile them after Stages 1 and 2 land — not before, since syncing to a
moving target would need doing twice.

**Paths in this work item are relative to the Taurcode repository**
(`/Users/centaur/Workspace/Taurcode/taurcode`), not to LRH. LRH planning
artifacts do not govern that repository; this item tracks the handoff so it is
not silently dropped, per `PROP-INVOCATION-AND-GATE-RESET`'s resolution to treat
Taurcode as a named handoff rather than folding it into Stage 3's cascade.

## Problem / Context

`DEC-DELIBERATE-CHAIN-INITIATION` names Taurcode's `:land` / `:execute` prompts
as "the human-initiated, single-cycle expression of this policy" — so they carry
the same gate and review model the reset changes. Measured state:

### Defect 1 — the prompts assume bot review is the review mechanism

`prompts/taurcode/land.md` (180 lines) Step 1 is titled "Wait for review to
ACTUALLY land" and reads:

> Automated reviewers post minutes after the PR opens or is pushed, so an empty
> thread list immediately after pushing is **not** proof of a clean review — it
> usually just means the review has not run yet.

That is accurate today and becomes half-wrong after Stage 1. Post-reset, bot
review fires **only** on PR open (repository configuration, which the reset does
not change), and every subsequent round is a `/lrh-self-review` pass — which is
synchronous and has no "posts minutes later" behaviour to wait for. A prompt
that waits for automated reviewers after each push would wait for something that
no longer happens.

`prompts/taurcode/execute.md` (173 lines) carries the same class of assumption;
both files reference gate and review concepts six and seven times respectively.

Notably the prompts contain **no retrigger commands** — verified by grep across
`prompts/`. So Defect 1 is about a stale *model* of how review arrives, not
about Taurcode issuing retriggers.

### Defect 2 — vendored LRH skills are stale

`.claude/skills/` in Taurcode holds thirteen LRH skills, **ten still carrying
`disable-model-invocation`**. Its `lrh-confirm-fixes/SKILL.md` is 373 lines
against LRH's current 674, and its `references/` directory contains only
`confirm-fixes-workflow.md` — no `round-cap-gate.md`. So that copy predates the
round-cap mechanism entirely.

This is a different problem from Defect 1 and has a different fix: Defect 1
needs authoring judgement, Defect 2 needs a reinstall. They are bundled here
because both must land together — refreshing the skills while the prompts still
describe the old review model would leave the two halves disagreeing.

### Why this is sequenced after Stages 1 and 2

Syncing before those stages land means syncing to a target that is still moving,
then syncing again. `forbidden_actions` records this as
`sync_before_stages_1_and_2_land` rather than leaving it to judgement.

### Prior Art Check

**Duplication search**

- In-repo: no work item covers Taurcode. `PROP-INVOCATION-AND-GATE-RESET` names
  Taurcode as a named handoff and explicitly declines to fold it into Stage 3's
  cascade; this work item is that handoff made concrete.
- Sibling repos: Taurcode has its own control plane and may have its own
  planning artifacts for this; **check before starting**, since a Taurcode-side
  item would be the better home and this one should then link rather than
  duplicate.
- External libraries: not applicable.
- Recommendation: Proceed, with the sibling-repo check as a first step.

**Demand search**

- Work items: none in LRH.
- Proposals: `PROP-INVOCATION-AND-GATE-RESET` is the governing design.
- Backlog: no matching entries.
- Recommendation: link the proposal; nothing to close.

## Scope

Taurcode's `prompts/taurcode/land.md` and `prompts/taurcode/execute.md`, and its
vendored `.claude/skills/` LRH copies.

Out of scope: Taurcode's other prompts, its own control-plane schema, and any
LRH-side change — this work item consumes the reset's outcome rather than
altering it.

## Required Changes

1. **Check for a Taurcode-side planning artifact first.** If one exists, link to
   it and scope this item to the LRH-side tracking only.
2. Refresh Taurcode's vendored LRH skills from LRH `main` once Stages 1 and 2
   have landed, and verify against the installed copies rather than the source
   tree — the same verification gap `PROP-INVOCATION-AND-GATE-RESET` records for
   its own stages.
3. Reconcile `land.md` Step 1's wait-for-review flow with the post-reset model:
   bot review on PR open only, self-review for every subsequent round, no
   "posts minutes later" wait after pushes.
4. Reconcile `execute.md` on the same basis.
5. Align any gate, round-cap, or confirmation language with the policy the
   Stage 3 DEC record establishes — or document a deliberate Taurcode-specific
   divergence, explicitly, rather than letting the two drift apart silently.
6. **Record a decision on whether Taurcode should keep vendoring LRH skills at
   all.** It maintains parallel prompts for the same workflows, so the vendored
   copies may be redundant. This is the question this work item is most likely
   to answer in passing, and leaving it unasked guarantees the same drift
   recurs.

## Non-Goals

- Does not change anything in LRH. This item consumes the reset's outcome.
- Does not run before Stages 1 and 2 land.
- Does not rewrite Taurcode's prompts beyond reconciling the review and gate
  model — their structure and voice are Taurcode's own.
- Does not migrate Taurcode's control-plane schema, which is tracked separately.
- Does not assume Taurcode must match LRH exactly; a documented divergence is an
  acceptable outcome, an undocumented one is not.

## Acceptance Criteria

- Taurcode's installed LRH skills are refreshed post-Stages 1 and 2, with no
  installed copy retaining `disable-model-invocation` or retrigger commands.
- `land.md` Step 1 is reconciled with the post-reset review model.
- `execute.md` is reconciled on the same basis.
- Gate and round-cap language matches the Stage 3 DEC policy, or documents a
  deliberate divergence.
- A decision is recorded on continued skill vendoring.
- Changes are verified against Taurcode's installed corpus, not only its source
  tree.

## Validation

- In Taurcode: `grep -rl "disable-model-invocation" .claude/skills/` returns no matches
- In Taurcode: `grep -rlE "add-reviewer @copilot|@codex review" .claude/skills/ prompts/` returns no matches
- Manual: read `land.md` and `execute.md` end to end against the Stage 3 DEC record and confirm no step waits for a review round that no longer occurs
- Manual: drive one Taurcode `:land` run and confirm the review step behaves as the reconciled prompt describes

## Risk Notes

Taurcode was not quiet at the time of writing: `main` had three modified files
and three open PRs. Unlike `velumin` and `replication_vector`, a quiet window
cannot be assumed here and should be confirmed before starting.

The larger risk is scope drift into a general LRH-Taurcode convergence project.
This item reconciles two prompts and one vendored skill tree against one specific
change. The vendoring question in Required Change 6 is deliberately scoped to
*recording a decision*, not to acting on it — acting on it is a separate,
larger piece of work.
