---
execution_id: 2026_05_17_22_48_33_LRH_DOCS_CURRENT_COMMAND_WORKFLOWS
prompt_id: PROMPT(AD_HOC:LRH_DOCS_CURRENT_COMMAND_WORKFLOWS)[2026-05-17T02:13:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-17T22:48:33+00:00
---

# Summary

Documented current implemented LRH command workflows and exact command surfaces for validation, snapshot, survey, request, and meta workflows. Added task-oriented how-to pages, CLI reference pages, and updated documentation indexes.

# Result

- Added how-to pages under `docs/how-to/` for project validation, snapshot generation, source-tree survey, request templates, meta registration, workspace inspection, and the developer sandbox.
- Added CLI reference pages under `docs/reference/cli/` for `validate`, `snapshot`, `survey`, `request`, and `meta`.
- Updated `docs/README.md`, `docs/how-to/README.md`, and `docs/reference/cli/README.md` to link the new documentation.
- No command behavior or CLI options were changed.

# Validation

- `scripts/version tools` — passed; Black and Ruff versions were available before lint/test validation.
- `python -m lrh.cli.main --help` — passed.
- `python -m lrh.cli.main validate --help` — passed.
- `python -m lrh.cli.main snapshot --help` — passed.
- `python -m lrh.cli.main survey --help` — passed.
- `python -m lrh.cli.main request --help` — passed.
- `python -m lrh.cli.main meta --help` — passed.
- `lrh validate --help`, `lrh snapshot --help`, `lrh survey --help`, `lrh request --help`, and `lrh meta --help` — passed with installed entry point.
- `scripts/lint` — passed.
- `scripts/test` — passed; 529 tests ran.
- `lrh validate` — passed with 0 errors and 0 warnings.
- Manual relative Markdown link check for added/updated docs — passed.

# Follow-up

None.
