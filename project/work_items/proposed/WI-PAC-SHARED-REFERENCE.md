---
resolution: null
blocked_reason: null
blocked: false
id: WI-PAC-SHARED-REFERENCE
title: Create shared prior-art-check reference and backlog entry
type: deliverable
status: proposed
owner: anthony
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-PRIOR-ART-CHECK
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_wi_pac_design_skills
  - implement_wi_pac_impl_skills
acceptance:
  - src/lrh/skills/_shared/prior-art-check.md exists with the 3-part search procedure (in-repo / sibling-repo / external library)
  - project/design/backlog.md exists with the validator drift-check entry
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/_shared/prior-art-check.md
  - project/design/backlog.md
---

## Summary

Create the canonical prior-art-check procedure at
`src/lrh/skills/_shared/prior-art-check.md` and initialize
`project/design/backlog.md` with the deferred validator drift-check entry.

## Problem / Context

Five LRH skills (`/lrh-design`, `/lrh-proposal`, `/lrh-workstream`,
`/lrh-work-item`, `/lrh-implement`) have no structured "has this already
been built?" check before committing new designs or code. A real duplication
incident in a sibling repo (LCATS) motivated `WS-PRIOR-ART-CHECK` to add
this check. The shared reference doc authored here is the dependency for the
two wiring work items (`WI-PAC-DESIGN-SKILLS`, `WI-PAC-IMPL-SKILLS`).

The `_shared/` directory is excluded from `lrh skills install` by the
leading-underscore convention in `src/lrh/skills/installer.py:41` — no
installer change is needed.

## Scope

- Create `src/lrh/skills/_shared/prior-art-check.md` with the 3-part search
  procedure and required output format
- Create `project/design/backlog.md` with the deferred validator drift-check
  entry (noting sync between copies as comment-only/manual for now)

## Required Changes

- `src/lrh/skills/_shared/prior-art-check.md` — new file; canonical source
  for the prior-art-check procedure
- `project/design/backlog.md` — new file; backlog entry for automated drift
  enforcement via `lrh validate`

## Non-Goals

- Does not copy the reference into individual skills — that is
  `WI-PAC-DESIGN-SKILLS` and `WI-PAC-IMPL-SKILLS`
- Does not add automated drift-checking between the `_shared/` master and
  per-skill copies

## Acceptance Criteria

- `src/lrh/skills/_shared/prior-art-check.md` exists with the 3-part search
  procedure (in-repo / sibling-repo / external library) and required output
  format
- `project/design/backlog.md` exists with the validator drift-check entry
- `lrh validate` reports 0 errors

## Validation

- `lrh validate`
