---
execution_id: 2026_08_13_03_49_59_DOC_WORK_WI_CODEX_CONVERSATION_EXPORT_SKILL
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_CODEX_CONVERSATION_EXPORT_SKILL)[2026-08-12T23:07:17+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/547
commit: 3adff45e8fb90283cae1d4c6732b642377f11b6d
agent: codex_app
instruction_source: WI-CODEX-CONVERSATION-EXPORT-SKILL
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
created_at: 2026-08-13T03:49:59+00:00
---

# Summary

Document the Codex conversation export skill after
`WI-CODEX-CONVERSATION-EXPORT-SKILL` landed, scoped to the Codex conversation
export documentation because the broader Codex exporter workstreams were already
resolved.

# Result

Opened PR #547 to add a Codex export how-to and update the conversation
documentation index and capture-options guide.

The documentation now covers `/lrh-codex-export` as the user-facing Codex app
workflow, points advanced users to `lrh conversation export-codex-thread`, and
reinforces the private-path and manifest-only inspection guidance from the
dogfood sessions.

# Validation

- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `lrh validate` passed with 0 errors and 1 pre-existing
  `WS-SESSION-ARCHIVE-SYNC` warning.
- `scripts/test` passed with 1086 tests OK.

# Follow-up

- Land PR #547 through the normal review/landing loop.
