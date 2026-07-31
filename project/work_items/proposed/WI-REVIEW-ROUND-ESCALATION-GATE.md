---
resolution: null
blocked_reason: null
blocked: false
id: WI-REVIEW-ROUND-ESCALATION-GATE
title: Escalating human-gated round cap for assist-model review/fix loops
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - implement_ci_round_limits
  - implement_bounded_auto_mode
  - run_lrh_agentic
  - merge_pr
acceptance:
  - "/lrh-review-response computes a durable round count for the target PR before any bot-retrigger"
  - "reaching the current ceiling stops the skill and presents the three-way gate (authorize/deny/pause) before further retrigger"
  - "default ceiling-suggestion sequence (3 -> 10 -> 20 -> ...) documented; actual next ceiling is human-supplied, not auto-applied"
  - "CHAIN-NOTE stops/note field docs updated to cover gate crossings"
  - "mechanism's scope (assist-loop only, not aggregate Copilot spend or Jules/manual activity) is explicitly documented"
  - "src/ and .claude/ skill mirrors match (diff -r reports no differences)"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-review-response/references/round-cap-gate.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/references/round-cap-gate.md
  - .claude/skills/lrh-land/references/land-workflow.md
---

## Summary

Add a durable, human-gated round-count check to `/lrh-review-response` that
stops the assist-model review/fix loop before each bot-retrigger once a
per-PR round ceiling is reached, requiring explicit human authorization (to
a new ceiling), denial, or pause before continuing.

## Problem / Context

Recent PRs in this repo drove the Codex/Copilot review/fix loop for many
unattended rounds — PR #438 (8 rounds) and PR #442 (14 rounds, 13 real
findings, `project/executions/AD_HOC/2026_07_30_05_33_51_LRH_MERGE_GATE_POLICY_391AEF_CONFIRM.md:54-61,102`)
— each round retriggering both bots, which rescans the full cumulative PR
diff (`feedback_bot_review_needs_explicit_retrigger.md`) and draws down a
GitHub Copilot credit pool shared across 6+ concurrently active projects of
differing priority (urgent, important, nice-to-have). That pool has no
per-repo partitioning at the GitHub platform level, so an unattended long
review cycle on a low-priority repo can stall unrelated, higher-priority
pipelines with no warning. `DEC-DELIBERATE-CHAIN-INITIATION` already
requires a human-set stop-work condition before any chain of these rounds
runs automatically, but today that's prose re-elicited per run, not a
persistent, recurring, numeric checkpoint. This item formalizes that
checkpoint for the assist-model loop specifically — the mechanism capable of
unattended, automatic round escalation (Jules and human-driven PR activity
are structurally outside `/lrh-review-response`'s reach, per
`WI-TEMPLATE-AUDIT-WORK-ITEMS.md:47-53`, and are explicitly out of scope).

### Duplication search
- In-repo: Related: `project/work_items/proposed/WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md` — broader planning item covering review + CI iteration limits, escalation, and manual/assisted/bounded-auto mode distinctions; blocked on `WI-GITHUB-PR-CI-OBSERVATION`, `WI-AGENT-BRANCH-CONTAINMENT`, `WI-DELIBERATE-MODEL-INVOCATION`. This item implements only the assisted-mode slice, standalone and unblocked, cross-linked rather than folded in.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed (standalone, cross-linked).

### Demand search
- Work items: Found: `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` — "Plan bounded review and CI stabilization loop" (broader, partially overlapping; blocked state does not satisfy this item's narrow, unblocked scope).
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action — proceed standalone; reference this item from `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`'s Related section once that item is unblocked.

## Scope

- Add a round-count check to `/lrh-review-response`, executed before any bot-retrigger action.
- Define "round" as one `/lrh-review-response` → `/lrh-confirm-fixes` iteration, matching the existing CHAIN-NOTE `cycles` definition.
- Derive the round count from durable state (`project/executions/` records for the target PR), not session memory.
- Present a three-way human gate (authorize to a new ceiling / deny-stop / pause) when the round count reaches the current ceiling; default next-ceiling suggestion 3 → 10 → 20, but the human states the actual next ceiling.
- Document the mechanism's scope explicitly: bounds only `/lrh-review-response` × `/lrh-confirm-fixes` assist-loop rounds.
- Extend CHAIN-NOTE `stops`/`note` field documentation to record gate crossings and authorized ceilings.

## Required Changes

1. Edit `src/lrh/skills/lrh-review-response/SKILL.md` to add a round-count-check step before the bot-retrigger step: compute the current round count for the target PR from `project/executions/` (reusing the primary-record-selection grep pattern already established in `src/lrh/skills/lrh-land/SKILL.md`), compare to the last-authorized ceiling, and stop with the three-way gate if reached.
2. Create `src/lrh/skills/lrh-review-response/references/round-cap-gate.md` documenting: the round-count derivation method, the default ceiling-suggestion sequence (3 → 10 → 20 → ...), the three-way gate options, and the explicit scope statement.
3. Edit `src/lrh/skills/lrh-land/references/land-workflow.md` to extend the CHAIN-NOTE `stops` and `note` field descriptions to cover round-cap gate crossings and the ceiling authorized at each crossing.
4. Mirror all changed/new files to `.claude/skills/lrh-review-response/` and `.claude/skills/lrh-land/` respectively.

## Non-Goals

- Do not implement `max_ci_rounds` or any CI-stabilization iteration limit — deferred to `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`.
- Do not implement a "bounded-auto" (autonomous) execution mode — assist-model only, per `DEC-DELIBERATE-CHAIN-INITIATION` principle 4.
- Do not integrate the GitHub Copilot premium-request usage API or any auto-fetched budget/cross-repo telemetry — not currently available; the human supplies that judgment at the gate.
- Do not extend the LRH meta-control-plane for cross-repo visibility — separate infrastructure (`project/design/meta_control_plane_mvp_spec.md`).
- Do not change `disable-model-invocation` semantics on either skill.
- Do not resolve or unblock `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`.

## Acceptance Criteria

- `/lrh-review-response` computes a round count for the target PR from durable `project/executions/` records before retriggering any bot review.
- When the round count reaches the current ceiling, the skill stops and presents the three-way gate (authorize to new ceiling / deny-stop / pause) before any further bot-retrigger action.
- The default ceiling-suggestion sequence (3 → 10 → 20 → ...) is documented, and the skill instructions make clear the actual next ceiling is human-supplied, not auto-applied.
- CHAIN-NOTE `stops`/`note` field documentation in `land-workflow.md` covers round-cap gate crossings.
- The skill/reference docs explicitly state the mechanism bounds only `/lrh-review-response` × `/lrh-confirm-fixes` rounds, not aggregate Copilot spend or Jules/manual PR activity.
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/` and `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/` report no differences.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`

## Risk Notes

- A round-cap gate that fires too often could become a rubber-stamp click rather than a substantive decision point — mitigate by ensuring the gate surfaces round-specific context (findings so far, if derivable) rather than a bare "continue?" prompt.
- Documentation alone cannot prevent a human from reflexively authorizing every gate; this item builds the checkpoint, not a guarantee of disciplined use.
