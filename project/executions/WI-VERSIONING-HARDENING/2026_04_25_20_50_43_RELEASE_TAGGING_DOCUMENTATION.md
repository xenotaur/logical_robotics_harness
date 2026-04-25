---
execution_id: 2026_04_25_20_50_43_RELEASE_TAGGING_DOCUMENTATION
prompt_id: PROMPT(WI-VERSIONING-HARDENING:RELEASE_TAGGING_DOCUMENTATION)[2026-04-25T02:30:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T20:50:43+00:00
---

# Summary

Document release tagging and packaging workflow in the repository README, with concise instructions aligned to current `scripts/version` behavior and `setuptools-scm` dynamic versioning.

# Result

Added a new `## Release workflow` section to `README.md` covering `vMAJOR.MINOR.PATCH` tagging, `scripts/version` subcommands (`tools`, `verify`, `tag`, `push`), and `python -m build` for sdist/wheel creation with tag-derived version metadata.

# Validation

- `scripts/version --help`
- `scripts/prompts/record-execution --help`

# Follow-up

Update `pr` and `commit` fields in this execution record after PR/merge if needed for final traceability.
