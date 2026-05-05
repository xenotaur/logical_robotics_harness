---
execution_id: 2026_05_05_16_54_17_PLAN_WORKSTREAM_CONTROL_PLANE_MVP
prompt_id: PROMPT(AD_HOC:PLAN_WORKSTREAM_CONTROL_PLANE_MVP)[2026-05-05T12:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-05T16:54:17+00:00
---

# Summary

Planning-only control-plane update for the Workstream Control Plane MVP. Updated roadmap and
current focus to establish workstreams-first sequencing, created focused proposed work items for
implementation order, and added a navigation note in the work-items README.

# Result

- Roadmap now includes an explicit near-term Workstream Control Plane MVP goal and deliverable
  list, with deferred execution-framework/runtime layers called out.
- Current focus now names Workstream Control Plane MVP as active and clarifies manual/project-
  control-first scope.
- Added proposed work items for: directory/README, schema, loader/model, validation,
  planning-tree relationships, snapshot summary, and dry-run-first organize/tidy.
- Updated work-items README with a sequencing note aligning metadata authority and bucket
  projection behavior.

# Validation

- `scripts/version tools`
- `scripts/test`
- Manual review of changed Markdown for consistency and link/path correctness.

# Follow-up

Generate the next prompt package for the first concrete implementation work item:
`WI-WORKSTREAM-DIRECTORY-README-MVP` (or `WI-WORKSTREAM-SCHEMA-MVP` if reviewers prefer schema-
first sequencing).
