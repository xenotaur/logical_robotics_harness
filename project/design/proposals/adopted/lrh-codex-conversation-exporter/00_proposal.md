---
id: PROP-LRH-CODEX-CONVERSATION-EXPORTER
type: design_proposal
title: LRH Codex Conversation Exporter and Inspectable Transcript Artifacts
status: adopted
created_on: 2026-08-02
updated_on: 2026-08-02
implementation_status: implemented
implemented_by:
  - WI-CODEX-CONVERSATION-EXPORT-MANIFEST
  - WI-CODEX-CONVERSATION-EXPORT-ADAPTER
  - WI-CODEX-CONVERSATION-INSPECT-EXPORT
  - WI-CODEX-CONVERSATION-ARCHIVE-VIEWER
supersedes: []
superseded_by: null
related_design:
  - docs/conversations/conversation-capture-options.md
  - docs/conversations/promote-conversation-to-project-artifact.md
  - docs/reference/cli/conversation.md
  - docs/reference/cli/serve.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
---

# LRH Codex Conversation Exporter and Inspectable Transcript Artifacts

## Summary

This proposal defines a focused Codex conversation export path for LRH:
private-by-default transcript artifacts with structured manifests,
deterministic inspection commands, and an optional later local viewer. The
design makes Codex sessions first-class LRH provenance without treating raw
conversation text as authoritative project state.

## Background / Motivation

LRH already supports review-first conversation capture guidance and a ChatGPT
PDF conversion path, but Codex app sessions do not currently have an LRH-native
durable export workflow. This leaves useful design reasoning, command context,
and follow-up decisions trapped in an interactive session unless a human
manually summarizes them.

The existing conversation guidance is clear that raw conversations are useful
context but not project truth. Raw transcripts should remain private by default,
be labeled as non-authoritative, and only influence `project/` artifacts after
explicit review and promotion.

The missing slice is therefore not a full conversation ledger, chat UI, or
automatic promotion system. The immediate need is a small, stable export
contract for Codex sessions that humans can read and machines can verify.

## Prior Art Check

### Duplication search

- In-repo: Related but not duplicate. `docs/reference/cli/conversation.md`
  defines local conversation conversion/inspection boundaries;
  `src/lrh/conversations/pdf_import.py` implements ChatGPT PDF to Markdown
  metadata; `src/lrh/conversations/sensitivity.py` provides local heuristic
  scanning; `lrh serve` provides a safe-default local read-only viewer.
  `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` defines the broader architecture.
  `PROP-LRH-SESSION-ARCHIVE-SYNC` defines a Claude-oriented archive/sync model
  and explicitly does not implement a conversation UI or viewer.
- Sibling repos: None identified in this session.
- External libraries: No external library identified that provides LRH-specific
  Codex session export, provenance, authority labeling, sensitivity triage, and
  promotion boundaries. General archive/viewer tools do not replace an LRH
  artifact contract.
- Recommendation: Proceed as a focused proposal that extends the existing
  conversation/storage direction rather than duplicating it.

### Demand search

- Work items: No specific open work item found for a Codex app exporter/viewer
  slice.
- Proposals: Found `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` and
  `PROP-LRH-SESSION-ARCHIVE-SYNC`; this proposal should link to both and define
  the Codex export/inspection slice beneath them.
- Backlog: No existing exact backlog entry found.
- Recommendation: Link this proposal to the existing conversation and
  session-archive proposals. Do not supersede them.

## Design Decisions

### Decision 1: Export artifact shape

Options considered:

- Markdown-only transcript.
- JSON-only structured export.
- Markdown transcript plus structured manifest.

Chosen: Markdown transcript plus structured manifest.

The Markdown file gives humans a direct review surface. The manifest gives
machines a stable contract for validation, indexing, and future viewer support.
The exporter should record at minimum: `kind`, `schema_version`, `source_tool`,
`source_adapter`, `privacy`, `authority`, `sensitivity`, `sensitivity_scan`,
`source_id` when available, source hash, export timestamp, adapter version,
warning list, and transcript statistics.

### Decision 2: Authority and privacy defaults

Options considered:

- Commit raw transcripts into `project/`.
- Store only summaries.
- Create private raw exports with explicit non-authoritative metadata.

Chosen: private raw exports with explicit `authority: non_authoritative_context`.

Raw Codex transcripts may contain speculation, secrets, stale assumptions,
private file paths, and unreviewed model output. They are durable context, not
LRH truth. Promotion into design proposals, work items, evidence, execution
records, or status remains a separate human-reviewed operation.

### Decision 3: Inspection before rich viewing

Options considered:

- Build a web viewer first.
- Build a CLI inspector/checker first.
- Rely on external Markdown viewers.

Chosen: implement `lrh conversation inspect-export` before any rich viewer.

The CLI inspector should support text and JSON output, validate metadata,
report sensitivity warnings, verify source hashes where possible, and make the
export usable by automation. A web viewer may be added later, but it should
consume the same artifact contract rather than becoming the verification
source.

### Decision 4: Optional local viewer

Options considered:

- No LRH viewer.
- Static HTML generated beside each export.
- `lrh serve` local read-only archive viewer.

Chosen: defer a `lrh serve` local read-only archive viewer until after the
export contract and CLI inspector are stable.

The viewer should be localhost-only by default, serve only explicitly configured
archive roots, escape transcript content as inert data, show privacy, authority,
sensitivity state, and warnings prominently, and avoid arbitrary filesystem
browsing or execution behavior.

### Decision 5: Codex adapter scope

Options considered:

- Depend immediately on private Codex app internals.
- Require manual copy/paste only.
- Start with file-based imports and leave API/native capture as an adapter
  extension.

Chosen: start with file-based imports.

The first implementation can accept a manually saved Codex transcript or
structured source export when available. If the Codex app later exposes a
stable export API, native capture can become another adapter without changing
the LRH transcript artifact schema.

## Non-Goals

- Does not make raw Codex transcripts authoritative LRH state.
- Does not commit private raw transcripts to this repository by default.
- Does not implement automatic promotion from conversation text to project
  artifacts.
- Does not certify redaction or public-export safety.
- Does not depend on undocumented Codex app storage internals as the only
  source.
- Does not build a full conversation ledger, chat UI, or search dashboard in
  the first slice.
- Does not change the execution-record `session_transcript` grammar in this
  proposal.

## Implementation Plan

1. Define `ConversationExportManifest` and related typed helpers under
   `src/lrh/conversations/`.
2. Implement a file-based Codex export adapter that writes Markdown plus
   manifest.
3. Reuse the existing local sensitivity scanner and clearly preserve its
   non-certification warning.
4. Add `lrh conversation inspect-export <path> --format text|json`.
5. Add unit tests for metadata validation, hash verification, sensitivity
   warnings, malformed exports, and JSON output stability.
6. Update `docs/reference/cli/conversation.md` and `docs/conversations/`.
7. Defer `lrh serve` archive viewing until the export schema and inspector have
   landed.

## Cross-References

- Existing conversation capture guidance:
  `docs/conversations/conversation-capture-options.md`
- Promotion boundary:
  `docs/conversations/promote-conversation-to-project-artifact.md`
- Existing CLI family: `docs/reference/cli/conversation.md`
- Safe local viewer precedent: `docs/reference/cli/serve.md`
- Broad storage architecture:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Session archive context:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`

## Open Questions

- What stable Codex session identifier should LRH use for `session_transcript`
  when the Codex app exposes one?
- Should the first exporter accept Markdown, JSON, or both as input?
- Should the manifest be sidecar-only, frontmatter-only, or both?
- Where should private local Codex exports live by default once LRH has an
  archive root convention?
