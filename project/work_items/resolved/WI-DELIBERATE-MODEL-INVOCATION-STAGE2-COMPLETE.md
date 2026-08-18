---
resolution: "Implemented and merged in PR #560 (commit 916012d0ff251347d0ba1f66df8fbd01545922b3)"
blocked_reason: null
blocked: false
id: WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE
title: Complete Stage 2 retained-flag removal and invocation-policy propagation
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
  - project/work_items/resolved/WI-DELIBERATE-MODEL-INVOCATION.md
depends_on:
  - WI-DELIBERATE-MODEL-INVOCATION
  - WI-RETRIGGER-REMOVAL-STAGE1
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - activate_skip_if_opted_in
  - retrigger_bot_review
acceptance:
  - The retained Stage 2 disable-model-invocation flags on lrh-self-review, lrh-confirm-fixes, lrh-land, and lrh-execute are removed only after their gate gaps are closed or explicitly reassigned by a recorded decision
  - Each affected skill has when_to_use guidance or an equivalent target-rendered policy that narrows invocation surface without relying on disable-model-invocation
  - /lrh-self-review remains report-only by default, with any diff-mode apply behavior and recursion guard documented consistently at all call sites
  - /lrh-confirm-fixes' empty-thread fast path is gated or the retained flag is explicitly justified by a governing decision that blocks Stage 2 completion
  - The installer.py Codex allow_implicit_invocation side effect is decided deliberately and tests are updated when code changes
  - Claude and Codex installed skill corpora are refreshed or verified, and disable-model-invocation absence/presence is checked against installed corpora, not only source
  - confirmed_commit is re-stamped if this work edits files on the chain-defaults staleness watch list
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-self-review/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/
  - .agents/skills/
  - tests/skills_installer_test.py
---

# Complete Stage 2 retained-flag removal and invocation-policy propagation

## Summary

Finish the Stage 2 invocation-policy work that `WI-DELIBERATE-MODEL-INVOCATION`
explicitly left out of scope: the retained flags on `lrh-self-review`,
`lrh-confirm-fixes`, `lrh-land`, and `lrh-execute`, plus the Codex installer
policy side effect and installed-corpus verification required by
`PROP-INVOCATION-AND-GATE-RESET`.

## Problem / Context

`WI-DELIBERATE-MODEL-INVOCATION` resolved the first scoped pass: nine skills
moved from `disable-model-invocation` to guidance and `when_to_use`. Its own
acceptance criteria deliberately retained four flags pending specific gate
gaps. `WS-INVOCATION-AND-GATE-RESET`, however, still requires Stage 2 to remove
the remaining flags with the replacement policy in place before Stage 3
proceeds.

Without this leaf, the workstream graph can advance from the already resolved
Stage 2 work straight to Stage 3 while the central invocation-reset condition
remains incomplete. This work item makes that missing edge explicit.

### Prior Art Check

**Duplication search.** No existing proposed work item owns the retained Stage 2
flag-removal completion scope. `WI-DELIBERATE-MODEL-INVOCATION` is resolved and
explicitly excluded these four flags. `WI-FRONT-OF-RUN-GATE-COLLAPSE` fixed one
front-of-run gate issue but did not remove all retained flags.

**Demand search.** Demand is explicit in
`WS-INVOCATION-AND-GATE-RESET.exit_criteria` and
`PROP-INVOCATION-AND-GATE-RESET` Stage 2.

**Recommendation.** Proceed before Stage 3. If a retained flag must remain,
record the governing decision and update the workstream exit criterion rather
than silently skipping the Stage 2 condition.

## Scope

- The four retained Stage 2 flags: `lrh-self-review`, `lrh-confirm-fixes`,
  `lrh-land`, and `lrh-execute`.
- Target-appropriate `when_to_use` or equivalent rendered policy guidance.
- `/lrh-self-review` report-only/default-apply behavior and recursion guard
  consistency.
- `/lrh-confirm-fixes` empty-thread fast-path gate.
- The `installer.py` Codex `allow_implicit_invocation` side effect and tests.
- Installed-corpus propagation and verification.

## Required Changes

1. Re-read the retained-flag criteria in
   `WI-DELIBERATE-MODEL-INVOCATION` and the Stage 2 section of
   `PROP-INVOCATION-AND-GATE-RESET`.
2. Remove retained flags only where the replacement gate or policy is actually
   present.
3. Add or update `when_to_use` guidance for each affected skill.
4. Decide and record the Codex installer policy behavior, updating tests when
   implementation changes.
5. Propagate source changes to installed Claude and Codex corpora.
6. Verify the installed corpora, not just `src/` and `.claude/`.

## Non-Goals

- Does not activate `chain_init_confirmation: skip_if_opted_in`.
- Does not implement Stage 3's gate corpus audit or cascade.
- Does not manually retrigger hosted GitHub review agents.
- Does not resolve unrelated retained flags outside the Stage 2 list.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Installed-corpus searches for the affected Stage 2 flags.

## Risk Notes

- Removing a flag before its replacement gate exists recreates the
  no-chain-self-starts gap this program is trying to close.
- Keeping a flag may be the right result for one skill, but then the governing
  Stage 2 criterion must be amended explicitly rather than left contradictory.
