---
id: WS-LRH-CODEX-CONVERSATION-EXPORTER
kind: planning_node
title: Codex Conversation Exporter
status: proposed
stage: assessed
origin: proposal
summary: >
  Coordinate implementation of private-by-default Codex conversation export
  artifacts, deterministic inspection tooling, and later human-readable viewing
  support so Codex sessions become first-class LRH provenance without making raw
  transcripts authoritative project state.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md
  - project/design/proposals/proposed/lrh-codex-conversation-exporter/README.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - docs/conversations/conversation-capture-options.md
  - docs/conversations/promote-conversation-to-project-artifact.md
  - docs/reference/cli/conversation.md
  - docs/reference/cli/serve.md
work_items:
  - WI-CODEX-CONVERSATION-EXPORT-MANIFEST
  - WI-CODEX-CONVERSATION-EXPORT-ADAPTER
exit_criteria:
  - Codex conversation export manifest and Markdown artifact contract are implemented with typed helpers and documented schema expectations
  - File-based Codex export adapter creates private, non-authoritative transcript artifacts without depending on undocumented Codex app storage internals
  - `lrh conversation inspect-export <path> --format text|json` validates manifest shape, source hashes when possible, sensitivity warnings, and stable JSON output
  - Tests cover valid exports, malformed exports, hash mismatch handling, sensitivity warning propagation, and JSON/text inspector behavior
  - User-facing conversation docs explain export, inspection, privacy, authority, and promotion boundaries
  - Viewer support is either implemented through safe-default `lrh serve` archive viewing or explicitly deferred with a follow-up work item
  - PROP-LRH-CODEX-CONVERSATION-EXPORTER is adopted, superseded, or updated to reflect the implemented state
---

## Purpose

This workstream coordinates implementation of
`PROP-LRH-CODEX-CONVERSATION-EXPORTER`, which makes Codex app sessions durable
and inspectable within the LRH ecosystem. It exists because Codex sessions can
contain important design reasoning, command context, and follow-up decisions,
but LRH currently has no first-class way to preserve that context as a private,
non-authoritative transcript artifact.

The workstream keeps the implementation bounded: define the artifact contract
and deterministic inspector first, then add richer viewing only after the
contract is stable.

## Scope

- Define a Markdown-plus-manifest export artifact for Codex conversations.
- Implement a file-based Codex export adapter that does not rely on private
  Codex app storage internals.
- Reuse LRH's existing local sensitivity-scanning posture while preserving its
  non-certification warning.
- Add `lrh conversation inspect-export <path> --format text|json` for
  deterministic human and machine checks.
- Update conversation and CLI documentation for export, inspection, privacy,
  authority, and promotion boundaries.
- Defer `lrh serve` archive viewing until after the export artifact contract
  and inspection CLI are stable, then capture it as follow-up work.
- Keep raw transcript exports private by default and non-authoritative unless a
  separate reviewed promotion step creates project-control artifacts.

## Prior Art Check

### Duplication search

- **In-repo:** Related conversation infrastructure exists, but no duplicate
  workstream or implementation was found. Relevant prior art includes
  `docs/reference/cli/conversation.md`,
  `docs/conversations/conversation-capture-options.md`,
  `docs/conversations/promote-conversation-to-project-artifact.md`,
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`,
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`,
  and `src/lrh/conversations/` helpers. The new proposal
  `PROP-LRH-CODEX-CONVERSATION-EXPORTER` defines the focused Codex export and
  inspection slice.
- **Sibling repos:** None identified as already implementing LRH-specific
  Codex transcript exports.
- **External libraries:** No well-known external library or service was
  identified that provides LRH-specific Codex export manifests, authority
  labeling, sensitivity triage, provenance links, and promotion boundaries.
- **Recommendation:** Proceed with a focused LRH workstream that extends the
  existing conversation/storage direction rather than duplicating it.

### Demand search

- **Work items:** No existing proposed work item was found for the Codex
  conversation exporter slice. `WI-SESSION-ARCHIVE-SYNC-CAPTURE` is related to
  Claude session archive sync but explicitly preserves the current
  `session_transcript` grammar and does not satisfy Codex export artifacts.
- **Proposals:** Found the governing proposal
  `PROP-LRH-CODEX-CONVERSATION-EXPORTER`, plus related broader proposals
  `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` and
  `PROP-LRH-SESSION-ARCHIVE-SYNC`.
- **Backlog:** Found the canonical Codex skill-adaptation backlog entry in
  `project/design/backlog.md`, including transcript/export and closeout-memory
  gaps encountered while dogfooding LRH skills in Codex.
- **Recommendation:** File this workstream as the implementation container for
  `PROP-LRH-CODEX-CONVERSATION-EXPORTER`; create focused work items next
  rather than closing or subsuming the broader conversation/archive proposals.

## Work Items

Initial linked work item:

- `WI-CODEX-CONVERSATION-EXPORT-MANIFEST` — define the manifest and artifact
  contract.

The remaining planning sequence should create small, reviewable work items
along these lines:

- **File-based Codex adapter** — accept a manually saved Codex transcript or
  structured source export and write the Markdown transcript plus manifest
  without depending on undocumented Codex app internals.

- **Inspection CLI** — implement
  `lrh conversation inspect-export <path> --format text|json`, including
  manifest validation, source-hash checks where possible, sensitivity warning
  reporting, and stable automation-friendly JSON output.

- **Tests and fixtures** — add focused unit tests and representative fixtures
  for valid exports, malformed manifests, hash mismatches, sensitivity warning
  propagation, and text/JSON output stability.

- **Documentation** — update `docs/reference/cli/conversation.md`,
  `docs/conversations/conversation-capture-options.md`, and related guidance to
  explain export, inspection, privacy, authority, and reviewed promotion.

- **Viewer follow-up** — after the artifact contract and inspector have landed,
  file a follow-up work item for safe-default `lrh serve` viewing of explicitly
  configured archive roots.

## Exit Criteria

- Codex conversation export manifest and Markdown artifact contract are
  implemented with typed helpers and documented schema expectations.
- File-based Codex export adapter creates private, non-authoritative transcript
  artifacts without depending on undocumented Codex app storage internals.
- `lrh conversation inspect-export <path> --format text|json` validates
  manifest shape, source hashes when possible, sensitivity warnings, and stable
  JSON output.
- Tests cover valid exports, malformed exports, hash mismatch handling,
  sensitivity warning propagation, and JSON/text inspector behavior.
- User-facing conversation docs explain export, inspection, privacy, authority,
  and promotion boundaries.
- Viewer support is explicitly deferred with a follow-up work item after the
  artifact contract and inspector are stable.
- `PROP-LRH-CODEX-CONVERSATION-EXPORTER` is adopted, superseded, or updated to
  reflect the implemented state.

## Non-Goals

- Does not make raw Codex transcripts authoritative LRH state.
- Does not commit private raw transcripts to this repository by default.
- Does not implement automatic promotion from conversation text to design
  proposals, work items, evidence, execution records, or status.
- Does not depend on undocumented Codex app storage internals as the only
  source.
- Does not change the execution-record `session_transcript` grammar in the
  first implementation slice.
- Does not build a full conversation ledger, chat UI, or search dashboard.
- Does not solve target-aware LRH skill installation for Codex; that remains
  under `WS-SKILLS-TARGET-AWARE-INSTALL`.

## Relationship to Design

- Governing proposal:
  `project/design/proposals/proposed/lrh-codex-conversation-exporter/00_proposal.md`
- Proposal-set README:
  `project/design/proposals/proposed/lrh-codex-conversation-exporter/README.md`
- Broader conversation storage direction:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Related session archive direction:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Conversation capture guidance:
  `docs/conversations/conversation-capture-options.md`
- Promotion boundary guidance:
  `docs/conversations/promote-conversation-to-project-artifact.md`
- Existing CLI family:
  `docs/reference/cli/conversation.md`
- Safe local viewer precedent:
  `docs/reference/cli/serve.md`
- Related skill-target workstream:
  `project/workstreams/proposed/WS-SKILLS-TARGET-AWARE-INSTALL.md`

## Open Questions

- What stable Codex session identifier should LRH eventually use for
  `session_transcript` pointers?
- Should the first file-based adapter accept Markdown only, JSON only, or both?
- Should the manifest be sidecar-only, frontmatter-only, or duplicated in both
  places?
- Where should private local Codex exports live by default once LRH has an
  archive-root convention?
- After the export contract and inspector are stable, what viewer scope is
  appropriate for the deferred safe-default `lrh serve` follow-up?
