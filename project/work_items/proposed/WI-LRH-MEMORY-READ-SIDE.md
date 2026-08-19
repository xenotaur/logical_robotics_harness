---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-MEMORY-READ-SIDE
title: Implement lrh memory read/search
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
  - project/design/proposals/proposed/lrh-memory-command/00_proposal.md
depends_on: []
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
  - implement_semantic_search
acceptance:
  - lrh memory read <name> prints a memory's full frontmatter and body
  - lrh memory search finds memories by substring match across frontmatter and body, filterable by --agent/--type
  - lrh memory search behavior matches lrh search's documented substring-only design, no semantic ranking
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

# Implement lrh memory read/search

## Summary

Implement `lrh memory read` and `lrh memory search` — the read-side
companions to `list`, letting an agent inspect a memory corpus without
knowing its on-disk layout or already knowing exactly what it's looking
for.

## Problem / Context

`lrh memory list` (delivered in `WI-LRH-MEMORY-WRITE-SIDE`) shows only the
index; an agent that already knows a memory's name still has to open the
file directly, and there is no way to find a relevant memory by content
at all. This item closes both gaps, per `PROP-LRH-MEMORY-COMMAND`
Decision 7.

### Duplication search
- In-repo: `lrh search` (`src/lrh/prompt_workflow_search.py`) already
  implements deterministic, case-folded substring search — for execution
  records only, with no memory coverage. `lrh memory search` follows this
  existing design rather than inventing new search semantics.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, reusing `lrh search`'s design.

### Demand search
- Backlog: Found — `project/design/backlog.md`'s "lrh memory command"
  entry names "a read path" explicitly.
- Proposals: Found — `PROP-LRH-MEMORY-COMMAND` (this item implements its
  Decision 7).
- Recommendation: Offer to close/link the backlog entry once all four
  workstream work items resolve (tracked at the `WS-LRH-MEMORY-COMMAND`
  level).

## Scope

- Implement `lrh memory read <name>`
- Implement `lrh memory search <query>` as deterministic substring
  matching, not semantic ranking

## Required Changes

1. Implement `read()` in `src/lrh/prompt_workflow_memory.py`: resolves the
   corpus path internally, prints a named memory's full frontmatter and
   body.
2. Implement `search()`: deterministic, case-folded substring search over
   frontmatter and body across a corpus, modeled directly on
   `search_execution_records`/`_searchable_segments`/`_comparable` in
   `src/lrh/prompt_workflow_search.py:46-58,238-261`; supports
   `--agent`/`--type`/`--case-sensitive`/`--format` filters per the
   governing proposal's API Sketch.
3. Register `read`/`search` under the `memory` CLI noun in
   `src/lrh/cli/main.py`/`src/lrh/memory_workflow.py`.

## Non-Goals

- Does not begin implementation before `PROP-LRH-MEMORY-COMMAND` reaches
  `status: adopted` — see the workstream's Purpose section for why
  adoption is an entry gate, not just an exit criterion.
- Does not implement semantic or relevance-ranked search — deterministic
  substring matching only, per Decision 7.
- Does not implement `write`/`list`/`validate`/`repair` — see
  `WI-LRH-MEMORY-WRITE-SIDE`.

## Acceptance Criteria

- `lrh memory read <name>` prints a memory's full frontmatter and body,
  given only its name.
- `lrh memory search <query>` finds memories by substring match across
  frontmatter and body, filterable by `--agent`/`--type`.
- `lrh memory search` does not silently return semantically-related-but-
  non-matching results — behavior matches `lrh search`'s documented
  substring-only design.
- `lrh validate` reports 0 errors after all files are written.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh memory search --help`

## Risk Notes

- Low risk overall — no new schema or write path is introduced. The main
  risk is scope creep toward semantic/embedding-based search, which
  Decision 7 explicitly rejects for this item.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`
- Design: `project/design/proposals/proposed/lrh-memory-command/00_proposal.md`
  (Decision 7)
