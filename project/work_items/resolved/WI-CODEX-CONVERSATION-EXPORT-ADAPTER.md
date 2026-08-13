---
resolution: Implemented file-based Codex conversation export adapter in PR #480 (merge commit a195f8415a3b4d43033c4495743a616cc10f7768).
blocked_reason: null
blocked: false
id: WI-CODEX-CONVERSATION-EXPORT-ADAPTER
title: Implement file-based Codex conversation export adapter
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
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_inspect_export_cli
  - implement_lrh_serve_viewer
  - modify_session_transcript_schema
  - depend_on_undocumented_codex_app_storage_internals
acceptance:
  - A file-based Codex conversation export adapter exists under `src/lrh/conversations/` and writes Markdown transcript artifacts with `ConversationExportManifest` frontmatter
  - The adapter accepts explicit local source and output paths, rejects source/output path collisions even when overwrite is enabled, and does not depend on undocumented Codex app storage internals
  - Output defaults remain private and non-authoritative and preserve source hash, export timestamp, adapter version, warning list, sensitivity metadata, and transcript statistics
  - Focused tests cover successful conversion, missing or existing file failures, same-file source/output rejection, hash/statistics behavior, sensitivity warning propagation, and stable frontmatter output
  - Documentation describes the file-based adapter workflow and keeps `inspect-export`, viewer support, and `session_transcript` grammar changes out of scope
  - `lrh validate` reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/codex_file_export.py
  - src/lrh/conversations/__init__.py
  - tests/conversations_tests/codex_file_export_test.py
  - docs/reference/cli/conversation.md
---

# Implement file-based Codex conversation export adapter

## Summary

Implement the first file-based Codex conversation export adapter that converts
an explicit local Codex transcript/source file into a private,
non-authoritative Markdown transcript artifact using the existing Codex export
manifest contract.

## Problem / Context

`WS-LRH-CODEX-CONVERSATION-EXPORTER` sequences Codex conversation export work
after the manifest contract and before inspection/viewer support.
`WI-CODEX-CONVERSATION-EXPORT-MANIFEST` is resolved, so later work can now
consume `ConversationExportManifest` instead of inventing a second metadata
shape. The governing proposal chooses a file-based adapter first so LRH can
preserve Codex session context without depending on undocumented Codex app
storage internals.

### Duplication search
- In-repo: Related but not duplicate. `src/lrh/conversations/export_manifest.py`
  defines the Codex manifest contract, `src/lrh/conversations/pdf_import.py`
  implements ChatGPT PDF conversion, and `docs/reference/cli/conversation.md`
  explicitly says the file-based Codex adapter is not yet implemented.
- Sibling repos: None identified.
- External libraries: None identified that provides LRH-specific Codex
  transcript export artifacts with LRH privacy, authority, sensitivity,
  provenance, and manifest semantics.
- Recommendation: Proceed by extending `src/lrh/conversations/` with a focused
  file-based Codex adapter.

### Demand search
- Work items: `WI-CODEX-CONVERSATION-EXPORT-MANIFEST` is resolved and
  intentionally deferred the adapter. No prior proposed
  `WI-CODEX-CONVERSATION-EXPORT-ADAPTER` existed before this item was created
  to fill that gap.
- Proposals: `PROP-LRH-CODEX-CONVERSATION-EXPORTER` asks for a file-based
  Codex export adapter as implementation step 2.
- Backlog: The Codex skill-adaptation backlog notes transcript/export and
  closeout-memory gaps that this adapter begins to address, but does not fully
  close by itself.
- Recommendation: Link this item to `WS-LRH-CODEX-CONVERSATION-EXPORTER`;
  leave inspector, viewer, and session-transcript pointer follow-up for later
  work items.

## Scope

- Implement a local file-based adapter for manually saved Codex
  transcript/source files.
- Write Markdown transcript artifacts with deterministic
  `ConversationExportManifest` frontmatter.
- Preserve private-by-default, non-authoritative metadata and local
  sensitivity-warning posture.
- Document the adapter workflow as implemented behavior, while keeping
  inspection and viewing as follow-up slices.

## Required Changes

1. Add `src/lrh/conversations/codex_file_export.py` with a small adapter API
   that accepts an explicit source path and output path, reads local text
   content, computes the source SHA-256 and transcript statistics, runs or
   records sensitivity-scan metadata, and writes Markdown with
   `ConversationExportManifest` frontmatter.
2. Reuse `ConversationExportManifest`, shared frontmatter rendering, and
   existing sensitivity helpers rather than defining a second manifest or
   scanner contract.
3. Add overwrite/preflight behavior consistent with local CLI helpers: fail
   when the source is missing or unreadable, fail when output exists unless an
   explicit force/overwrite option is provided, reject source/output paths that
   resolve to the same file even when overwrite is enabled, and keep all work
   local.
4. Export public adapter helper(s) through `src/lrh/conversations/__init__.py`
   if that matches the package convention.
5. Add focused tests in `tests/conversations_tests/codex_file_export_test.py`
   for successful Markdown output, source hash/statistics, sensitivity warning
   propagation, missing input, existing output handling, and stable frontmatter.
6. Update `docs/reference/cli/conversation.md` and, if appropriate,
   `src/lrh/conversations/README.md` to describe the adapter's supported
   input/output workflow and its privacy/authority boundaries.

## Non-Goals

- Do not implement `lrh conversation inspect-export`.
- Do not implement `lrh serve` archive viewing or any conversation UI.
- Do not change execution-record `session_transcript` pointer grammar.
- Do not read undocumented Codex app storage internals.
- Do not implement native Codex API/app capture.
- Do not commit raw Codex transcript exports to this repository.
- Do not certify redaction or public-export safety.

## Acceptance Criteria

- A file-based Codex conversation export adapter exists under
  `src/lrh/conversations/` and writes Markdown transcript artifacts with
  `ConversationExportManifest` frontmatter.
- The adapter accepts explicit local source and output paths, rejects
  source/output path collisions even when overwrite is enabled, and does not
  depend on undocumented Codex app storage internals.
- Output defaults remain private and non-authoritative and preserve source hash,
  export timestamp, adapter version, warning list, sensitivity metadata, and
  transcript statistics.
- Focused tests cover successful conversion, missing or existing file failures,
  same-file source/output rejection, hash/statistics behavior, sensitivity
  warning propagation, and stable frontmatter output.
- Documentation describes the file-based adapter workflow and keeps
  `inspect-export`, viewer support, and `session_transcript` grammar changes out
  of scope.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `PYTHONPATH=src python -m unittest tests.conversations_tests.codex_file_export_test`
- `PYTHONPATH=src scripts/test`
- `PYTHONPATH=src python -m lrh.cli.main validate`

## Risk Notes

- The adapter should not infer private Codex app storage paths or couple LRH to
  current Codex desktop internals.
- Input formats may evolve; keep the first adapter conservative and file-based
  so future JSON/native adapters can be added without changing the manifest
  contract.
- Sensitivity scanning remains heuristic and must not be described as redaction
  or publication safety.
- Avoid implementing inspection output in this slice; doing so would collapse
  the next planned work item into this PR.

## Dependencies / Order

This item depends on `WI-CODEX-CONVERSATION-EXPORT-MANIFEST`, which is
resolved. It should land before the `inspect-export` CLI work item so the
inspector validates real adapter output rather than a hypothetical artifact
shape.

## Related Workstream and Designs

- Workstream:
  `project/workstreams/proposed/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- Governing proposal:
  `project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md`
- Broader conversation storage proposal:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Related session archive proposal:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
