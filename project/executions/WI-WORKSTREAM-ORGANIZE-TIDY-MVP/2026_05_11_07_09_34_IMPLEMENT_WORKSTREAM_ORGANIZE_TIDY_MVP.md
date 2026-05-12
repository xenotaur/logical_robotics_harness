---
execution_id: 2026_05_11_07_09_34_IMPLEMENT_WORKSTREAM_ORGANIZE_TIDY_MVP
prompt_id: PROMPT(WI-WORKSTREAM-ORGANIZE-TIDY-MVP:IMPLEMENT_WORKSTREAM_ORGANIZE_TIDY_MVP)[2026-05-06T11:30:00-04:00]
work_item: WI-WORKSTREAM-ORGANIZE-TIDY-MVP
status: landed
rerun_of: null
pr: null
commit: null
created_at: 2026-05-11T07:09:34+00:00
---

# Summary

Implemented the Workstream Organize/Tidy MVP as a focused, dry-run-first maintenance command for
`project/workstreams/`.

# Result

- Added `lrh workstreams organize` with safe default preview behavior.
- Added `--dry-run` and `--apply` flags, with `--apply` required before any file moves occur.
- Used workstream frontmatter `status` as the authoritative source of truth for status-bucket
  placement:
  - `proposed` -> `project/workstreams/proposed/`
  - `active` -> `project/workstreams/active/`
  - `resolved` -> `project/workstreams/resolved/`
  - `abandoned` -> `project/workstreams/abandoned/`
- Preserved workstream filenames, IDs, frontmatter, stages, relationships, and file contents during
  organization.
- Reported invalid workstream metadata and destination conflicts without guessing or moving unsafe
  files.
- Added unit coverage for dry-run output, no-mutation behavior, apply moves, already-correct files,
  ignored README/placeholder files, invalid status handling, destination conflict handling, content
  preservation, and deterministic multi-move output.
- Updated `project/workstreams/README.md` to document explicit organize behavior and its safety
  constraints.

# Validation

- `scripts/version tools` passed; Black and Ruff versions were available in the task environment.
- `scripts/format --check` initially reported that the new organize module needed formatting.
- `scripts/format` reformatted the new organize module.
- `scripts/lint` passed after formatting.
- `scripts/test` passed with 438 unit tests.

# Follow-up

Pause and review the Workstream Control Plane MVP before moving toward execution readiness,
run-packet generation, or any future `lrh run` / autonomous execution work. This change deliberately
avoids automated lifecycle advancement, stage/status rewriting, agent execution, execution backends,
or orchestration.
