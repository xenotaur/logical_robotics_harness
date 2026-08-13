---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-DOC-RELATED-DESIGN-REPOINT
title: Repoint three resolved doc-skills WIs' related_design at the adopted proposal
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-doc-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_proposal
  - implement_lrh_workstream
  - implement_lrh_design_step4
acceptance:
  - WI-SKILLS-LRH-DOC-AUDIT related_design points at project/design/proposals/adopted/lrh-doc-skills/00_proposal.md
  - WI-SKILLS-LRH-DOC-ORGANIZE related_design points at the same adopted path
  - WI-SKILLS-LRH-DOC-WORK related_design points at the same adopted path
  - lrh work-items validate reports no unresolved-metadata-reference warning for any of the three
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - validation_output
artifacts_expected:
  - project/work_items/resolved/WI-SKILLS-LRH-DOC-AUDIT.md
  - project/work_items/resolved/WI-SKILLS-LRH-DOC-ORGANIZE.md
  - project/work_items/resolved/WI-SKILLS-LRH-DOC-WORK.md
---

## Summary

Update the `related_design` metadata reference in three resolved work items
(`WI-SKILLS-LRH-DOC-AUDIT`, `WI-SKILLS-LRH-DOC-ORGANIZE`,
`WI-SKILLS-LRH-DOC-WORK`) to point at the `lrh-doc-skills` proposal at its
current adopted location, resolving three
`unresolved-metadata-reference` warnings from `lrh work-items validate`.

## Problem / Context

The `lrh-doc-skills` design proposal moved from
`project/design/proposals/proposed/lrh-doc-skills/00_proposal.md` to
`project/design/proposals/adopted/lrh-doc-skills/00_proposal.md` when it was
adopted. The three doc-skills work items that reference it were resolved
against the old `proposed/` path and were never repointed, so each now carries
a `related_design` reference to a path that no longer exists.

`lrh validate` passes (0 errors), but `lrh work-items validate` emits a
`unresolved-metadata-reference` **warning** for each of the three:

```
Metadata field 'related_design' references unresolved artifact
project/design/proposals/proposed/lrh-doc-skills/00_proposal.md.
```

Discovered while running `lrh work-items validate` during the
`WI-SKILLS-NEXT-STEP-CHAIN` work (PRs #412/#413); recorded there as
out-of-scope follow-up. Pre-existing and independent of that change.

## Scope

- The `related_design` frontmatter field in the three named resolved WI files.
- No body or other frontmatter changes; no change to the resolved status of
  any item.

## Required Changes

For each of the three files under `project/work_items/resolved/`
(`WI-SKILLS-LRH-DOC-AUDIT.md`, `WI-SKILLS-LRH-DOC-ORGANIZE.md`,
`WI-SKILLS-LRH-DOC-WORK.md`), change the `related_design` entry:

```
-   - project/design/proposals/proposed/lrh-doc-skills/00_proposal.md
+   - project/design/proposals/adopted/lrh-doc-skills/00_proposal.md
```

## Non-Goals

- Do not change any WI's `status`, `resolution`, or any field other than
  `related_design`.
- Do not modify the `lrh-doc-skills` proposal itself, or any skill.
- Do not touch any WI other than the three named here, even if other
  `unresolved-metadata-reference` warnings exist for unrelated causes.

## Acceptance Criteria

- All three files' `related_design` point at
  `project/design/proposals/adopted/lrh-doc-skills/00_proposal.md`.
- `lrh work-items validate` emits no `unresolved-metadata-reference` warning
  for any of the three (verify the specific warnings are gone, not merely that
  the count dropped).
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `lrh work-items validate`
