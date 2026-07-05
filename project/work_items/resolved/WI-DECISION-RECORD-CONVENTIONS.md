---
resolution: "Implemented and merged in PR #374 (commit d76cbd31); documented the two-tier decision model in design.md and retrofitted DEC-PRECEDENCE-SEMANTICS onto precedence_semantics.md."
blocked_reason: null
blocked: false
id: WI-DECISION-RECORD-CONVENTIONS
title: Document the decision_log.md / project/memory/decisions two-tier model and add DEC-* ID convention
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/design.md
  - project/memory/decisions/precedence_semantics.md
  - project/memory/decision_log.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_decision
  - add_decision_schema
acceptance:
  - design.md documents the two-tier decision model (decision_log.md vs project/memory/decisions/<slug>.md) and the promotion criterion, citing precedence_semantics.md as the worked example
  - "project/memory/decisions/precedence_semantics.md has valid YAML frontmatter including an id: DEC-* field"
  - lrh validate reports 0 errors
  - project/memory/decision_log.md is unmodified
  - No new schema files added under project/design/schemas/
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/design/design.md
  - project/memory/decisions/precedence_semantics.md
---

# WI-DECISION-RECORD-CONVENTIONS

## Summary

Document LRH's existing two-tier decision-recording model — `decision_log.md`
for routine decisions, `project/memory/decisions/<slug>.md` for decisions
promoted into independently-cited canonical files — and introduce a `DEC-*`
id convention for the promoted tier.

## Problem / Context

`project/design/design.md:393` references `memory/decision_log.md` but never
explains its relationship to `project/memory/decisions/precedence_semantics.md`,
a separate promoted-decision file cited from 13 other locations across the
repo (`AGENTS.md`, `architecture.md`, `repository_spec.md`,
`docs/explanations/precedence-model.md`, three work items, and an unadopted
proposal). This ambiguity is not hypothetical: it caused an AI assistant
working in this repo to conclude `decision_log.md` had "never been built"
mid-session, when it has in fact been in active use since project bootstrap
(`src/lrh/assist/templates/request/bootstrap_project.md:276-284`) with 9
dated entries from 2026-04-03 to 2026-04-23. Scoped via `/lrh-design` rather
than `/lrh-proposal`, since it requires no novel architectural decision —
only documenting and naming a pattern that already exists in practice.

## Scope

- Add a subsection to `design.md` documenting the two-tier model and its
  promotion criterion.
- Add a `DEC-*` id frontmatter convention for `project/memory/decisions/*.md`
  files only.
- Retrofit the id onto the existing `precedence_semantics.md` file.

## Required Changes

1. Add a subsection near `design.md` §14 (Revision Policy) explaining:
   `decision_log.md` is the default landing spot for routine decisions;
   `project/memory/decisions/<slug>.md` is for decisions promoted out of the
   log because other documents need to cite them independently and
   repeatedly, outside the log's chronological narrative. Use
   `precedence_semantics.md` as the worked example.
2. Define the `DEC-*` id convention (SCREAMING-KEBAB-CASE, matching
   `WI-*`/`PROP-*` style) for `project/memory/decisions/*.md` files.
3. Add a YAML frontmatter block with `id: DEC-PRECEDENCE-SEMANTICS` (or a
   better slug) to `project/memory/decisions/precedence_semantics.md`,
   which currently has no frontmatter at all.

## Non-Goals

- Do not add a JSON schema for `project/memory/decisions/` or
  `decision_log.md`.
- Do not add `lrh validate` coverage/enforcement for either mechanism.
- Do not change `decision_log.md`'s format or edit any of its 9 historical
  entries.
- Do not create a second `project/memory/decisions/` file — none is
  currently warranted; fabricating one to "prove" the convention would
  misrepresent project history.
- Do not implement the `/lrh-decision` skill discussed earlier in the same
  conversation — that is future, separate work contingent on this
  convention proving out.

## Acceptance Criteria

- `design.md` documents the two-tier model and promotion criterion, citing
  `precedence_semantics.md` as the worked example.
- `project/memory/decisions/precedence_semantics.md` has valid YAML
  frontmatter including an `id: DEC-*` field.
- `lrh validate` reports 0 errors.
- `project/memory/decision_log.md` is unmodified.
- No new schema files added under `project/design/schemas/`.

## Validation

- `lrh validate`
- `grep -n "id:" project/memory/decisions/precedence_semantics.md`
- `git diff --stat project/memory/decision_log.md`

## Risk Notes

- `precedence_semantics.md` currently has no YAML frontmatter block; adding
  one must not disturb its existing Markdown body structure, which is cited
  by section anchors from other docs (e.g. `## Options considered`).
- `design.md`'s Revision Policy section already exists; the new subsection
  must integrate without duplicating the existing `decision_log.md`
  reference at line 393.

## Related Workstream and Designs

- `project/design/design.md` (§14 Revision Policy; Precedence Model section)
- `project/memory/decisions/precedence_semantics.md`
- `project/memory/decision_log.md`
- No workstream — scoped directly as a standalone work item via `/lrh-design`
