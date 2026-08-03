---
execution_id: 2026_08_03_03_20_27_WI_CODEX_CONVERSATION_EXPORT_MANIFEST
prompt_id: PROMPT(AD_HOC:WI_CODEX_CONVERSATION_EXPORT_MANIFEST)[2026-08-03T03:01:06+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/472
commit:
agent: codex_app
instruction_source: project/work_items/proposed/WI-CODEX-CONVERSATION-EXPORT-MANIFEST.md
session_transcript: pending
created_at: 2026-08-03T03:20:27+00:00
---

# Summary

Create the proposed work item
`WI-CODEX-CONVERSATION-EXPORT-MANIFEST`.

# Result

Created
`project/work_items/proposed/WI-CODEX-CONVERSATION-EXPORT-MANIFEST.md` as the
first implementation leaf for `WS-LRH-CODEX-CONVERSATION-EXPORTER`.

The item is a prompt-ready deliverable for defining the
`ConversationExportManifest` contract under `src/lrh/conversations/`, with
adapter, `inspect-export` CLI, viewer, and `session_transcript` grammar changes
explicitly out of scope.

# Validation

- `python -m lrh.cli.main prompt check-execution --slug wi-codex-conversation-export-manifest --work-item AD_HOC --project-root .` found no prior execution record.
- `python -m lrh.cli.main prompt check-execution --prompt-id 'PROMPT(AD_HOC:WI_CODEX_CONVERSATION_EXPORT_MANIFEST)[2026-08-03T03:01:06+00:00]' --project-root .` found no existing record for the freshly minted prompt ID.
- `python -m lrh.cli.main validate`: 0 errors, 0 warnings.
- `python -m lrh.cli.main work-items readiness WI-CODEX-CONVERSATION-EXPORT-MANIFEST --format md`: `prompt_ready: yes`.
- `git diff --check`: clean.

# Follow-up

Add `WI-CODEX-CONVERSATION-EXPORT-MANIFEST` to
`WS-LRH-CODEX-CONVERSATION-EXPORTER`'s `work_items:` list if approved, then
land PR #472 and execute the work item through `/lrh-execute`.
