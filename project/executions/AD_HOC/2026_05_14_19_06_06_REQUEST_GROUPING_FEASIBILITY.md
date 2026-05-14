---
execution_id: 2026_05_14_19_06_06_REQUEST_GROUPING_FEASIBILITY
prompt_id: PROMPT(AD_HOC:REQUEST_GROUPING_FEASIBILITY)[2026-05-05T14:00:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T19:06:06+00:00
---

# Summary

Evaluated whether grouped `lrh request` subcommands should be added after the
flat canonical request catalog and `list` / `describe` discoverability commands.

# Result

Deferred grouped request subcommands. The current catalog has nine primary
user-facing requests; only `review` and `ci` have more than one request, and each
has only two. `lrh request list` is already short and grouped by category, while
`lrh request --help` remains a single flat template-rendering surface that points
users to the catalog commands. Added the defer decision, supporting evidence, and
future trigger conditions to `project/design/request_command_naming.md`.

# Validation

- `scripts/version tools`
- `lrh prompt check-execution --prompt-id 'PROMPT(AD_HOC:REQUEST_GROUPING_FEASIBILITY)[2026-05-05T14:00:00-04:00]' --project-root .`
- `lrh request --help`
- `lrh request list`
- `scripts/lint`
- `scripts/format`
- `scripts/test`
- `scripts/validate`

# Follow-up

Revisit grouped request subcommands only if the catalog grows, category-specific
flags or validation rules emerge, help/completion output becomes hard to scan, or
user documentation starts teaching request families more often than individual
canonical flat names.
