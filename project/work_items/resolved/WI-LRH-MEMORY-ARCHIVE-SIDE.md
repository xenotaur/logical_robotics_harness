---
resolution: "Implemented and merged in PR #583 (commit f37672d4)"
blocked_reason: null
blocked: false
id: WI-LRH-MEMORY-ARCHIVE-SIDE
title: Implement lrh memory sync
type: deliverable
status: resolved
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
  - implement_lrh_memory_write
  - modify_lrh_sessions_sync_behavior
acceptance:
  - lrh memory sync mirrors a test project's memory corpus into the archive root, matching content exactly
  - re-running lrh memory sync with no changes is a no-op, verified by content hash, not size/mtime
  - editing a memory file and re-running sync snapshots the prior version to history/ before overwriting, and never deletes a prior snapshot
  - a memory file shrinking (e.g. via consolidate-memory) is mirrored correctly, not blocked
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

# Implement lrh memory sync

## Summary

Implement `lrh memory sync`, mirroring a project's Claude Code memory
corpus into the same durable archive `lrh sessions sync` already
maintains for transcripts, using a snapshot-before-overwrite invariant
suited to edited — not append-only — files.

## Problem / Context

`lrh sessions sync` archives zero memory files today: after a full sync
of 187 transcripts, `find <archive-root> -name '*.md'` returns 0 results
and no `memory/` directory exists anywhere under the archive root. During
the rescue that discovered this gap, the only backup of 296 memory files
was a tarball written to `/private/tmp`, which macOS is free to reclaim.
This item closes that gap per `PROP-LRH-MEMORY-COMMAND` Decisions 5 and 6.

### Duplication search
- In-repo: No existing implementation. `mirror_transcript()` at
  `src/lrh/prompt_workflow_sessions.py:255-293` is the direct precedent to
  generalize, not reimplement from scratch.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, generalizing `mirror_transcript`.

### Demand search
- Backlog: Found — `project/design/backlog.md`'s "lrh memory command"
  entry, archival-gap addendum appended 2026-08-18.
- Proposals: Found — `PROP-LRH-MEMORY-COMMAND` (this item implements its
  Decisions 5 and 6).
- Recommendation: Offer to close/link the backlog entry once all four
  workstream work items resolve (tracked at the `WS-LRH-MEMORY-COMMAND`
  level).

## Scope

- Implement `lrh memory sync` as an independent subcommand (not an
  extension of `lrh sessions sync`, per Decision 5)
- Generalize `mirror_transcript` into a shared `mirror_file`/`mirror_tree`
  primitive implementing snapshot-before-overwrite (Decision 6)

## Required Changes

1. Generalize `mirror_transcript()` (`prompt_workflow_sessions.py:255-293`)
   into a shared `mirror_file`/`mirror_tree` primitive implementing
   snapshot-before-overwrite: compare by SHA-256 content hash (not
   size/mtime); on any change, copy the currently-archived file to
   `<archive_root>/history/<slug>/memory/<relpath>.<timestamp>.<shorthash>.md`
   before overwriting; never delete a history snapshot.
2. Implement `lrh memory sync` in `src/lrh/prompt_workflow_memory.py`/
   `src/lrh/memory_workflow.py`: mirrors `<slug>/memory/**/*.md`
   (including `MEMORY.md`) into `<archive_root>/raw/<slug>/memory/**`,
   reusing `resolve_archive_root()` and matching `sessions sync`'s
   `--claude-projects-root`/`--archive-root`/`--project-root`/`--dry-run`
   flag shape.
3. Register `sync` under the `memory` CLI noun in `src/lrh/cli/main.py`/
   `src/lrh/memory_workflow.py`.

## Non-Goals

- Does not begin implementation before `PROP-LRH-MEMORY-COMMAND` reaches
  `status: adopted` — see the workstream's Purpose section for why
  adoption is an entry gate, not just an exit criterion.
- Does not modify `lrh sessions sync`'s existing behavior, transcript
  mirroring, or never-shrink invariant.
- Does not implement retention or pruning of the `history/` subtree —
  unbounded growth is accepted for v1 at the current corpus scale (~461
  files), per the governing proposal's Open Questions.
- Does not resolve the archive-root storage-location question — deferred
  the same way the sibling `PROP-LRH-SESSION-ARCHIVE-SYNC` defers it.

## Acceptance Criteria

- `lrh memory sync` mirrors a test project's memory corpus into the
  archive root, matching content exactly.
- Re-running `lrh memory sync` with no changes is a no-op, verified by
  content hash, not size/mtime.
- Editing a memory file and re-running `sync` snapshots the prior version
  to `history/` before overwriting, and never deletes a prior snapshot.
- A memory file shrinking (e.g. via `consolidate-memory`) is mirrored
  correctly, not blocked.
- `lrh validate` reports 0 errors after all files are written.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh memory sync --dry-run`

## Risk Notes

- Reusing `mirror_transcript`'s never-shrink invariant instead of
  snapshot-before-overwrite would silently block legitimate
  `consolidate-memory` edits — verify the generalized primitive
  implements the new invariant, not the old one carried over unchanged.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`
- Design: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
  (Decisions 5, 6)
