---
resolution: null
blocked_reason: null
blocked: false
id: WI-GATE-CONFIRM-RENDERING
title: Platform-neutral confirm-gate phrasing across the LRH skill corpus, plus a bounded structured-choice spike
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - change_gate_cardinality_or_consent_policy
acceptance:
  - Every gate-bearing SKILL.md instructs platform-neutral confirm phrasing -- prefer a structured choice mechanism when the running environment provides one, always include an explicit "stop and ask for guidance" option, and state the gate as the agent's final top-level message rather than nested inside intermediate or collapsible output
  - A written spike note answers, with cited evidence, whether Codex and/or Antigravity currently expose any structured multiple-choice or button input primitive an LRH render adapter could target
  - If the spike finds a viable primitive, a follow-up work item is drafted (not implemented) proposing the adapter extension; if not, the spike note says so explicitly and no follow-up is drafted
  - lrh validate reports 0 errors
  - Claude and Codex rendered installs are up to date with the edited skills
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-readiness/SKILL.md
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/ mirrors of the above
  - .agents/skills/ mirrors of the above
  - project/design/ (spike note)
---

# Platform-neutral confirm-gate phrasing across the LRH skill corpus, plus a bounded structured-choice spike

## Summary

Rewrite the gate-instruction language in every gate-bearing LRH skill to
platform-neutral phrasing that pushes agents toward a structured-choice
presentation where the runtime supports one, and toward an un-buried,
explicit stop option everywhere else; and run a bounded spike on whether
Codex or Antigravity expose a structured-choice primitive worth adapting to.

## Problem / Context

LRH skills are authored once and rendered across Claude Code, Codex, and
Antigravity via `src/lrh/skills/installer.py`'s render adapters
(`CodexSkillRenderer` at `installer.py:190-260`,
`AntigravitySkillRenderer` at `:261-288`). Every gate in the corpus today is
plain prose with no rendering guidance -- e.g. `/lrh-implement` Step 4
(`src/lrh/skills/lrh-implement/SKILL.md:145-157`): "Wait for explicit
confirmation... Do not proceed past this gate without approval," and
`/lrh-closeout` Step 4 (`src/lrh/skills/lrh-closeout/SKILL.md:257-284`),
same pattern. On Claude Code this can render as free text the user must
type a reply to, even though a structured-choice tool is available. On
Codex, the final gate text can end up nested inside a collapsed
"Worked for Nm Ns" tool-log section, adding a click before the user can
even see the ask. Both add friction for a user who is, e.g., interacting
by mouse/voice rather than keyboard.

This item was scoped in design conversation on 2026-08-13 (see the
session's design comparison of three options: (B) platform-neutral gate
vocabulary with no tool named explicitly, (A) hardcoding `AskUserQuestion`
calls, and (C) a new platform-capability negotiation layer in the render
adapters). (A) was rejected because `AskUserQuestion` is Claude-Code-
specific and the render adapters do not translate tool names inside
prose. (C) was found premature -- no evidence surfaced that Codex or
Antigravity expose any structured-choice primitive today, so building a
negotiation layer for capabilities that may not exist elsewhere has no
current payoff. (B) was chosen as the first move, with (C) deferred to a
spike rather than dropped, since the evidence gap is the actual blocker
and might not hold.

### Duplication search

- In-repo: No existing implementation. Two proposals reference UI
  "buttons" (`project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md`
  and `project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md`)
  but both concern the separate `lrh serve` web console's own action
  buttons, not agent-chat confirm-gate rendering -- a different surface,
  not a duplicate.
- Sibling repos: `taurcode` was named as carrying the same gate *policy*
  via its `:land`/`:execute` prompts (per
  `WS-INVOCATION-AND-GATE-RESET.md:94-97`), but rendering/input modality
  was not investigated there; treated as unknown, not a match.
- External libraries: None identified -- this is prompt-authoring
  convention, not a library concern.
- Recommendation: Proceed.

### Demand search

- Work items: None found requesting this specifically.
- Proposals: `PROP-INVOCATION-AND-GATE-RESET` addresses gate *cardinality
  and consent policy* (how many times the human is asked), not gate
  *rendering* -- adjacent, not a match.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Rewrite gate-instruction language in every gate-bearing skill identified
  by Stage 3's gate corpus audit (or, if this item starts before that
  audit artifact exists, the currently known set listed in
  `artifacts_expected`) to platform-neutral phrasing.
- Run and document one bounded spike answering whether Codex and/or
  Antigravity expose a structured multiple-choice/button input primitive.
- Propagate edited skills to `.claude/skills/` and `.agents/skills/`
  mirrors and verify installs.

## Required Changes

1. Draft the platform-neutral gate phrasing convention as a shared
   fragment (following the existing `src/lrh/skills/_shared/` pattern used
   for `lifecycle-chain.md` and `prior-art-check.md`), stating: prefer a
   structured choice mechanism when available, always include an explicit
   "stop and ask for guidance" option, and state the gate as the final
   top-level message rather than nested inside intermediate output.
2. Apply that convention to each gate-bearing `SKILL.md` in
   `artifacts_expected` (or the Stage 3 audit's list, whichever is
   authoritative when this item starts).
3. Run the Codex/Antigravity structured-choice spike: inspect each
   platform's available tool/primitive surface for anything resembling a
   button or forced multiple-choice input; write findings with citations
   to `project/design/` as a spike note.
4. If the spike finds a viable primitive, draft (do not implement) a
   follow-up work item proposing the adapter extension.
5. Run `lrh skills install` and verify against the installed corpora for
   both Claude and Codex targets.

## Non-Goals

- Does not change gate cardinality, consent policy, or which gates exist
  -- that is `WS-INVOCATION-AND-GATE-RESET` Stage 3's own scope (audit,
  policy proposal, DEC record).
- Does not build the full platform-capability negotiation layer in
  `installer.py` (Option C) -- only the bounded spike answering whether
  the evidence for it exists.
- Does not implement any adapter extension even if the spike finds a
  viable Codex/Antigravity primitive -- that becomes a separate future
  work item.
- Does not touch the `lrh serve` web console's own button/UI work.

## Acceptance Criteria

Consult the `acceptance:` frontmatter field, which is the authoritative list.

## Validation

- `lrh validate`
- `lrh skills check --target claude --local`
- `lrh skills status --target codex --local`
- `diff -r src/lrh/skills/<skill> .claude/skills/<skill>` for each touched skill

## Risk Notes

- **File-collision risk with Stage 3.** `WS-INVOCATION-AND-GATE-RESET.md:151-160`
  documents that Stages 1-2 wrongly assumed independence "because they
  share no files" and broke a re-stamp constraint as a result. This item
  touches the same gate-bearing files Stage 3's cascade touches. `depends_on`
  is left empty here because Stage 3's own gate-corpus-audit/cascade work
  item has not yet been minted a `WI-*` ID (see
  `project/workstreams/proposed/WS-INVOCATION-AND-GATE-RESET.md:147`, which
  still lists Stage 3 as unassigned in its work-item table) -- update
  `depends_on` to name it once minted, and do not start this item's file
  edits concurrently with Stage 3's cascade in the meantime.
- **Codex's collapsed-summary placement is a client rendering quirk.**
  Instructing "state the gate as the final top-level message" mitigates
  but cannot guarantee Codex will stop collapsing tool-call sections --
  that behavior is outside LRH's control.
- **Spike scope creep.** The Codex/Antigravity investigation is bounded to
  answering the question and, if warranted, drafting a follow-up work
  item -- not implementing anything found.

## Open Questions

- Stage 3's gate-corpus-audit work item has not been minted yet, so this
  item's `depends_on` cannot yet name it by ID. Resolve when Stage 3's
  first work item is created.
