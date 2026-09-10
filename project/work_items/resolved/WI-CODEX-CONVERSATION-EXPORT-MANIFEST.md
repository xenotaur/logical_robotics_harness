---
resolution: 'Implemented and merged in PR #476 (commit d4301e2bff808ea9c7464a756cc3f91be41677a2).'
blocked_reason: null
blocked: false
id: WI-CODEX-CONVERSATION-EXPORT-MANIFEST
title: Define Codex conversation export manifest contract
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-LRH-CODEX-CONVERSATION-EXPORTER
related_design:
  - project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_codex_file_adapter
  - implement_inspect_export_cli
  - implement_lrh_serve_viewer
  - modify_session_transcript_schema
acceptance:
  - '`ConversationExportManifest` or an equivalent typed helper exists under `src/lrh/conversations/` and models the Codex export manifest contract'
  - Manifest helpers preserve private-by-default, non-authoritative defaults and include schema version, source tool/adapter, source hash, export timestamp, adapter version, warning list, sensitivity metadata, and transcript statistics
  - Manifest rendering/parsing or serialization helpers have focused unit tests for valid manifests, malformed or missing required fields, default handling, and stable output
  - Documentation describes the manifest fields and explicitly states that raw Codex exports remain private, non-authoritative context
  - The work item does not implement the file-based Codex adapter, `inspect-export` CLI, viewer support, or `session_transcript` grammar changes
  - '`lrh validate` reports 0 errors'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/export_manifest.py
  - src/lrh/conversations/__init__.py
  - tests/conversations_tests/export_manifest_test.py
  - docs/reference/cli/conversation.md
---

# Define Codex conversation export manifest contract

## Summary

Define the typed manifest contract for Codex conversation export artifacts so
later adapter and inspector work can share a stable, tested representation of
private, non-authoritative transcript metadata.

## Problem / Context

`PROP-LRH-CODEX-CONVERSATION-EXPORTER` chooses a Markdown transcript plus
structured manifest as the artifact shape for Codex session exports. The
workstream `WS-LRH-CODEX-CONVERSATION-EXPORTER` sequences this contract before
the file-based adapter, inspection CLI, and deferred viewer work so later
implementation slices do not encode competing metadata shapes.

Existing ChatGPT PDF conversion already writes private,
non-authoritative Markdown frontmatter, but that path is specific to PDF
conversion and does not define a reusable Codex export manifest contract. This
item creates that contract and its tests without implementing capture, import,
inspection, or viewing behavior.

### Duplication search
- In-repo: Related but not duplicate. `src/lrh/conversations/pdf_import.py`
  renders ChatGPT PDF transcript frontmatter with privacy, authority,
  sensitivity, source hash, timestamp, adapter version, and warnings, and
  `docs/reference/cli/conversation.md` documents that behavior. No
  `ConversationExportManifest` or reusable Codex export manifest helper exists.
- Sibling repos: None identified.
- External libraries: None identified that provides LRH-specific Codex export
  authority, privacy, sensitivity, provenance, and transcript-statistics
  metadata.
- Recommendation: Proceed by extending `src/lrh/conversations/` with a reusable
  manifest contract.

### Demand search
- Work items: None found for this manifest slice.
- Proposals: `PROP-LRH-CODEX-CONVERSATION-EXPORTER` explicitly lists defining
  `ConversationExportManifest` and related typed helpers as implementation
  step 1.
- Backlog: The canonical Codex skill-adaptation backlog notes transcript/export
  pointer gaps, but this manifest work item does not close those backlog entries
  by itself.
- Recommendation: Link this item to `WS-LRH-CODEX-CONVERSATION-EXPORTER` and
  create later work items for the adapter, inspector, docs expansion, and
  deferred viewer follow-up.

## Scope

- Define the manifest data model for LRH Codex conversation exports.
- Provide helper behavior needed by later adapter and inspector work, such as
  defaults, serialization/parsing, required-field validation, and transcript
  statistics.
- Keep privacy and authority defaults private and non-authoritative.
- Document the field contract at the CLI/conversation reference level.

## Required Changes

1. Add `src/lrh/conversations/export_manifest.py` with a typed
   `ConversationExportManifest` model or equivalent helper API. The model must
   capture at least: `kind`, `schema_version`, `source_tool`, `source_adapter`,
   `privacy`, `authority`, `sensitivity`, `sensitivity_scan`, `source_id` when
   available, source hash, export timestamp, adapter version, warning list, and
   transcript statistics.
2. Define stable constants or helper functions for the default values required
   by the governing proposal: private privacy, non-authoritative context,
   Codex source-tool metadata, and a schema version.
3. Add serialization and parsing/validation helpers appropriate to the existing
   conversation package style. The helpers should produce deterministic output
   suitable for later Markdown-plus-manifest writing and machine inspection.
4. Add transcript-statistics support for at least byte count, character count,
   line count, and optional turn/message count when an adapter can provide it.
5. Export the public helper(s) through `src/lrh/conversations/__init__.py` if
   that is the local package convention.
6. Add `tests/conversations_tests/export_manifest_test.py` covering valid
   manifests, required-field failures, default handling, sensitivity metadata,
   warning lists, transcript statistics, and stable serialized output.
7. Update `docs/reference/cli/conversation.md` or adjacent conversation docs to
   describe the manifest contract and note that adapter, inspector, and viewer
   behavior are separate follow-up work.

## Non-Goals

- Do not implement the file-based Codex adapter.
- Do not implement `lrh conversation inspect-export`.
- Do not implement `lrh serve` archive viewing or any conversation UI.
- Do not change execution-record `session_transcript` grammar.
- Do not commit raw Codex transcript exports to this repository.
- Do not promise redaction or public-export safety; sensitivity scanning remains
  heuristic and non-certifying.

## Acceptance Criteria

- `ConversationExportManifest` or an equivalent typed helper exists under
  `src/lrh/conversations/` and models the Codex export manifest contract.
- Manifest helpers preserve private-by-default, non-authoritative defaults and
  include schema version, source tool/adapter, source hash, export timestamp,
  adapter version, warning list, sensitivity metadata, and transcript
  statistics.
- Manifest rendering/parsing or serialization helpers have focused unit tests
  for valid manifests, malformed or missing required fields, default handling,
  and stable output.
- Documentation describes the manifest fields and explicitly states that raw
  Codex exports remain private, non-authoritative context.
- The work item does not implement the file-based Codex adapter,
  `inspect-export` CLI, viewer support, or `session_transcript` grammar
  changes.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `python -m lrh.cli.main validate`
- `python -m unittest tests.conversations_tests.export_manifest_test`

## Risk Notes

- The manifest shape will become a contract consumed by later adapter,
  inspector, and viewer work, so avoid underspecified or adapter-specific field
  names.
- Reusing PDF frontmatter patterns is useful, but this item should not bake PDF
  import assumptions into Codex export metadata.
- Sensitivity metadata must keep the existing non-certification posture clear.

## Dependencies / Order

This is the first implementation work item for
`WS-LRH-CODEX-CONVERSATION-EXPORTER`. It has no work-item dependencies. The
file-based Codex adapter and `inspect-export` CLI should depend on this item or
at least consume its resulting manifest helper.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- Governing proposal:
  `project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md`
- Broader conversation storage proposal:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Related session archive proposal:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
