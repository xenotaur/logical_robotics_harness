---
resolution: 'Implemented and merged in PR #484 at commit da1cfadb51b966b668d3dc1c65af3f8a1f0921ef.'
blocked_reason: null
blocked: false
id: WI-CODEX-CONVERSATION-INSPECT-EXPORT
title: Implement Codex conversation export inspector CLI
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
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_serve_viewer
  - modify_session_transcript_schema
  - depend_on_undocumented_codex_app_storage_internals
  - commit_raw_transcript_exports
  - commit_private_transcript_fixtures
  - echo_transcript_content_by_default
acceptance:
  - '`lrh conversation inspect-export <path> --format text|json` exists and validates Codex export Markdown artifacts with `ConversationExportManifest` frontmatter'
  - The inspector recomputes artifact body statistics and flags drift from manifest `transcript` byte, character, and line counts
  - The inspector reports manifest validity, privacy/authority metadata, sensitivity status and warnings, transcript statistics, and source-hash verification status when a source path is supplied
  - JSON output is deterministic and automation-friendly; text output is concise and human-readable; neither output mode includes raw transcript body, snippets, or message text by default
  - Focused tests cover valid exports, malformed or missing manifests, body-statistic drift, hash matches and mismatches, missing or unreadable source handling, sensitivity warning propagation, transcript-content non-disclosure in text and JSON output, CLI command wiring, `--format` choices, invalid export exit behavior, and stable text/JSON output
  - Documentation describes the inspection workflow and keeps viewer support, promotion, and `session_transcript` grammar changes out of scope
  - '`lrh validate` reports 0 errors'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/export_inspector.py
  - src/lrh/conversations/__init__.py
  - src/lrh/cli/main.py
  - tests/conversations_tests/export_inspector_test.py
  - docs/reference/cli/conversation.md
---

# Implement Codex conversation export inspector CLI

## Summary

Implement `lrh conversation inspect-export` so humans and machines can validate
private, non-authoritative Codex conversation export artifacts produced by the
manifest and file adapter work.

## Problem / Context

`WS-LRH-CODEX-CONVERSATION-EXPORTER` sequences inspection after the Codex export
manifest and file-based adapter. Those prerequisites are now resolved, so LRH
can validate real Markdown export artifacts rather than a hypothetical shape.
The governing proposal requires deterministic inspection before viewer support
so automation can check manifests, hashes, warnings, and stable JSON output
without treating raw transcripts as authoritative project state.

### Duplication search
- In-repo: Related but not duplicate. `src/lrh/conversations/export_manifest.py`
  defines the manifest contract, `src/lrh/conversations/codex_file_export.py`
  writes export artifacts, and `docs/reference/cli/conversation.md` says
  `inspect-export` is not yet implemented. No inspector command exists.
- Sibling repos: None identified.
- External libraries: None identified that provides LRH-specific Codex export
  manifest validation, privacy/authority reporting, sensitivity warning
  handling, source-hash verification, and stable text/JSON output.
- Recommendation: Proceed by extending `src/lrh/conversations/` and the
  existing `lrh conversation` CLI family.

### Demand search
- Work items: `WI-CODEX-CONVERSATION-EXPORT-MANIFEST` and
  `WI-CODEX-CONVERSATION-EXPORT-ADAPTER` are resolved and intentionally
  deferred `inspect-export`.
- Proposals: `PROP-LRH-CODEX-CONVERSATION-EXPORTER` explicitly lists
  `lrh conversation inspect-export <path> --format text|json` as
  implementation step 4 and a workstream exit criterion.
- Backlog: No exact backlog entry found beyond the broader Codex
  transcript/export gaps already linked to the workstream.
- Recommendation: Link this item to `WS-LRH-CODEX-CONVERSATION-EXPORTER`;
  leave viewer support and promotion workflows for later work items.

## Scope

- Implement a local inspector for Markdown Codex export artifacts with manifest
  frontmatter.
- Validate the manifest shape using the existing `ConversationExportManifest`
  contract.
- Report privacy, authority, sensitivity, warnings, transcript statistics, and
  adapter/source metadata.
- Verify source SHA-256 when the caller supplies an explicit source path.
- Provide deterministic `text` and `json` output modes suitable for human
  review and automation.
- Keep default inspection output metadata-only: report counts, hashes, privacy
  flags, and warnings without echoing raw transcript body, snippets, or message
  text to terminal output or CI logs.

## Required Changes

1. Add `src/lrh/conversations/export_inspector.py` with a reusable inspector
   API for reading a Markdown export artifact, parsing frontmatter, validating
   it as `ConversationExportManifest`, and returning structured inspection
   results.
2. Add `lrh conversation inspect-export EXPORT.md --format text|json` to
   `src/lrh/cli/main.py`.
3. Support an optional explicit source path for hash verification, such as
   `--source SOURCE`, while keeping inspection useful when the source is
   unavailable.
4. Recompute the Markdown artifact body statistics and compare them against the
   manifest's recorded transcript byte, character, and line counts so tampered
   bodies or stale manifests are surfaced as inspection findings.
5. Define clear exit/status behavior for invalid export artifacts, body
   statistic mismatches, hash
   mismatches, missing source paths, unreadable source paths, and successful
   inspections so CLI consumers can distinguish validation failures from tool
   failures.
6. Reuse existing manifest/frontmatter helpers where practical instead of
   inventing a second manifest schema.
7. Add focused tests in `tests/conversations_tests/export_inspector_test.py`
   for valid exports, malformed or missing frontmatter, invalid manifest
   fields, body-statistic drift, hash matches and mismatches, missing or
   unreadable source handling, sensitivity warning propagation,
   transcript-content non-disclosure in text and JSON output, CLI command
   wiring, `--format` choices, invalid export exit behavior, and stable
   text/JSON output.
8. Update `docs/reference/cli/conversation.md` and, if appropriate,
   `src/lrh/conversations/README.md` to document supported inspection behavior
   and privacy/authority boundaries.

## Non-Goals

- Do not implement `lrh serve` archive viewing or any conversation UI.
- Do not promote transcript content into project-control artifacts.
- Do not change execution-record `session_transcript` pointer grammar.
- Do not read undocumented Codex app storage internals.
- Do not implement native Codex API/app capture.
- Do not commit raw transcript exports or fixtures containing private session
  content.
- Use only synthetic fixture content for inspector tests.
- Do not certify redaction or public-export safety.
- Do not print raw transcript body, snippets, or message text in default text or
  JSON inspection output.

## Acceptance Criteria

- `lrh conversation inspect-export <path> --format text|json` exists and
  validates Codex export Markdown artifacts with `ConversationExportManifest`
  frontmatter.
- The inspector reports manifest validity, privacy/authority metadata,
  sensitivity status and warnings, transcript statistics, and source-hash
  verification status when a source path is supplied.
- JSON output is deterministic and automation-friendly; text output is concise
  and human-readable.
- Focused tests cover valid exports, malformed or missing manifests, hash
  matches and mismatches, missing or unreadable source handling, sensitivity
  warning propagation, CLI command wiring, `--format` choices, invalid export
  exit behavior, and stable text/JSON output.
- Documentation describes the inspection workflow and keeps viewer support,
  promotion, and `session_transcript` grammar changes out of scope.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `PYTHONPATH=src python -m unittest tests.conversations_tests.export_inspector_test`
- `PYTHONPATH=src scripts/test`
- `PYTHONPATH=src python -m lrh.cli.main validate`

## Risk Notes

- The inspector should treat raw transcripts as private, non-authoritative
  context and must not imply that inspection promotes them into LRH project
  truth.
- Default output should be safe for terminal scrollback and CI logs by exposing
  metadata and diagnostics only, not transcript content.
- Hash verification should distinguish source unavailable, hash match, hash
  mismatch, and source read failure without pretending every export can be
  fully verified.
- Body-statistic verification should catch manifest/body drift even when no
  original source file is available for hash verification.
- JSON output should be stable enough for later automation and viewer work to
  consume.
- Avoid implementing viewer or promotion behavior in this slice; doing so would
  collapse future workstream steps.

## Dependencies / Order

This item depends on the resolved manifest and file adapter work. It should
land before any `lrh serve` viewer work so the viewer can consume an
already-validated artifact contract.

## Related Workstream and Designs

- Workstream:
  `project/workstreams/proposed/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- Governing proposal:
  `project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md`
- Broader conversation storage proposal:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Related session archive proposal:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
