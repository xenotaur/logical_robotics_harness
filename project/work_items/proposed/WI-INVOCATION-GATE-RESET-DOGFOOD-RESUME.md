---
resolution: null
blocked_reason: null
blocked: false
id: WI-INVOCATION-GATE-RESET-DOGFOOD-RESUME
title: Dogfood, triage, feed back, and resume normal fleet operation for invocation/gate reset
type: operation
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
  - project/work_items/proposed/WI-TAURCODE-PROMPT-AND-SKILL-SYNC.md
depends_on:
  - WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - retrigger_bot_review
  - resume_fleet_without_recorded_criterion
acceptance:
  - A low-stakes LRH-internal dogfood run exercises the post-reset review and gate flow without hosted review-bot retriggers
  - Related open PRs and live sessions are triaged with go/no-go decisions, including whether each belongs to this workstream, a sibling workstream, or an unrelated sweep
  - Findings are explicitly fed back into Stages 1-4 as follow-up work items, proposal amendments, or recorded no-action decisions
  - Taurcode and other cross-repository handoffs are checked for tracked follow-up rather than silently treated as LRH-owned changes
  - The proposal's resumption criterion is met and recorded before normal fleet operation is resumed
  - PROP-INVOCATION-AND-GATE-RESET metadata is updated to adopted or otherwise records why adoption remains blocked
  - AGENTS.md, CLAUDE.md, STYLE.md, and relevant session memories carry current policy guidance or have explicit no-change evidence
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/executions/
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/workstreams/active/WS-INVOCATION-AND-GATE-RESET.md
  - AGENTS.md
  - CLAUDE.md
  - STYLE.md
---

# Dogfood, triage, feed back, and resume normal fleet operation

## Summary

Complete `PROP-INVOCATION-AND-GATE-RESET` Stages 5-7 after Stage 3.5 activation:
run a low-stakes LRH-internal dogfood pass, triage related open PRs and live
sessions, feed findings back into the staged plan, and record the resumption of
normal fleet operation.

## Problem / Context

The proposal intentionally paused normal fleet operation until the new review
and gate posture was proven on low-stakes LRH work. Stages 1-3.5 change how
agents ask, wait, review, and continue. Those changes need a deliberate
dogfood and resumption record so the project does not simply drift back into
normal operation on an unverified assumption.

### Prior Art Check

**Duplication search.** No existing work item owns the combined Stage 5-7
dogfood, related-PR triage, feedback, and resumption record. `WI-TAURCODE-
PROMPT-AND-SKILL-SYNC` is a named cross-repository handoff, not this LRH
resumption pass.

**Demand search.** Demand is explicit in
`WS-INVOCATION-AND-GATE-RESET.exit_criteria` and
`PROP-INVOCATION-AND-GATE-RESET` Stages 5-7.

**Recommendation.** Proceed after Stage 3.5 activation. Keep any discovered
implementation defects as follow-up work items unless they are small, directly
blocking corrections to the resumption record.

## Scope

- Low-stakes LRH-internal dogfood run.
- Related open PR and live-session triage.
- Feedback into Stages 1-4.
- Fleet-resumption criterion and record.
- Final proposal/workstream metadata cleanup.
- Guidance and memory policy synchronization.

## Required Changes

1. Select and run a low-stakes LRH-internal dogfood task through the post-reset
   flow.
2. Triage related open PRs and live sessions with go/no-go decisions grounded in
   actual repository state.
3. Record findings as follow-up work items, proposal amendments, or no-action
   decisions.
4. Check cross-repository handoffs, including Taurcode, for tracked ownership.
5. Record the resumption criterion and whether it is met.
6. Update `PROP-INVOCATION-AND-GATE-RESET` and
   `WS-INVOCATION-AND-GATE-RESET` toward adoption/resolution or record the
   remaining blocker.
7. Synchronize guidance docs and relevant session memories with the final
   policy state.

## Non-Goals

- Does not implement Stage 3 or Stage 3.5.
- Does not directly edit sibling repositories.
- Does not manually retrigger hosted GitHub review agents.
- Does not close unrelated stale PRs without separate human direction.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- A dogfood run can surface real defects. Keep the resumption pass honest:
  record blockers rather than declaring the fleet resumed because most pieces
  landed.
- Open PR triage can sprawl. Limit the pass to PRs and sessions related to the
  invocation/gate reset unless the user explicitly broadens scope.
