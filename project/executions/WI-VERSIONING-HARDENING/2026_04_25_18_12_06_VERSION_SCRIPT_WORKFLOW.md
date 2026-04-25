---
execution_id: 2026_04_25_18_12_06_VERSION_SCRIPT_WORKFLOW
prompt_id: PROMPT(WI-VERSIONING-HARDENING:VERSION_SCRIPT_WORKFLOW)[2026-04-25T02:30:00-04:00]
work_item: WI-VERSIONING-HARDENING
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T18:12:06+00:00
---

# Summary

Refactor `scripts/version` into a structured subcommand workflow and move
release logic into `src/lrh/dev/versioning.py`.

# Result

- Added `scripts/version` wrapper that delegates to `python -m lrh.dev.versioning`.
- Implemented `tools`, `verify [tag]`, `tag <tag>`, and `push <tag>` commands.
- Implemented clean-tree/lint/format/test verification checks.
- Added idempotent and safety checks for local tagging and remote tag pushes.
- Updated script documentation and added tests.

# Validation

- `scripts/format src/lrh/dev tests/dev_tests tests/scripts_tests`
- `scripts/lint src/lrh/dev tests/dev_tests tests/scripts_tests`
- `scripts/test`
- `scripts/version --help`
- `scripts/version`

# Follow-up

- Populate `pr` and `commit` metadata after PR merge tracking is available.
