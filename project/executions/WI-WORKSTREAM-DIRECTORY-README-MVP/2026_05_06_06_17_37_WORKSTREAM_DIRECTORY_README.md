---
execution_id: 2026_05_06_06_17_37_WORKSTREAM_DIRECTORY_README
prompt_id: PROMPT(WI-WORKSTREAM-DIRECTORY-README-MVP:WORKSTREAM_DIRECTORY_README)[2026-05-06T09:00:00-04:00]
work_item: WI-WORKSTREAM-DIRECTORY-README-MVP
status: in_progress
rerun_of:
pr: pending
commit: pending
created_at: 2026-05-06T06:17:37+00:00
---

# Summary

Added the first human-facing `project/workstreams/` home for the Workstream Control Plane MVP,
linked to work item `WI-WORKSTREAM-DIRECTORY-README-MVP`.

# Result

- Added the initial workstream directory buckets: `proposed/`, `active/`, `resolved/`, and
  `abandoned/`, each tracked with `.gitkeep` placeholders.
- Added `project/workstreams/README.md` documenting purpose, the Project -> Workstream -> Work
  Item vocabulary, status buckets, metadata authority, status versus stage, the large-work
  lifecycle, relationships to work items and execution records, and directory-MVP non-goals.
- Updated `project/work_items/README.md` with a small navigational note to the new workstream
  directory documentation.

# Validation

- `scripts/version tools` completed and reported available tool versions.
- Manually inspected changed Markdown for heading structure, line wrapping, paths, and consistency
  with the accepted workstream proposal and work-item bucket conventions.
- `find project/workstreams -maxdepth 2 -type f | sort` confirmed the README and placeholder files
  exist.
- `scripts/test` passed: 336 tests.
- `scripts/lint` passed Ruff and Black checks.

# Follow-up

Generate a prompt for `WI-WORKSTREAM-SCHEMA-MVP`, the Workstream Schema MVP work item.
