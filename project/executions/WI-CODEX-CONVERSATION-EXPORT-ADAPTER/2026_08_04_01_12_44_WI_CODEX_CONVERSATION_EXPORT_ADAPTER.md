---
execution_id: 2026_08_04_01_12_44_WI_CODEX_CONVERSATION_EXPORT_ADAPTER
prompt_id: PROMPT(WI-CODEX-CONVERSATION-EXPORT-ADAPTER:WI_CODEX_CONVERSATION_EXPORT_ADAPTER)[2026-08-04T00:53:46+00:00]
work_item: WI-CODEX-CONVERSATION-EXPORT-ADAPTER
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/480
commit: a195f8415a3b4d43033c4495743a616cc10f7768
created_at: 2026-08-04T01:12:44+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-CONVERSATION-EXPORT-ADAPTER.md
session_transcript: none
---

# Summary

Implement `WI-CODEX-CONVERSATION-EXPORT-ADAPTER`: add a file-based Codex
conversation export adapter that accepts explicit local source/output paths and
writes private, non-authoritative Markdown artifacts with
`ConversationExportManifest` frontmatter.

# Result

- Added `src/lrh/conversations/codex_file_export.py` with reusable conversion,
  manifest-building, Markdown rendering, and CLI helper functions.
- Wired `lrh conversation convert-codex-file INPUT --out OUTPUT.md`.
- Exported the public adapter helpers from `lrh.conversations`.
- Documented the explicit-file workflow and privacy/authority boundaries.
- Added focused tests for successful conversion, output preflight failures,
  exact-path and hard-link source/output collision rejection, source hashing,
  transcript statistics, sensitivity warning propagation, stable frontmatter,
  and CLI error handling.

Prior-art check: present in the work item. Related in-repo artifacts were the
manifest contract, ChatGPT PDF importer, and conversation CLI docs; no duplicate
Codex file adapter existed.

Independent pre-push self-review found a blocking hard-link collision gap in
the initial source/output preflight. The implementation was fixed with
`Path.samefile()` handling for existing outputs and a hard-link regression test
before PR creation.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.8; Pyright
  not installed in this environment.
- `scripts/format --check --diff` — clean.
- `scripts/lint` — clean.
- `PYTHONPATH=src python -m unittest tests.conversations_tests.codex_file_export_test`
  — 10 tests OK.
- `PYTHONPATH=src scripts/test` — first sandboxed run failed because serve tests
  could not bind local sockets (`PermissionError: Operation not permitted`);
  rerun outside the sandbox passed, 917 tests OK.
- `PYTHONPATH=src python -m lrh.cli.main validate` — 0 errors, 0 warnings.
- Manual CLI smoke: `lrh conversation convert-codex-file` wrote manifest
  frontmatter and transcript body for an explicit local source file.
- `git diff --check` — clean.

# Follow-up

Continue the workstream with the planned export inspection CLI after this
adapter lands. Viewer support, `session_transcript` grammar changes, and native
Codex app/API capture remain out of scope.
