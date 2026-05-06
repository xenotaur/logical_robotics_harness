---
execution_id: 2026_05_06_21_46_44_WORKSTREAM_SCHEMA_MVP
prompt_id: PROMPT(AD_HOC:WORKSTREAM_SCHEMA_MVP)[2026-05-06T10:00:00-04:00]
work_item: WI-WORKSTREAM-SCHEMA-MVP
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-05-06T21:46:44+00:00
---

# Summary

Defined the documentation-level Workstream Schema MVP for the Workstream Control Plane MVP, linked
it to `WI-WORKSTREAM-SCHEMA-MVP`, and kept the change limited to project-control documentation and a
small illustrative example artifact.

# Result

- Added `project/design/workstream_schema_mvp.md` documenting the minimal workstream
  metadata/frontmatter model, including required fields (`id`, `kind`, `title`, `status`, `stage`)
  and optional field vocabulary (`origin`, `parent_id`, `children`, `summary`, `rationale`,
  `related_focus`, `related_roadmap`, `work_items`, `execution_records`, `evidence`,
  `exit_criteria`, and `closeout`).
- Documented the initial `kind: planning_node` vocabulary without introducing subtype complexity.
- Documented coarse `status` semantics (`proposed`, `active`, `resolved`, `abandoned`) and
  fine-grained `stage` semantics (`conceived`, `assessed`, `designed`, `planned`, `executing`,
  `reviewing`, `closed`, `abandoned`) while leaving runtime validation rules deferred.
- Documented metadata-driven parent/child relationship semantics through `parent_id` and `children`,
  including future support for workstream-to-workstream, workstream-to-work-item, and project-root
  planning contexts without implementing planning-tree logic.
- Reaffirmed that workstream metadata/frontmatter is authoritative and directory placement is a
  navigational projection that future validators and organize/tidy commands may reconcile.
- Added `project/workstreams/proposed/WS-EXAMPLE.md` as a small illustrative proposed workstream
  using the documented MVP vocabulary.
- Updated `project/workstreams/README.md`, `project/design/design.md`,
  `project/design/proposals/README.md`, and the workstream schema work item for discoverability
  and work-item linkage.

# Validation

- Checked for prior execution records matching the exact prompt ID and found none.
- `scripts/version tools` completed and reported available tool versions.
- Manually inspected changed Markdown/YAML for heading structure, field consistency, readability,
  and alignment with the accepted workstream planning-tree proposal.
- A small Python line-length/readability scan was used to inspect changed Markdown files; no
  readability issues were found in the new schema and example workstream files.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed Ruff and Black checks.
- `scripts/test` passed: 336 tests.
- `lrh validate` passed with 0 errors and 0 warnings.

# Follow-up

Recommended next step: generate a prompt for `WI-WORKSTREAM-LOADER-MODEL-MVP` so typed workstream
model and loader work can begin from the documented schema without adding validation, snapshot,
organize/tidy, or execution behavior in this PR.
