---
execution_id: 2026_05_14_04_42_55_REQUEST_CATALOG_FLAT_NAMES
prompt_id: PROMPT(AD_HOC:REQUEST_CATALOG_FLAT_NAMES)[2026-05-05T13:50:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-14T04:42:55+00:00
---

# Summary

Implemented a structured `lrh request` catalog and canonical hyphenated flat request names while preserving existing legacy and template-oriented names as compatibility aliases.

# Result

Added request metadata under `src/lrh/assist/request_catalog.py`, routed request CLI invocations through the catalog for known names, updated completion sources to expose catalog aliases, and refreshed assist request documentation with the canonical mapping table. Legacy names such as `improve_coverage` and `codex-prompt-from-work-item` remain supported.

# Validation

- `scripts/version tools`
- `scripts/format --check --diff` (initial review-update check found formatting changes before repair)
- `scripts/format`
- `scripts/format --check --diff`
- `scripts/lint`
- `git diff --check`
- `python -m unittest tests.assist_tests.request_catalog_test tests.assist_tests.request_cli_test tests.cli_tests.request_test tests.cli_tests.completion_sources_test`
- `scripts/test`
- `scripts/validate`
- `lrh request templates where improve-coverage && lrh request prompt-from-work-item project/work_items/active/WI-META-CLI-MVP.md --style-file STYLE.md --prompt-id 'PROMPT(WI-META-CLI-MVP:REQUEST_CATALOG_SMOKE)[2026-05-14T00:00:00+00:00]' | head -5`

# Review feedback update

Addressed review feedback by preserving generic `prompt-from-work-item` invocation, keeping canonical names in validation diagnostics, resolving catalog names in `templates where`, expanding acronym-based canonical names per `project/design/request_command_naming.md`, and adding focused CLI/completion tests.

# Follow-up

No grouped subcommands or short aliases were introduced; those remain deferred for future request-command design work. Keep this execution record `in_progress` until PR merge metadata is available.
