---
id: WS-PER-FILE-BACKLOG
kind: planning_node
title: "Per-File Backlog Entries Implementation"
status: proposed
stage: assessed
origin: design_review
summary: >
  Carry PROP-LRH-PER-FILE-BACKLOG from proposal to a delivered per-file
  backlog format: frontmatter schema and validation, read-only lrh backlog
  views, migration of LRH's own backlogs, a gated write side, and per-repo
  migration work items for Taurworks, LCATS, and prosoc.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-per-file-backlog/00_proposal.md
  - project/design/backlog.md
  - project/design/proposals/adopted/lrh-skills-target-aware-install/backlog.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/backlog.md
  - src/lrh/skills/_shared/prior-art-check.md
work_items: []
exit_criteria:
  - "PROP-LRH-PER-FILE-BACKLOG adopted, with its Open Questions resolved or explicitly carried forward"
  - "lrh validate checks backlog entry frontmatter under project/backlog/ and lrh backlog list|search are implemented with tests"
  - "LRH's project/design/backlog.md and both proposal-local backlogs are migrated to project/backlog/, each legacy file replaced by a pointer stub, with lrh validate at 0 errors"
  - "No LRH skill or shared reference cites a project/design/backlog.md section by heading text, and the prior-art check's backlog step searches project/backlog/"
  - "The write side (lrh backlog add|close|organize with dedupe) is either implemented or recorded as deferred with its trigger condition"
  - "A migration work item is filed in each of Taurworks, LCATS, and prosoc"
---

# Per-File Backlog Entries Implementation

## Purpose

This workstream carries `PROP-LRH-PER-FILE-BACKLOG` (proposed in
[PR #868](https://github.com/xenotaur/logical_robotics_harness/pull/868))
from design into a delivered backlog format: one Markdown file per backlog
entry under `project/backlog/{open,closed}/`, with minimal frontmatter that
LRH validates and on-demand `lrh backlog` views. It groups the proposal's
four implementation stages so that their ordering — read side before
migration, migration before write side — and their cross-repository reach
are tracked as one coordinated effort rather than as unrelated work items.

## Scope

- Define the backlog entry frontmatter schema and add frontmatter-only
  checks to `lrh validate`.
- Implement read-only `lrh backlog list|search`.
- Migrate LRH's own backlogs and repoint the skill references that cite them.
- Implement the write side (`add`, `close`, `organize`) once an automated
  writer needs it.
- File (not execute) migration work items in Taurworks, LCATS, and prosoc.

## Prior Art Check

### Duplication search
- In-repo: No existing backlog workstream or work item found
  (`grep -rli "per-file backlog\|PER-FILE-BACKLOG\|lrh backlog"` over
  `project/workstreams/`, `project/work_items/`, `src/` returned nothing).
  Governing design: `PROP-LRH-PER-FILE-BACKLOG`. Closest structural
  precedent: `WS-LRH-MEMORY-COMMAND` (resolved), which staged
  `PROP-LRH-MEMORY-COMMAND` into write, archive, read, and portability work
  items.
- Sibling repos: prosoc `WI-CARD-AUDIT-BACKLOG-SYNC` (project-local
  table-append helper, in flight; not on prosoc `main` as of 2026-11-11).
- External libraries: Backlog.md (`MrLesk/Backlog.md`) — assessed in the
  proposal; its file layout is borrowed, the tool is not adopted.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: `PROP-LRH-PER-FILE-BACKLOG` — the governing proposal, not a
  competing one.
- Backlog: No matching LRH entry; prosoc `backlog.md` § "Tooling" requests
  automated appends.
- Recommendation: Link prosoc `WI-CARD-AUDIT-BACKLOG-SYNC` when it lands, so
  prosoc's migration work item can retarget it.

## Work Items

No work items have been created yet; `work_items:` is populated as each is
filed. The planned items, in delivery order, are:

1. **Schema, validation, and read-only views** — frontmatter schema; `lrh
   validate` checks (ID equals filename stem, status vocabulary,
   status/bucket agreement, `noted` date, `promoted_to` when promoted,
   `(kind, subject)` uniqueness among open entries); `lrh backlog list`
   (filters `--status`, `--kind`, `--priority`; text, table, and JSON
   output) and `lrh backlog search`.
2. **Migrate LRH** — convert the 46 entries in `project/design/backlog.md`
   and the two proposal-local backlogs; replace each legacy file with a
   pointer stub; repoint section-by-heading references (for example
   `src/lrh/skills/_shared/prior-art-check.md:6` and `:99`,
   `src/lrh/skills/_shared/chain-defaults.md:7`,
   `src/lrh/skills/_shared/lifecycle-chain.md:6`) and their installed skill
   copies. Depends on item 1.
3. **Write side** — `lrh backlog add` (ID and `(kind, subject)` dedupe),
   `close`, and `organize`. Gated: started only when a skill needs to write
   entries automatically (for example, audit-finding collation). Depends on
   item 1.
4. **Downstream migration work items** — one filed in each of Taurworks
   (2 entries), LCATS (about 35 entries plus a pointer entry for the
   Gettenberg register), and prosoc (about 43 table rows plus prose
   sections). Executed in those repositories, on their own schedules.
   Depends on item 2, so each repository migrates against a proven LRH
   migration.

## Exit Criteria

- `PROP-LRH-PER-FILE-BACKLOG` is adopted, with its Open Questions resolved or
  explicitly carried forward.
- `lrh validate` checks backlog entry frontmatter under `project/backlog/`,
  and `lrh backlog list|search` are implemented with tests.
- LRH's `project/design/backlog.md` and both proposal-local backlogs are
  migrated to `project/backlog/`, each legacy file is replaced by a pointer
  stub, and `lrh validate` reports 0 errors.
- No LRH skill or shared reference cites a `project/design/backlog.md`
  section by heading text, and the prior-art check's backlog step searches
  `project/backlog/`.
- The write side is either implemented or recorded as deferred with its
  trigger condition.
- A migration work item is filed in each of Taurworks, LCATS, and prosoc.

## Non-Goals

- Does not complete the Taurworks, LCATS, or prosoc migrations — this
  workstream closes once their work items are filed; each repository owns
  its own execution.
- Does not change work items, workstreams, or proposals, or how backlog
  entries are promoted to them.
- Does not build the write side speculatively — item 3 waits for an
  automated writer.
- Does not decide the proposal's Open Questions; those are settled at
  proposal review or adoption.

## Open Questions

- Should item 1 wait for the proposal's adoption, or can it start once the
  `project/backlog/` location question is settled in review?
- During migration, should the prior-art check search both the legacy file
  and `project/backlog/` until all four repositories have migrated?
- If no automated writer appears, is recording the write side as deferred
  enough to close this workstream (as the exit criteria currently allow)?

## Relationship to Design

- Design proposal: `project/design/proposals/proposed/lrh-per-file-backlog/00_proposal.md`
- Structural precedent: `project/workstreams/resolved/WS-LRH-MEMORY-COMMAND.md`
- Current backlog: `project/design/backlog.md`
