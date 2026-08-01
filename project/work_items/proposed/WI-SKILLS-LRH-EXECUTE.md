---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-EXECUTE
title: Implement /lrh-execute Claude Code skill
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
  - WS-SKILLS-EXECUTE
related_design:
  - project/design/proposals/proposed/lrh-land-execute/00_proposal.md
  - project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md
  - src/lrh/skills/_shared/lifecycle-chain.md
depends_on:
  - WI-SKILLS-LRH-LAND
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - src/lrh/skills/lrh-execute/SKILL.md exists with valid frontmatter
  - .claude/skills/lrh-execute/ is a byte-identical copy of src/lrh/skills/lrh-execute/
  - /lrh-execute accepts a WI-ID or WS-ID, enforces depends_on before starting, invokes the /lrh-implement workflow, and hands off to /lrh-land for landing
  - /lrh-execute retriggers bot review only through /lrh-land's existing round-cap-gate.md guardrail, never an independent unguarded retrigger path
  - lrh validate passes with 0 errors
  - CLAUDE.md's ## Skills index has an entry for /lrh-execute
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-execute/SKILL.md
  - .claude/skills/lrh-execute/SKILL.md
  - CLAUDE.md (Skills index entry)
---

## Summary

Implement the `/lrh-execute` Claude Code skill — the compound "implement a
work item and land it" skill (Phase 2 of `PROP-LRH-LAND-EXECUTE`),
packaging the Taurcode `:execute` master prompt as a first-class LRH skill.

## Problem / Context

`/lrh-execute` does not exist yet, even though `PROP-LRH-LAND-EXECUTE`
proposed it alongside `/lrh-land` (implemented, resolved via
`WI-SKILLS-LRH-LAND`). Sessions that need to implement-and-land a work
item currently fall back to the raw Taurcode `:execute` master prompt,
which predates and lacks `round-cap-gate.md`'s bot-review retrigger
guardrail. On 2026-08-01 this caused a real incident: a session using
`:execute` ran 14 uncapped review rounds before a human manually
triggered a fresh-context self-review that returned a NO-GO verdict,
finding a root-cause design issue and a bug none of the 14 rounds had
caught. `WI-SKILLS-LRH-LAND` is resolved, satisfying this item's stated
prerequisite. `WI-DELIBERATE-MODEL-INVOCATION` (proposed, owned by
`WS-EXECUTION-FRAMEWORK`) would enable direct sub-skill invocation but is
explicitly not a hard gate — `WS-SKILLS-EXECUTE` documents that Phase 1's
inline sub-skill pattern can carry Phase 2 if needed.

### Duplication search
- In-repo: No existing `/lrh-execute` implementation. `WS-SKILLS-EXECUTE`'s
  own prior art check (2026-07-28) found no existing chain-running-skills
  workstream; re-verified 2026-08-01 — still true.
- Sibling repos: Taurcode's `:execute` master prompt is the pre-LRH-skill
  implementation this item canonicalizes, per `PROP-LRH-LAND-EXECUTE` —
  not a duplicate to preserve.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found under this ID; `WS-SKILLS-EXECUTE`'s own
  `## Work Items` section already describes this item's scope (Phase 2) —
  this WI formalizes that as a standalone, validated artifact.
- Proposals: `PROP-LRH-LAND-EXECUTE` (proposed, PR #427 merged
  2026-07-28) is the governing design this item implements.
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: No action — this WI is the demand item `WS-SKILLS-EXECUTE`
  and `PROP-LRH-LAND-EXECUTE` already call for.

## Scope

- Implement `/lrh-execute`: accepts a `WI-ID` or `WS-ID`, enforces
  `depends_on` before starting, invokes the `/lrh-implement` workflow,
  hands off to `/lrh-land` for landing.
- Reuse `/lrh-land`'s existing inline chain (review-response →
  confirm-fixes → merge gate → closeout) and `round-cap-gate.md`'s
  bot-retrigger guardrail — do not build a second, parallel retrigger
  mechanism.
- Mirror to both `src/lrh/skills/lrh-execute/` and `.claude/skills/lrh-execute/`.
- Add a `## Skills` index entry to `CLAUDE.md`.

## Required Changes

1. Create `src/lrh/skills/lrh-execute/SKILL.md` following the established
   LRH skill pattern (see `src/lrh/skills/lrh-land/SKILL.md` for the
   sibling chain-running skill's structure).
2. Wire `/lrh-execute` to invoke `/lrh-implement`'s three-phase workflow
   for the target `WI-ID`, then hand off to `/lrh-land` for the resulting
   PR — inline sub-skill execution (matching `/lrh-land`'s own current
   pattern), not direct Skill-tool invocation, since
   `WI-DELIBERATE-MODEL-INVOCATION` remains unresolved.
3. Enforce the target work item's `depends_on` list before starting.
4. Mirror `src/lrh/skills/lrh-execute/SKILL.md` byte-for-byte to
   `.claude/skills/lrh-execute/SKILL.md`.
5. Add a `/lrh-execute` entry to `CLAUDE.md`'s `## Skills` index.

## Non-Goals

- Does not implement `/lrh-next` or `/lrh-run-tree` — Phases 3–4 of
  `PROP-LRH-LAND-EXECUTE`, explicitly deferred by `WS-SKILLS-EXECUTE`.
- Does not implement direct Skill-tool sub-skill invocation —
  `WI-DELIBERATE-MODEL-INVOCATION`'s scope.
- Does not design or implement the fresh-context go/no-go escalation
  pattern discussed as a response to hitting a review-round ceiling —
  that is `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`'s scope; this item's
  obligation is narrower: reuse the *existing* round-cap-gate
  ceiling/ask-the-human mechanism, not invent a new escalation behavior.
- Does not retire or modify the Taurcode `:execute` master prompt itself.
- Does not modify execution-record schema, `PROP-LRH-LAND-EXECUTE`'s
  adoption status, or any of `/lrh-land`'s existing behavior.

## Acceptance Criteria

- `src/lrh/skills/lrh-execute/SKILL.md` exists with valid frontmatter.
- `.claude/skills/lrh-execute/` is byte-identical to
  `src/lrh/skills/lrh-execute/`.
- `/lrh-execute` accepts a `WI-ID` or `WS-ID`, enforces `depends_on`,
  invokes `/lrh-implement`, and hands off to `/lrh-land`.
- `/lrh-execute` retriggers bot review only through `/lrh-land`'s existing
  `round-cap-gate.md` guardrail.
- `lrh validate` reports 0 errors.
- `CLAUDE.md`'s `## Skills` index has an entry for `/lrh-execute`.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `diff -r src/lrh/skills/lrh-execute/ .claude/skills/lrh-execute/`

## Risk Notes

- The coverage gap this item closes is actively costing GitHub review
  credits today (two known incidents on 2026-08-01) — time-sensitive, not
  routine backlog work.
- Reusing `/lrh-land`'s inline pattern duplicates some of its prose rather
  than composing it — a known, accepted tradeoff per `WS-SKILLS-EXECUTE`,
  not a defect to fix here.

## Dependencies / Order

`WI-SKILLS-LRH-LAND` is resolved, satisfying this item's stated
prerequisite. `WI-DELIBERATE-MODEL-INVOCATION` is not a hard gate —
proceed with the inline pattern if it remains unresolved when this item
is picked up.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SKILLS-EXECUTE.md`
- Design: `project/design/proposals/proposed/lrh-land-execute/00_proposal.md`
- Governance: `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
