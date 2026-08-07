---
id: WS-SKILLS-EXECUTE
kind: planning_node
title: Chain-Running Skills — /lrh-land, /lrh-execute, /lrh-next, /lrh-run-tree
status: resolved
stage: closed
origin: follow_up
summary: >
  Govern development of the four chain-running Claude Code skills that automate
  the LRH post-PR lifecycle chain: /lrh-land (primitive), /lrh-execute
  (compound), /lrh-next (navigator), and /lrh-run-tree (orchestrator).
related_design:
  - project/design/proposals/adopted/lrh-land-execute/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - src/lrh/skills/_shared/lifecycle-chain.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
work_items:
  - WI-SKILLS-LRH-LAND
  - WI-REVIEW-RESPONSE-INCLUDE-THREAD
  - WI-LRH-LAND-OUTDATED-THREAD-RECOVERY
  - WI-SKILLS-LRH-EXECUTE
  - WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION
exit_criteria:
  - /lrh-land skill implemented, lrh validate 0 errors, installed in both src/ and .claude/ mirrors
  - /lrh-execute skill implemented, lrh validate 0 errors, installed in both src/ and .claude/ mirrors
  - All five glue-logic rules from PROP-LRH-LAND-EXECUTE Decision 3 are encoded as explicit algorithmic steps in /lrh-land
  - Run journal prototype producing structured YAML output and used in at least one dogfooding session
  - PROP-LRH-LAND-EXECUTE adopted (status updated from proposed to adopted)
  - CLAUDE.md Skills index updated for /lrh-land and /lrh-execute
---

## Purpose

This workstream governs development of the four chain-running Claude Code
skills specified in `PROP-LRH-LAND-EXECUTE`: `/lrh-land`, `/lrh-execute`,
`/lrh-next`, and `/lrh-run-tree`. It exists to convert the existing Taurcode
`:land` and `:execute` master prompts into first-class LRH skills, encoding
the five glue-logic rules documented in the LCATS full-lifecycle case study
(nine PRs, 35 manual operations, 2026-07-26 to 2026-07-28) and aligning with
the `DEC-DELIBERATE-CHAIN-INITIATION` governance framework.

The immediate deliverables are Phases 1 and 2: `/lrh-land` and
`/lrh-execute`. Phases 3 and 4 (`/lrh-next` and `/lrh-run-tree`) are owned
by this workstream but explicitly deferred until the Phase 1–2 skills are
stable and observed in practice.

## Scope

- Implement `/lrh-land`: terminal pipeline skill for landing one open PR
  through review, confirm, merge gate, and closeout, with all five
  PROP-LRH-LAND-EXECUTE glue-logic rules encoded algorithmically.
- Implement `/lrh-execute`: compound skill for implementing one WI end-to-end
  and handing off to `/lrh-land`, with minimal WS-level navigation.
- Create `WI-SKILLS-LRH-NEXT` and `WI-SKILLS-LRH-RUN-TREE` as thin planning
  WIs (deferred implementation); design work feeds back into
  `PROP-WORKSTREAM-EXECUTION-FRAMEWORK`.
- Update `CLAUDE.md ## Skills` index for each shipped skill.
- Adopt `PROP-LRH-LAND-EXECUTE` once Phase 2 is complete.

## Prior Art Check

### Duplication search

- **In-repo:** `WS-SKILLS` (resolved 2026-06-25) covered core skill
  infrastructure (create-skill, lrh-setup, lrh-work-item, lrh-implement,
  lrh-review-response). `WS-EXECUTION-FRAMEWORK` (proposed) covers the
  long-term bounded execution framework and run packets — different scope.
  `WS-SKILLS-CLOSEOUT`, `WS-SKILLS-CONFIRM-FIXES` (resolved) covered their
  respective single skills. No existing chain-running-skills workstream.
- **Sibling repos:** Taurcode contains `:land` and `:execute` master prompts;
  this workstream canonicalises them as LRH skills — no duplication.
- **External libraries:** None applicable.
- **Recommendation:** Proceed.

### Demand search

- **Work items:** `WI-DELIBERATE-MODEL-INVOCATION` (proposed, owned by
  `WS-EXECUTION-FRAMEWORK`) is a prerequisite for Phase 2's direct sub-skill
  invocation; cross-link but do not subsume.
- **Proposals:** `PROP-LRH-LAND-EXECUTE` (proposed, PR #427 merged
  2026-07-28) is the governing design — this workstream implements it.
- **Backlog:** No matching entries.
- **Recommendation:** No action; `PROP-LRH-LAND-EXECUTE` is the demand item
  that this workstream satisfies.

## Work Items

Delivery is phased per `PROP-LRH-LAND-EXECUTE` § Implementation Plan:

- **WI-SKILLS-LRH-LAND** (Phase 1) — Implement the `/lrh-land` skill.
  Terminal pipeline: PR assessment → chain authorization gate →
  review-response → confirm-fixes → merge gate → closeout → run journal.
  Encodes all five glue-logic rules. Uses inline sub-skill steps until
  `WI-DELIBERATE-MODEL-INVOCATION` lands (interim invocation pattern per
  PROP-LRH-LAND-EXECUTE Decision 7).

- **WI-SKILLS-LRH-EXECUTE** (Phase 2) — Implement the `/lrh-execute` skill.
  Accepts `WI-ID` or `WS-ID`; enforces `depends_on`; invokes `/lrh-implement`
  workflow; hands off to `/lrh-land`. Requires `WI-SKILLS-LRH-LAND` resolved.
  `WI-DELIBERATE-MODEL-INVOCATION` enables direct invocation of lifecycle
  sub-skills via the Skill tool, but is not a hard gate — Phase 1's inline
  pattern can carry Phase 2 if needed.

- **WI-SKILLS-LRH-NEXT** (Phase 3, deferred) — Implement the `/lrh-next`
  navigator skill. Full planning-tree traversal; machine-readable YAML output
  for `/lrh-run-tree` consumption. Design after Phase 2 is stable.

- **WI-SKILLS-LRH-RUN-TREE** (Phase 4, deferred) — Implement the
  `/lrh-run-tree` orchestrator skill. Bounded
  `/lrh-next → /lrh-execute|/lrh-land` loop; requires completion condition
  and stop-work condition.
  Design after Phase 3 is stable.

The prerequisite `WI-DELIBERATE-MODEL-INVOCATION` is owned by
`WS-EXECUTION-FRAMEWORK` and tracked there; it is a dependency, not a
child of this workstream.

## Exit Criteria

- `/lrh-land` skill implemented, `lrh validate` 0 errors, installed in both
  `src/lrh/skills/lrh-land/` and `.claude/skills/lrh-land/` mirrors
- `/lrh-execute` skill implemented, `lrh validate` 0 errors, installed in
  both `src/` and `.claude/` mirrors
- All five glue-logic rules from PROP-LRH-LAND-EXECUTE Decision 3 are
  encoded as explicit algorithmic steps in `/lrh-land` (not prose)
- Run journal prototype producing structured YAML output and used in at least
  one dogfooding session
- `PROP-LRH-LAND-EXECUTE` status updated to `adopted`
- `CLAUDE.md ## Skills` index entries added for `/lrh-land` and `/lrh-execute`

## Non-Goals

- Does not govern `WI-DELIBERATE-MODEL-INVOCATION` — owned by
  `WS-EXECUTION-FRAMEWORK`.
- Does not implement the bounded autonomous execution framework
  (`lrh[agentic]`) — that remains the scope of `WS-EXECUTION-FRAMEWORK`.
- Does not require `/lrh-next` or `/lrh-run-tree` to ship before closure —
  Phases 3 and 4 are explicitly deferred; their WIs close separately.
- Does not modify execution record schema (typed `role:` field, validated
  `rerun_of:`) — separate work items outside this workstream.
- Does not fix the `/lrh-work-item` Step 9 workstream-registration gap —
  flagged in LCATS evidence as a separate issue.

## Relationship to Design

- Governing proposal:
  `project/design/proposals/adopted/lrh-land-execute/00_proposal.md`
- Governance decision:
  `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
- Canonical chain: `src/lrh/skills/_shared/lifecycle-chain.md`
- Long-term framework:
  `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Prior skills workstreams: `project/workstreams/resolved/WS-SKILLS.md`,
  `project/workstreams/resolved/WS-SKILLS-CLOSEOUT.md`
