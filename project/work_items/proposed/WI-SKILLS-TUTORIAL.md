---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-TUTORIAL
title: Add "Using Claude Code skills" tutorial to docs/tutorials/
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_land_tutorial
acceptance:
  - docs/tutorials/using-claude-code-skills.md exists, following the Step-based shape of first-lrh-project.md (numbered Steps, "What success looks like", "Where to go next")
  - The tutorial's worked examples are /lrh-work-remains (report-only) followed by /lrh-work-item (stopping at its Step 5 confirm gate, before any file write)
  - The tutorial names the typed-vs-offered invocation distinction observably, without naming disable-model-invocation or when_to_use
  - The tutorial explicitly defers chain-authorization (/lrh-land, /lrh-execute, completion/stop-work conditions) to a future tutorial, named in "Where to go next"
  - docs/tutorials/README.md's "Currently relevant docs" list has a new one-line entry for the tutorial, matching the existing three entries' format
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - docs/tutorials/using-claude-code-skills.md
  - docs/tutorials/README.md
---

## Summary

Add `docs/tutorials/using-claude-code-skills.md`, a beginner-facing tutorial
teaching how to invoke an LRH Claude Code skill, read a confirm-before-write
gate, and distinguish a report-only skill from one that writes files —
closing the gap that no existing tutorial teaches the skills system itself.

## Problem / Context

`docs/tutorials/` has three tutorials (first-lrh-project, first-prompt-driven-change,
work-item-readiness) but none teaches the skills system. The closest doc,
`docs/how-to/use-lrh-with-agent-assistants.md`, is How-to-shaped — it covers
installing/configuring skills across agent backends, not how a newcomer
invokes one day to day. CLAUDE.md's `## Skills` section is a bare index, not
a guided walkthrough. This gap was confirmed via `/lrh-design` (see this
work item's originating conversation) by reading `docs/tutorials/README.md`'s
inclusion criteria and the existing tutorials directly to match their shape.

### Duplication search
- In-repo: No existing implementation found — confirmed by direct read of
  `docs/tutorials/`, `docs/how-to/use-lrh-with-agent-assistants.md`, and
  `docs/explanations/`.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found (`grep -rli "skills tutorial\|tutorial.*skill"` across
  `project/work_items/`, `project/design/proposals/`, `project/workstreams/`
  returned nothing).
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Write one new tutorial file teaching skill invocation, a report-only
  worked example, and a confirm-gate worked example.
- Update `docs/tutorials/README.md`'s index to reference it.

## Required Changes

1. Create `docs/tutorials/using-claude-code-skills.md`, mirroring
   `first-lrh-project.md`'s shape: framing paragraph, numbered Steps with
   copy-pasteable commands, "What success looks like", "Where to go next".
2. Step content: invoking a skill as a slash command; running `/lrh-work-remains`
   as a report-only example (no file writes); running `/lrh-work-item` up to
   and including its Step 5 confirm-before-write gate, without completing
   the write, to show what a confirm gate looks like and why it exists.
3. Name the observable typed-vs-offered invocation distinction ("some skills
   must be typed as the first word of your message; others Claude can offer
   on its own judgment") without naming `disable-model-invocation` or
   `when_to_use` — that is reference-level detail, out of scope here.
4. "Where to go next" section: link to `use-lrh-with-agent-assistants.md`
   for install/config, and note chain-authorization (`/lrh-land`,
   `/lrh-execute`, completion/stop-work conditions) as a future tutorial
   topic not covered here.
5. Add a one-line entry to `docs/tutorials/README.md`'s "Currently relevant
   docs" list, matching the existing three entries' format.

## Non-Goals

- Do not cover chain-authorization mechanics, `/lrh-land`, or `/lrh-execute`
  — defer to a future tutorial.
- Do not name or explain `disable-model-invocation` or `when_to_use` by name
  — defer to reference/explanation docs.
- Do not write a new how-to or explanation doc for gate/chain mechanics as
  part of this item.
- Do not modify `use-lrh-with-agent-assistants.md` or any other existing doc
  besides `docs/tutorials/README.md`.

## Acceptance Criteria

- `docs/tutorials/using-claude-code-skills.md` exists, following the
  Step-based shape of `first-lrh-project.md`.
- The tutorial's worked examples are `/lrh-work-remains` then `/lrh-work-item`
  (stopping at the confirm gate).
- The tutorial names the typed-vs-offered distinction observably, without
  naming `disable-model-invocation` or `when_to_use`.
- The tutorial defers chain-authorization to a future tutorial, noted in
  "Where to go next".
- `docs/tutorials/README.md`'s index includes the new entry.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`

## Risk Notes

- Risk that the tutorial drifts into reference-level detail (flag names,
  exhaustive skill catalog) — mitigated by the Non-Goals above and by
  reviewing against `docs/tutorials/README.md`'s own inclusion criteria
  before merging.
- Risk that `/lrh-work-item`'s actual interview flow changes after this
  tutorial is written, making the worked example stale — no special
  mitigation; treat as ordinary doc-drift risk, addressable via
  `/lrh-doc-work` later.
