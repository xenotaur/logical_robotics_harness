---
resolution: Implemented and merged in PR #577 (commit 194d0262e660d91297c7ff8b4c59b761218aefa1)
blocked_reason: null
blocked: false
id: WI-GATE-POLICY-CASCADE-STAGE3
title: Deliver PROP-INVOCATION-AND-GATE-RESET Stage 3 gate policy audit, DEC, and cascade
type: deliverable
status: resolved
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
  - project/design/proposals/adopted/lrh-gate-policy/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-AGENT-EXECUTED-MERGE-GATE.md
  - project/memory/decisions/DEC-SINGLE-ASK-RUN-GATES.md
  - project/memory/decisions/DEC-SELF-REVIEW-RECURSION-GUARD.md
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
depends_on:
  - WI-RETRIGGER-REMOVAL-STAGE1
  - WI-DELIBERATE-MODEL-INVOCATION
  - WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL
  - WI-FRONT-OF-RUN-GATE-COLLAPSE
  - WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - activate_skip_if_opted_in
  - weaken_merge_authorization
  - retrigger_bot_review
acceptance:
  - A gate corpus audit artifact inventories the gate-bearing LRH skill, guidance, decision, proposal, and memory statements that govern human confirmation, review substitution, and chain continuation
  - A gate policy proposal is written or adopted that states the canonical policy replacing the accreted gate prose, including Decision 7's merge/closeout shape, Decision 9's staleness-watch shape, and Decision 11's front-of-run shape
  - A DEC record names exactly which prior statements it supersedes, carries the extended statement-shaped cascade taxonomy from PROP-INVOCATION-AND-GATE-RESET Decision 6, and includes the named Stage 3.5 compensating control
  - The four known stale ownership claims are corrected in WS-SKILLS-EXECUTE.md lines 77, 114, and 133 and WI-SKILLS-LRH-EXECUTE.md line 70, or the artifact has moved and the replacement locations are cited
  - The cascade updates affected LRH skills, guidance docs, and project memory without changing cross-repository files directly
  - Any required cross-repository memory or Taurcode correction is recorded as a named handoff rather than silently folded into LRH-owned implementation scope
  - The work leaves Stage 3.5 activation explicitly blocked unless the compensating control is present and checkable
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/audits/gates/gate-corpus-audit-2026-08-20.md
  - project/design/proposals/adopted/lrh-gate-policy/00_proposal.md
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
  - project/workstreams/
  - project/work_items/
  - src/lrh/skills/
  - .claude/skills/
  - .agents/skills/
---

# Deliver Stage 3 gate policy audit, DEC, and cascade

## Summary

Deliver `PROP-INVOCATION-AND-GATE-RESET` Stage 3 without activating the
chain-defaults skip path. The work audits the existing gate corpus, records the
canonical replacement policy, writes the DEC that names superseded statements
and the Stage 3.5 compensating control, and cascades those decisions through
the LRH-owned skill and planning corpus.

## Problem / Context

Stages 1 and 2 removed the urgent cost and invocation blockers, and
`WI-FRONT-OF-RUN-GATE-COLLAPSE` landed Decision 11's front-of-run shape. Those
changes intentionally used narrow interim mechanisms. The proposal's root-cause
fix is still Stage 3: replace the accreted, partly contradictory gate prose with
one auditable policy and a precise cascade.

The workstream cannot safely proceed to Stage 3.5 while this remains implicit.
`skip_if_opted_in` needs a named compensating control that establishes a run was
genuinely human-initiated after the chain-runner flags are removed. A statement
that the condition is met is not enough; the control must be checkable.

### Prior Art Check

**Duplication search.** No existing work item owns the Stage 3 gate corpus audit,
policy proposal, superseding DEC, and cascade as one executable deliverable.
`WI-FRONT-OF-RUN-GATE-COLLAPSE` implemented one Stage 3 decision but did not
audit or replace the full gate corpus. `WI-GATE-CONFIRM-RENDERING` is adjacent
platform-rendering work and explicitly avoids changing gate cardinality or
consent policy.

**Demand search.** Demand is explicit in
`WS-INVOCATION-AND-GATE-RESET.exit_criteria` and
`PROP-INVOCATION-AND-GATE-RESET` Decisions 6, 7, 9, and 11. The proposal also
names four stale ownership claims and requires a Stage 3.5 compensating control.

**Recommendation.** Proceed as the next executable leaf. Keep Stage 3.5
activation and Stages 5-7 out of this PR.

## Scope

- Gate corpus audit.
- Gate policy proposal or adoption update.
- Superseding DEC record, including the statement-shaped cascade taxonomy.
- Named, checkable Stage 3.5 compensating control.
- LRH-owned cascade through skills, guidance, workstream/work-item text, and
  memory records.

## Required Changes

1. Inventory gate-bearing statements in LRH-owned skill, guidance, decision,
   proposal, workstream, work-item, and memory artifacts using tracked-file
   searches for any counts or committed claims.
2. Write the audit artifact that distinguishes current policy, superseded
   policy, provisional Stage 1/2 mechanisms, and follow-up handoffs.
3. Write or adopt the policy proposal that defines the canonical gate model.
4. Write the DEC record that names superseded statements and carries the
   extended cascade taxonomy.
5. Define the Stage 3.5 compensating control in that DEC as a named, checkable
   mechanism.
6. Apply the cascade to LRH-owned skill corpora and planning artifacts.
7. Record any cross-repository or live-session memory corrections as handoffs.

## Non-Goals

- Does not activate `chain_init_confirmation: skip_if_opted_in`.
- Does not implement Stage 4 `confirm_fixes_batch` or Increment 3 fields owned
  by `WS-LRH-CHAIN-DEFAULTS`.
- Does not manually retrigger hosted GitHub review agents.
- Does not edit Taurcode directly; that repository is tracked by its own
  handoff work item.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- For any committed count or corpus claim, cite the exact `git grep` command
  used to derive it.

## Risk Notes

- The audit/cascade can grow quickly. Keep one PR scoped to Stage 3 and avoid
  folding in Stage 3.5 activation.
- Some stale statements may live in resolved artifacts. Prefer explicit
  supersession/cascade notes over rewriting historical execution records.
- Existing installed sessions keep the skill copy loaded at start; any
  propagation report must remind humans to restart live sessions.
