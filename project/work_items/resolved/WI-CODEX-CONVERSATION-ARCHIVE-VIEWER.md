---
resolution: "Implemented safe-default Codex conversation archive viewing and merged in PR #492 (commit 59ae473d)."
blocked_reason: null
blocked: false
id: WI-CODEX-CONVERSATION-ARCHIVE-VIEWER
title: Implement safe-default Codex conversation archive viewer
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
depends_on:
  - WI-CODEX-CONVERSATION-EXPORT-MANIFEST
  - WI-CODEX-CONVERSATION-EXPORT-ADAPTER
  - WI-CODEX-CONVERSATION-INSPECT-EXPORT
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_session_transcript_schema
  - depend_on_undocumented_codex_app_storage_internals
  - commit_raw_transcript_exports
  - commit_private_transcript_fixtures
  - expose_nonlocal_server_by_default
  - implement_promotion_workflow
  - implement_full_conversation_ledger
  - echo_transcript_content_by_default
acceptance:
  - '`lrh serve` can expose a local-only, read-only view of explicitly configured Codex conversation export archive roots'
  - The viewer consumes the existing `ConversationExportManifest` and `inspect-export` validation contract rather than inventing a second transcript schema
  - The viewer prominently displays privacy, authority, sensitivity, warning counts, validation status, and transcript statistics before showing transcript content
  - Transcript content is escaped and rendered as inert read-only data; the viewer does not browse arbitrary filesystem paths or execute actions
  - Focused tests cover archive-root configuration, local-only defaults, valid and invalid export handling, content escaping, and non-disclosure of private transcript fixtures
  - Documentation explains configuration, privacy/authority boundaries, limitations, and the separation from promotion and `session_transcript` grammar changes
  - '`lrh validate` reports 0 errors'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/serve.py
  - tests/cli_tests/serve_test.py
  - docs/reference/cli/serve.md
  - docs/reference/cli/conversation.md
  - docs/conversations/conversation-capture-options.md
---

# Implement safe-default Codex conversation archive viewer

## Summary

Implement safe-default `lrh serve` support for viewing explicitly configured
Codex conversation export archive roots as private, read-only, non-authoritative
context.

## Problem / Context

`WS-LRH-CODEX-CONVERSATION-EXPORTER` has now landed the manifest, file adapter,
and deterministic `inspect-export` CLI slices. The remaining workstream exit
criterion requires viewer support to be implemented through safe-default
`lrh serve` archive viewing or explicitly deferred with a follow-up work item.
This item captures that follow-up so the viewer can consume the stable export
artifact contract without making raw transcripts authoritative project state.

### Duplication search
- In-repo: Related but not duplicate. `lrh serve` already provides a local
  read-only viewer skeleton, and `lrh conversation inspect-export` validates
  Codex export artifacts, but no Codex conversation archive viewer route or
  archive-root configuration exists.
- Sibling repos: None identified.
- External libraries: None identified that provides LRH-specific safe-default
  viewing of private Codex export artifacts with LRH privacy, authority,
  sensitivity, and promotion boundaries.
- Recommendation: Proceed by extending the existing `lrh serve` surface and
  reusing `lrh.conversations` manifest/inspection helpers.

### Demand search
- Work items: The three prerequisite Codex exporter items are resolved; no
  proposed viewer work item exists yet.
- Proposals: `PROP-LRH-CODEX-CONVERSATION-EXPORTER` chooses a deferred
  `lrh serve` local read-only archive viewer after the export contract and
  inspector are stable.
- Backlog: The Codex conversation export/provenance gap is represented by the
  exporter proposal and workstream.
- Recommendation: Link this item to `WS-LRH-CODEX-CONVERSATION-EXPORTER` and
  leave proposal adoption/update for a later closeout step.

## Scope

- Extend `lrh serve` with a safe-default way to view Codex conversation export
  artifacts under explicitly configured archive roots.
- Reuse the existing `ConversationExportManifest` and `inspect-export`
  validation behavior to classify artifacts before display.
- Show transcript content only as escaped, inert, read-only data after metadata
  and warning context is visible.
- Preserve private-by-default and non-authoritative boundaries throughout the UI
  and documentation.

## Required Changes

1. Define how Codex archive roots are configured for `lrh serve`, preferring an
   explicit opt-in configuration path over implicit filesystem discovery.
2. Extend the serve projection/model layer to enumerate configured Codex export
   Markdown artifacts without arbitrary filesystem browsing.
3. Reuse `lrh.conversations.export_inspector` to validate each export and expose
   metadata, warning counts, source-hash status, and transcript-statistic status
   to the viewer.
4. Add read-only routes or panels to `lrh serve` for archive lists and individual
   export views.
5. Render transcript content as escaped inert text, never as executable HTML,
   Markdown with unsafe rendering, or interactive command input.
6. Add focused tests for configuration, local-only defaults, missing/invalid
   exports, validation metadata display, transcript escaping, and privacy
   boundaries.
7. Update `docs/reference/cli/serve.md`, `docs/reference/cli/conversation.md`,
   and conversation guidance docs to describe the viewer workflow and limits.

## Non-Goals

- Do not import transcript text into `project/` control-plane artifacts.
- Do not make conversation exports authoritative evidence, decisions, work
  items, or status.
- Do not implement automatic promotion from transcript content to project
  artifacts.
- Do not change execution-record `session_transcript` pointer grammar.
- Do not depend on undocumented Codex app storage internals.
- Do not add broad conversation search, a full conversation ledger, or a general
  chat UI.
- Do not bind `lrh serve` to non-local hosts by default.
- Do not commit private transcript fixtures or raw exports.

## Acceptance Criteria

- `lrh serve` can expose a local-only, read-only view of explicitly configured
  Codex conversation export archive roots.
- The viewer consumes the existing `ConversationExportManifest` and
  `inspect-export` validation contract rather than inventing a second transcript
  schema.
- The viewer prominently displays privacy, authority, sensitivity, warning
  counts, validation status, and transcript statistics before showing transcript
  content.
- Transcript content is escaped and rendered as inert read-only data; the viewer
  does not browse arbitrary filesystem paths or execute actions.
- Focused tests cover archive-root configuration, local-only defaults, valid and
  invalid export handling, content escaping, and non-disclosure of private
  transcript fixtures.
- Documentation explains configuration, privacy/authority boundaries,
  limitations, and the separation from promotion and `session_transcript`
  grammar changes.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `PYTHONPATH=src python -m unittest tests.cli_tests.serve_test`
- `PYTHONPATH=src scripts/test`
- `PYTHONPATH=src python -m lrh.cli.main validate`

## Risk Notes

- Viewer affordances could be mistaken for promotion unless the UI and docs keep
  raw transcripts clearly labeled as private, non-authoritative context.
- Archive-root handling could accidentally become arbitrary filesystem browsing;
  keep roots explicit and route access constrained.
- Rendering transcript text could introduce HTML/script injection risk unless
  content is escaped and treated as inert data.
- Tests must use synthetic fixture content only, not private real transcripts.

## Dependencies / Order

This item depends on the resolved manifest, file adapter, and inspector work.
It should run after those pieces are stable so `lrh serve` can consume the
existing validation contract instead of defining its own export semantics.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- Governing proposal: `project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md`
- Broader storage direction: `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Session archive context: `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
