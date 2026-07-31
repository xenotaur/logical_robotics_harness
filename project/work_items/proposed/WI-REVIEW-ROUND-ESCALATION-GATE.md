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
  - "/lrh-review-response and /lrh-confirm-fixes Step 8 each compute a durable round count (bot-retrigger batches, not cycles) before any bot-retrigger"
  - "round count is written synchronously before each retrigger, not reconstructed post-hoc from a finished record"
  - "applying the definition to PR #442 would yield 14, not the cycles=1 its CHAIN-NOTE reports today"
  - "reaching the current ceiling stops the skill and presents the three-way gate (authorize/deny/pause) before further retrigger"
  - "default ceiling-suggestion sequence (3 -> 10 -> 20 -> ...) documented; actual next ceiling is human-supplied, not auto-applied"
  - "CHAIN-NOTE stops/note field docs updated to cover gate crossings and distinguish the round-cap counter from cycles"
  - "mechanism's scope (lrh-review-response + lrh-confirm-fixes bot-retriggers only, not aggregate Copilot spend or Jules/manual activity) is explicitly documented"
  - "src/ and .claude/ skill mirrors match for all three touched skills (diff -r reports no differences)"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - .claude/skills/lrh-confirm-fixes/SKILL.md
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
unattended rounds — PR #438 (8 rounds) and PR #442, whose own CHAIN-NOTE
reports `cycles=1` (`project/executions/AD_HOC/2026_07_30_05_33_51_LRH_MERGE_GATE_POLICY_391AEF_CONFIRM.md:102`)
despite a 14-round bot-retrigger saga with 13 real findings recorded in the
same file's Step 8 narrative (lines 54-61). That gap is itself the evidence
that the natural counting unit is the bot-retrigger batch performed by
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8 (lines 330-335, repeated
at line 376 on each new finding), not the coarser review-response ↔
confirm-fixes `cycles` count — a ceiling defined in `cycles` units would
never have fired during the incident motivating this item. Each retrigger
draws down a GitHub Copilot credit pool shared across 6+ concurrently
active projects of differing priority (urgent, important, nice-to-have).
That pool has no
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

- Add a round-count check before every bot-retrigger action, in **both**
  `/lrh-review-response` (initial retrigger-and-wait) and
  `/lrh-confirm-fixes` Step 8 (the iterative retrigger loop — this is where
  the PR #442 incident actually occurred; gating `/lrh-review-response`
  alone would leave it ungated).
- Define "round" as one bot-retrigger batch (a single `@codex review` /
  `@copilot review` retrigger-and-wait pass), matching the unit
  `lrh-confirm-fixes/SKILL.md` Step 8 actually repeats — not the coarser
  `cycles` field, which PR #442 shows can read `1` across a 14-retrigger
  incident.
- Persist the round count **durably and synchronously before each
  retrigger** (not only reconstructed after the fact from a finished
  record), so the count survives a session restart mid-loop.
- Present a three-way human gate (authorize to a new ceiling / deny-stop / pause) when the round count reaches the current ceiling; default next-ceiling suggestion 3 → 10 → 20, but the human states the actual next ceiling.
- Document the mechanism's scope explicitly: bounds only the
  `/lrh-review-response` and `/lrh-confirm-fixes` bot-retrigger actions.
- Extend CHAIN-NOTE `stops`/`note` field documentation to record gate
  crossings and authorized ceilings, and clarify that the round-cap counter
  is a distinct metric from `cycles` (which undercounts retrigger batches).

## Required Changes

1. Edit `src/lrh/skills/lrh-review-response/SKILL.md` to add a round-count-check step before its bot-retrigger action.
2. Edit `src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8 (the retrigger commands at lines 330-335 and the repeat-on-new-finding logic at line 376) to add the same round-count-check before each retrigger — this is the loop the PR #442 incident actually ran in.
3. Define, in both edits, a durable per-PR round-tracking mechanism written synchronously immediately before each retrigger call (e.g. a field updated on the in-progress execution record for the target PR, or a small per-PR round-state artifact under `project/executions/`) — not a value reconstructed from `project/executions/` after the fact, since today's records (including CHAIN-NOTE `cycles`) are only written at the end of a run and would undercount or reset after a restart.
4. Create `src/lrh/skills/lrh-review-response/references/round-cap-gate.md` documenting: the bot-retrigger-batch round definition, the durable persistence mechanism, the default ceiling-suggestion sequence (3 → 10 → 20 → ...), the three-way gate options, and the explicit scope statement. Reference it from both edited skills.
5. Edit `src/lrh/skills/lrh-land/references/land-workflow.md` to extend the CHAIN-NOTE `stops` and `note` field descriptions to cover round-cap gate crossings and the ceiling authorized at each crossing, and to note that the round-cap counter is a separate, finer-grained metric than `cycles`.
6. Mirror all changed/new files to `.claude/skills/lrh-review-response/` and `.claude/skills/lrh-confirm-fixes/` and `.claude/skills/lrh-land/` respectively.

## Non-Goals

- Do not implement `max_ci_rounds` or any CI-stabilization iteration limit — deferred to `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`.
- Do not implement a "bounded-auto" (autonomous) execution mode — assist-model only, per `DEC-DELIBERATE-CHAIN-INITIATION` principle 4.
- Do not integrate the GitHub Copilot premium-request usage API or any auto-fetched budget/cross-repo telemetry — not currently available; the human supplies that judgment at the gate.
- Do not extend the LRH meta-control-plane for cross-repo visibility — separate infrastructure (`project/design/meta_control_plane_mvp_spec.md`).
- Do not change `disable-model-invocation` semantics on either skill.
- Do not resolve or unblock `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`.

## Acceptance Criteria

- Both `/lrh-review-response` and `/lrh-confirm-fixes` Step 8 compute a round count for the target PR before retriggering any bot review, counting each bot-retrigger batch (not `cycles`).
- The round count is written durably and synchronously immediately before each retrigger — verifiable by confirming the design does not rely solely on a post-hoc/end-of-run record (e.g. CHAIN-NOTE) to reconstruct the in-progress count.
- Applying this definition retroactively to PR #442's own record would have produced a round count of 14, not the `cycles=1` its CHAIN-NOTE currently reports — documented explicitly as the worked check that the unit is correct.
- When the round count reaches the current ceiling, the skill stops and presents the three-way gate (authorize to new ceiling / deny-stop / pause) before any further bot-retrigger action.
- The default ceiling-suggestion sequence (3 → 10 → 20 → ...) is documented, and the skill instructions make clear the actual next ceiling is human-supplied, not auto-applied.
- CHAIN-NOTE `stops`/`note` field documentation in `land-workflow.md` covers round-cap gate crossings and distinguishes the round-cap counter from `cycles`.
- The skill/reference docs explicitly state the mechanism bounds only `/lrh-review-response` and `/lrh-confirm-fixes` bot-retrigger actions, not aggregate Copilot spend or Jules/manual PR activity.
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`, `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`, and `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/` report no differences.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/`
- `diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/`
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`

## Risk Notes

- A round-cap gate that fires too often could become a rubber-stamp click rather than a substantive decision point — mitigate by ensuring the gate surfaces round-specific context (findings so far, if derivable) rather than a bare "continue?" prompt.
- Documentation alone cannot prevent a human from reflexively authorizing every gate; this item builds the checkpoint, not a guarantee of disciplined use.
- Gating two skills (`lrh-review-response` and `lrh-confirm-fixes`) instead of one roughly doubles the surface implementation touches; the durable per-retrigger persistence mechanism (Required Change 3) is the least-specified piece of this item and may need a follow-up design pass if a simple execution-record field update proves insufficient under concurrent/interleaved runs.
