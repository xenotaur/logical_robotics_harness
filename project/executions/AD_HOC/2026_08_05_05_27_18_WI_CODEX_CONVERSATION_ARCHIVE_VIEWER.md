---
execution_id: 2026_08_05_05_27_18_WI_CODEX_CONVERSATION_ARCHIVE_VIEWER
prompt_id: PROMPT(AD_HOC:WI_CODEX_CONVERSATION_ARCHIVE_VIEWER)[2026-08-04T22:41:10+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/486
commit:
created_at: 2026-08-05T05:27:18+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-CONVERSATION-ARCHIVE-VIEWER.md
session_transcript: none
---

# Summary

Create a proposed LRH work item for the safe-default Codex conversation archive
viewer follow-up under `WS-LRH-CODEX-CONVERSATION-EXPORTER`.

# Result

Created `project/work_items/proposed/WI-CODEX-CONVERSATION-ARCHIVE-VIEWER.md`.
The work item captures the deferred `lrh serve` local read-only archive viewer
slice after the manifest, file adapter, and `inspect-export` CLI work items
landed.

The item is scoped to explicit archive-root configuration, reuse of
`ConversationExportManifest` and `lrh.conversations.export_inspector`, inert
read-only transcript rendering, and documentation of privacy, authority,
sensitivity, and promotion boundaries. It intentionally excludes
`session_transcript` grammar changes, undocumented Codex app storage internals,
automatic promotion, broad conversation search, and private transcript fixtures.

Opened draft PR #486:
https://github.com/xenotaur/logical_robotics_harness/pull/486

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate` — 0 errors, 0 warnings.
- `PYTHONPATH=src python -m lrh.cli.main work-items readiness WI-CODEX-CONVERSATION-ARCHIVE-VIEWER --format md` — prompt_ready: yes.
- `git diff --check` — clean.

# Follow-up

Ask whether to update
`project/workstreams/proposed/WS-LRH-CODEX-CONVERSATION-EXPORTER.md` so its
`work_items:` list includes `WI-CODEX-CONVERSATION-ARCHIVE-VIEWER`; the
`/lrh-work-item` skill requires explicit approval before editing the workstream.
