---
resolution: null
blocked_reason: null
blocked: false
id: WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5
title: Activate chain-defaults Stage 3.5 under the Stage 3 compensating control
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
  - WS-LRH-CHAIN-DEFAULTS
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
  - project/design/proposals/adopted/lrh-gate-policy/00_proposal.md
  - project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
depends_on:
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
  - bypass_two_step_consent
  - retrigger_bot_review
acceptance:
  - The Stage 3 DEC's `human_initiated_invocation_evidence` compensating control is present, named, and checked before activation proceeds
  - chain-defaults activation preserves DEC-CHAIN-INIT-SKIP-CONSENT's two-step consent contract: storing the profile default and granting user-local skip consent remain separate affirmative actions
  - skip_if_opted_in is not shipped as the default configuration
  - confirmed_commit and confirmed_at are stamped to the activation commit only after the human live-confirms the activated profile values
  - Any local skip-consent value is bound to the exact activated profile value and can be revoked or invalidated by the existing staleness path
  - The installed Claude and Codex skill corpora are refreshed or verified as not requiring refresh, and the report states that already-running sessions must restart to pick up changes
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/config/chain-defaults.yaml
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/
  - .agents/skills/
---

# Activate chain-defaults Stage 3.5

## Summary

Activate the chain-defaults mechanism only after Stage 3 has produced the
compensating control that proves a `skip_if_opted_in` run was genuinely
human-initiated. This is an activation and verification operation, not a policy
redesign.

## Problem / Context

`PROP-INVOCATION-AND-GATE-RESET` deliberately sequences Stage 3.5 after Stage 3.
The project already has a chain-defaults mechanism, but the proposal found it
dormant and potentially unsafe to activate before the gate policy explains what
replaces the removed chain-runner flags. Stage 3 names that checkable
replacement control as `human_initiated_invocation_evidence`.

The sharp edge is consent. `DEC-CHAIN-INIT-SKIP-CONSENT` requires two separate
affirmative acts: live-confirming the profile values and granting user-local
skip consent bound to those exact values. This work item must preserve that
contract while moving the mechanism from dormant to usable.

### Prior Art Check

**Duplication search.** No existing `WS-INVOCATION-AND-GATE-RESET` work item
activates Stage 3.5. `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` and
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` are mechanism increments owned by
`WS-LRH-CHAIN-DEFAULTS`; they do not perform this activation.

**Demand search.** Demand is explicit in
`WS-INVOCATION-AND-GATE-RESET.exit_criteria` and
`PROP-INVOCATION-AND-GATE-RESET` Decision 8.

**Recommendation.** Proceed only after `WI-GATE-POLICY-CASCADE-STAGE3`
resolves.

## Scope

- Verify `human_initiated_invocation_evidence` exists and is checkable.
- Activate the chain-defaults profile under that control.
- Stamp profile confirmation metadata at the activation commit.
- Refresh or verify installed skill corpora as needed.
- Report restart requirements for in-flight sessions.

## Required Changes

1. Read `DEC-GATE-POLICY-CASCADE` and verify
   `human_initiated_invocation_evidence` is present.
2. Update `project/config/chain-defaults.yaml` only as needed to activate the
   confirmed profile without making `skip_if_opted_in` the shipped default.
3. Preserve the two-step consent path from `DEC-CHAIN-INIT-SKIP-CONSENT`.
4. Re-stamp `confirmed_commit` and `confirmed_at` after live confirmation.
5. Propagate or verify installed skill corpora for the active Claude and Codex
   targets.
6. Record in the execution result that in-flight sessions must restart.

## Non-Goals

- Does not define the Stage 3 compensating control.
- Does not implement Stage 4 fields such as `confirm_fixes_batch` or
  `closeout_with_merge`.
- Does not weaken merge authorization or closeout confirmation policy.
- Does not manually retrigger hosted GitHub review agents.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Activating before Stage 3 resolves would recreate the consent-riding gap this
  workstream exists to avoid.
- Local skip consent is user-local state; report exact commands and values
  rather than implying repository commits alone grant consent.
