---
id: "PROP-LRH-CONVERSATIONS-EXPORT-MANIFEST-TAXONOMY"
type: design_proposal
title: "Conversation Export Manifest Taxonomy and Backlog Gate Resolution"
status: proposed
created_on: 2026-09-25
updated_on: 2026-09-25
implementation_status: not_started
parent: "PROP-LRH-CONVERSATIONS-STORAGE-INTEROP"
related_design:
  - "project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md"
  - "project/design/proposals/proposed/lrh-conversations-storage-interop/01_chatgpt_pdf_import.md"
  - "project/design/backlog.md"
  - "project/work_items/proposed/WI-SESSION-SYNC-JULES-INGESTION.md"
supersedes: []
superseded_by: null
---

# Conversation Export Manifest Taxonomy and Backlog Gate Resolution

## Summary

This design note resolves the long-open backlog gate on generalizing
`ConversationExportManifest` beyond Codex. It records a three-family
taxonomy for LRH's conversation-export/transcript metadata shapes, adopts
per-tool `kind` literals as the governing pattern for the shared-manifest
family, and defers enforcement tooling in favor of a discoverable,
concrete trigger for revisiting that decision later.

## Background / Motivation

`project/design/backlog.md`'s "Generalize conversation export manifests
beyond Codex before `/lrh-export`" entry (opened 2026-08-07, touched again
2026-09-09, never resolved) asked for a deliberate choice among three
`kind`-versioning strategies before more non-Codex adapters landed on
`export_manifest.ConversationExportManifest`. That choice was never made
explicitly. In the meantime, three independent adapters —
`codex_file_export.py`, `codex_app_server_export.py`, `antigravity_export.py`,
and `claude_export.py` — each converged on the same per-tool-`kind`-literal
pattern (`KIND`, `KIND_ANTIGRAVITY`, `KIND_CLAUDE` in `export_manifest.py`)
without the gate ever being formally closed. Two other adapters,
`codex_archive.py` (backing `archive-codex-thread` and
`import-codex-exports`) and `pdf_import.py` (backing `convert-pdf`), do not
use the shared manifest at all and were never reconciled against the gate
either — one deliberately (`01_chatgpt_pdf_import.md` predates the gate by
three months and records its own contract on purpose), one by omission
(`codex_archive.py`'s `attempt.json` format has no design record at all).

A sixth shape is now planned: `WI-SESSION-SYNC-JULES-INGESTION` (proposed,
unimplemented) plans Jules session-export ingestion, citing two existing
Codex precedents — `import-codex-exports` and `convert-codex-file` — without
noting that they diverge in manifest-conformance (the former unvalidated,
the latter manifest-backed). This is the concrete trigger for resolving the
taxonomy now, while the WI is still open and free to amend.

## Prior Art Check

### Duplication search
- In-repo: No existing design proposal, workstream, or work item resolves
  this taxonomy question directly. `01_chatgpt_pdf_import.md` documents one
  sibling contract but not the cross-adapter reconciliation.
- Sibling repos: None identified.
- External libraries: None applicable — an internal contract-consistency
  question, not one an external library solves.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-SESSION-SYNC-JULES-INGESTION` (proposed) is the concrete
  trigger that makes this decision time-sensitive; not itself a duplicate
  request.
- Proposals: `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` (`00_proposal.md`) is
  the stated parent for this class of design work; this note fulfills that
  role for the export-manifest question specifically.
- Backlog: Found — `project/design/backlog.md`, "Generalize conversation
  export manifests beyond Codex before `/lrh-export`" (opened 2026-08-07,
  touched 2026-09-09, unresolved). This note is written to close it.
- Recommendation: Close the backlog entry on adoption of this note, with a
  pointer back to it.

## Design Decisions

### Decision 1: Backlog gate — `kind` strategy for the shared manifest

Options considered (from the original backlog entry):
- Backward-compatible `kind` — add a new per-tool literal per adapter,
  validated via `SUPPORTED_KINDS`.
- Fully general `kind` (e.g. `lrh_conversation_export`) with `source_tool`
  carrying the distinction.
- Schema-versioned compatibility rules, with `kind` stable and
  `schema_version` as the real compatibility axis.

**Chosen: backward-compatible, per-tool `kind` literals.** Three
independent adapters (Codex, Antigravity, Claude) already converged on this
pattern without coordination — empirical validation stronger than a
speculative choice among the other two would provide. It also requires no
migration of existing on-disk artifacts, unlike the fully-general option,
and no versioning machinery for a compatibility problem (`schema_version`
drift) that has not yet actually occurred, unlike the schema-versioned
option. This closes `backlog.md`'s gate.

**Follow-up:** remove the dead `"lrh_conversation_export"` literal from
`SUPPORTED_KINDS` in `export_manifest.py` — a half-started generalization
stub with zero producers.

### Decision 2: Three-family taxonomy

Not every conversation-export-shaped artifact belongs in
`ConversationExportManifest`. The distinguishing axis is **purpose**, not
source (static file vs. live thread) — `codex_file_export.py` is
static-file-sourced and still belongs to the manifest family, which rules
out "is the source live" as the taxonomy key.

- **Family 1 — Session Export Manifest** (`export_manifest.
  ConversationExportManifest`, unchanged): a one-shot, review-ready,
  validated export of a single identifiable transcript. Members:
  `codex_file_export.py`, `codex_app_server_export.py`,
  `antigravity_export.py`, `claude_export.py`.
- **Family 2 — Archive Ingestion Record** (new; not yet a validated
  contract): bulk/private-archive bookkeeping for material landed into the
  durable session archive — dedup, attempt/retry provenance — not a single
  reviewable artifact. Members today: `codex_archive.py`. Candidate member:
  Jules ingestion, per its own stated design intent.
- **Family 3 — Static External Transcript Import** (already documented in
  `01_chatgpt_pdf_import.md`, unchanged): a one-shot conversion of a
  foreign, non-LRH-tool artifact into a private transcript. Member:
  `pdf_import.py`.

This note adds a short comment to `export_manifest.py` cross-linking
Family 3's rationale, so "why doesn't this adapter use the shared
contract" is answerable from the code itself, not only from a proposal
three directories away.

### Decision 3: Family 2's minimal contract shape

Proposed shape (not yet implemented — see Open Questions for timing):
`kind` (discriminated per source, e.g. `lrh_codex_export_attempt`, future
`lrh_jules_export_attempt`), `source_tool`, an attempt/dedup key,
`imported_at`, plus the same baseline `privacy`/`authority` fields Families
1 and 3 already carry independently. This closes `codex_archive.py`'s
current zero-validation gap on its `attempt.json` output.

### Decision 4: `WI-SESSION-SYNC-JULES-INGESTION` — narrow revision, not reversal

The WI's Non-Goal rejecting a shared `SessionBackend`/connection
abstraction across Claude, Codex, and Jules is sound (Interface
Segregation Principle: the three have genuinely different connection
models — live API, local session file, downloaded zip) and is **not**
revisited by this note. What is revised: the WI should state explicitly
that Jules's *output metadata* follows the Family 2 contract (Decision 3)
rather than leaving ambiguous which of its two cited precedents
(`import-codex-exports` vs. `convert-codex-file`) governs its shape.

### Decision 5: Enforcement — deferred, with a discoverable trigger

No lint/test tooling is built now. Only one more adapter (Jules) is
currently planned, and building conformance tooling for a two-instance
outlier pattern risks encoding the wrong abstraction before real
requirements are known. Instead: a short comment is added at the top of
`export_manifest.py` stating a concrete trigger — "if a fourth Family-1
adapter or a second Family-2 adapter ships without using the relevant
contract, escalate to a lint/conformance-test enforcement design" — placed
in the file itself rather than only in `backlog.md`, since a backlog-only
gate already failed to prevent two silent bypasses of the original rule.

## Non-Goals

- Does not reverse `WI-SESSION-SYNC-JULES-INGESTION`'s rejection of a
  shared `SessionBackend` connection/discovery abstraction — that
  reasoning stands.
- Does not migrate `pdf_import.py` onto the shared manifest — Family 3
  remains a deliberately distinct contract per `01_chatgpt_pdf_import.md`.
- Does not implement Family 2's contract in code as part of this note —
  design only (see Open Questions on timing).
- Does not build lint or test enforcement tooling — deferred per Decision 5.
- Does not change `ConversationExportManifest`'s existing shape or its
  three current `kind` literals — Decision 1 ratifies, not modifies, the
  status quo.

## Implementation Plan

Small-to-medium scope, no single novel architectural build:

1. Close `backlog.md:50-91`, referencing this note.
2. Remove the dead `"lrh_conversation_export"` `SUPPORTED_KINDS` literal
   (small work item or ad hoc change).
3. Add the Family 3 cross-link comment and the Decision 5 enforcement-
   trigger comment to `export_manifest.py` (small work item or ad hoc
   change).
4. Revise `WI-SESSION-SYNC-JULES-INGESTION`'s acceptance criteria per
   Decision 4 (direct edit to the existing, unimplemented WI).
5. Family 2 contract implementation — timing depends on the Open Question
   below; if built now, a standalone work item; if deferred, tracked as a
   follow-on once Jules's zip format is reverse-engineered.

## Open Questions

- **Build Family 2's contract now, or defer until Jules's zip format is
  reverse-engineered?** Building now gives Jules a real target from day
  one and fixes `codex_archive.py`'s existing validation gap immediately.
  Deferring avoids designing a two-member abstraction (one real member,
  one planned) before Jules's actual requirements are known, per "prefer
  duplication over the wrong abstraction." Left to the user to decide.

## Cross-References

- Parent proposal: `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Sibling design note (Family 3): `project/design/proposals/proposed/lrh-conversations-storage-interop/01_chatgpt_pdf_import.md`
- Backlog gate being closed: `project/design/backlog.md` ("Generalize conversation export manifests beyond Codex before `/lrh-export`")
- Work item to be revised: `project/work_items/proposed/WI-SESSION-SYNC-JULES-INGESTION.md`
- Contract module: `src/lrh/conversations/export_manifest.py`
