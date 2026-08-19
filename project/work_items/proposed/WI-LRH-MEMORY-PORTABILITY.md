---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-MEMORY-PORTABILITY
title: Implement lrh memory export/import/transfer
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-MEMORY-COMMAND
related_design:
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
depends_on:
  - WI-LRH-MEMORY-WRITE-SIDE
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_automatic_transfer_on_bucket_creation
acceptance:
  - lrh memory export produces a bundle with correct exported_from_slug provenance
  - lrh memory import writes bundled memories through write's own validation, rejecting anything write itself would reject
  - lrh memory transfer moves memories between two corpora without requiring a manually-managed intermediate file
  - lrh validate reports 0 errors after all files are written
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_memory.py
  - src/lrh/memory_workflow.py
  - src/lrh/cli/main.py
---

# Implement lrh memory export/import/transfer

## Summary

Implement `lrh memory export`, `lrh memory import`, and `lrh memory
transfer` — the portability surface that moves curated memories between
corpora, directly addressing that fresh workstream and worktree
directories start with a wholly empty memory corpus by construction.

## Problem / Context

Confirmed empirically against live `~/.claude/projects/` state during the
governing proposal's own design session: every new workstream subdirectory
or git worktree gets a wholly separate, empty memory corpus (e.g. the
LCATS main checkout's bucket has 160 memory files, while every sibling
`LCATS/Workstreams/Claude/*` bucket has 0). This item delivers the
curated, file-based propagation mechanism `PROP-LRH-MEMORY-COMMAND`
Decision 8 selects over a symlink-based alternative — disqualified because
it collides with the 200-line `MEMORY.md` truncation ceiling and with
`authored_by`/`applies_to` scoping.

### Duplication search
- In-repo: No existing implementation. `harvest_export_metadata()`
  (`src/lrh/prompt_workflow_sessions.py:401`) and `sync_export()`
  (`:462`) — two separate, non-adjacent functions, not one contiguous
  range — are the direct precedent for export-as-escape-hatch from a
  path-keyed bucket (for transcripts); this item is the memory analogue.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Backlog: Found — `project/design/backlog.md`'s "lrh memory command"
  entry.
- Proposals: Found — `PROP-LRH-MEMORY-COMMAND` (this item implements its
  Decision 8).
- Recommendation: Offer to close/link the backlog entry once all four
  workstream work items resolve (tracked at the `WS-LRH-MEMORY-COMMAND`
  level).

## Scope

- Implement `lrh memory export`, `import`, `transfer`
- `import`/`transfer` must route through `write`'s validated path per
  record, not a separate write mechanism

## Required Changes

1. Implement `export()`: dumps memories selected by `--name`/`--agent`
   filter, plus `exported_from_slug` provenance, to a portable bundle file
   (`--output`). **Do not implement an unfiltered "all memories" fallback
   as default behavior** — whether `export`/`transfer` should require an
   explicit filter at all, given the 200-line `MEMORY.md` ceiling, is the
   first Open Question below and must be resolved before this behavior is
   encoded, not assumed by the implementor.
2. Implement `import()`: validates and writes each bundled memory through
   `write`'s own rules per record; supports `--name` filter, `--force`,
   `--dry-run`.
3. Implement `transfer()`: a thin `export`+`import` wrapper through a temp
   bundle, taking `--from`/`--to` path-or-slug arguments.
4. Register `export`/`import`/`transfer` under the `memory` CLI noun in
   `src/lrh/cli/main.py`/`src/lrh/memory_workflow.py`.

## Non-Goals

- Does not begin implementation before `PROP-LRH-MEMORY-COMMAND` reaches
  `status: adopted` — see the workstream's Purpose section for why
  adoption is an entry gate, not just an exit criterion. This item in
  particular also cannot start before its own two Open Questions below
  are resolved, independent of the workstream-level gate.
- Does not implement automatic transfer-on-bucket-creation (Decision 8's
  third option) — explicitly deferred to a later proposal or amendment.
- Does not define a default-selection policy for "what memory is relevant
  to a new workstream" beyond explicit `--name`/`--agent` filters or a
  full-corpus fallback.

## Acceptance Criteria

- `lrh memory export --output <file>` produces a bundle containing the
  filtered memories (`--name`/`--agent`) with correct provenance, per
  whatever no-filter behavior the Open Questions below resolve to.
- `lrh memory import --input <file>` writes bundled memories through
  `write`'s validation, rejecting anything `write` itself would reject.
- `lrh memory transfer --from <a> --to <b>` moves memories between two
  corpora without requiring a manually-managed intermediate file.
- `lrh validate` reports 0 errors after all files are written.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh memory transfer --help`

## Risk Notes

- Two Open Questions from the governing proposal are unresolved and
  should be settled before implementation starts, not guessed at: (1)
  whether `export`/`transfer` should require an explicit `--name`/
  `--agent` filter rather than defaulting to "all," given the 200-line
  `MEMORY.md` ceiling; (2) the export bundle format (JSONL vs.
  tar-plus-manifest). Implementing against a guessed answer risks rework.
- `import` must not become a second, less-validated write path — verify
  it genuinely calls `write`'s logic per record rather than duplicating
  validation.

## Open Questions

- Default-selection policy for `export`/`transfer` when no filter is
  given (carried from the governing proposal's own Open Questions).
- Export bundle format: JSONL vs. tar-plus-manifest (carried from the
  governing proposal's own Open Questions).

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`
- Design: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
  (Decision 8)
