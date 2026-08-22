---
id: WS-LRH-MEMORY-COMMAND
kind: planning_node
title: LRH Memory Command Implementation
status: resolved
stage: closed
origin: design_review
summary: >
  Implement the ten-command lrh memory surface specified in
  PROP-LRH-MEMORY-COMMAND, across four staged work items covering
  write-side validation, durable archival, read-side inspection, and
  cross-corpus portability.
related_design:
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
  - project/design/backlog.md
work_items:
  - WI-LRH-MEMORY-WRITE-SIDE
  - WI-LRH-MEMORY-ARCHIVE-SIDE
  - WI-LRH-MEMORY-READ-SIDE
  - WI-LRH-MEMORY-PORTABILITY
  - WI-LRH-MEMORY-TRANSFER-SAFETY
exit_criteria:
  - lrh memory write/list/validate implemented (with the metadata.authored_by/applies_to schema, the malformed/legacy validate distinction, the memory-file-before-index write ordering, and the lrh-closeout SKILL.md migration); WI-LRH-MEMORY-WRITE-SIDE resolved
  - lrh memory sync implemented with the snapshot-before-overwrite invariant; WI-LRH-MEMORY-ARCHIVE-SIDE resolved
  - lrh memory read/search implemented; WI-LRH-MEMORY-READ-SIDE resolved
  - lrh memory export/import/transfer implemented; WI-LRH-MEMORY-PORTABILITY resolved
  - project/design/backlog.md's "lrh memory command" entry closed or linked
  - PROP-LRH-MEMORY-COMMAND adopted, with implementation_status: implemented and implemented_by listing all four WIs
---

# LRH Memory Command Implementation

## Purpose

This workstream carries `PROP-LRH-MEMORY-COMMAND` (still `proposed`,
documentation-only) from design into a delivered `lrh memory` command
family. It groups the four independently-landable work items the
proposal's own Implementation Plan already stages by risk, so their
sequencing, dependencies, and shared helpers (an extracted atomic-write
module, `project_slug_for_path` reuse) are tracked as one coordinated
effort rather than four unrelated PRs.

**Prerequisite — gates entry, not just exit.** `PROP-LRH-MEMORY-COMMAND`
must reach `status: adopted` before any of these four work items proceeds
past planning into `/lrh-implement`. **Satisfied as of 2026-08-19** — the
proposal is now `adopted`. Adoption alone does not resolve every Open
Question the proposal lists, so it does not blanket-unblock all four work
items uniformly: `WI-LRH-MEMORY-PORTABILITY` remains independently gated
on its own two listed Open Questions (default-selection policy, bundle
format — see that work item's Non-Goals and Open Questions) regardless of
the workstream-level gate above. `WI-LRH-MEMORY-WRITE-SIDE`,
`ARCHIVE-SIDE`, and `READ-SIDE` are not blocked by any remaining Open
Question — see the proposal's own "Adoption note" in its Open Questions
section for the per-question blocking classification that grounds this.

## Scope

- Implement all ten `lrh memory` commands (`write`, `list`, `validate`,
  `repair`, `sync`, `read`, `search`, `export`, `import`, `transfer`) as
  specified in the proposal's Design Decisions and API Sketch.
- Extract the shared atomic-write helper and reuse `project_slug_for_path()`,
  per Decision 4.
- Migrate `src/lrh/skills/lrh-closeout/SKILL.md:403-406`'s direct
  memory-write instruction to call `lrh memory write`, per the write-side
  review finding on the proposal's own PR.
- Land associated work items through the standard LRH execution lifecycle
  (`/lrh-implement` → `/lrh-land`).

## Prior Art Check

Carried forward from the proposal's own check, re-verified at
workstream-creation time.

### Duplication search
- In-repo: No existing implementation, confirmed via `git grep -l
  "WS-LRH-MEMORY-COMMAND" -- '*.md'` (tracked files only, per `AGENTS.md`'s
  survey convention — a filesystem `find`/`grep -r` also walks
  `.claude/worktrees/` checkouts and untracked scratch files, inflating or
  misrepresenting results). At the time this check was run, before this
  file existed, the query returned nothing; no other workstream covers
  this scope.
- Recommendation: Proceed.

### Demand search
- Proposals: Found — `PROP-LRH-MEMORY-COMMAND` (this workstream implements
  it directly, not incidentally).
- Backlog: Found — `project/design/backlog.md`'s "lrh memory command" entry
  (the proposal already answers it; this workstream is what closes it).
- Recommendation: Offer to close/link the backlog entry once all four WIs
  resolve.

## Work Items

- **WI-LRH-MEMORY-WRITE-SIDE** — `lrh memory write`/`list`/`validate`, the
  `metadata.authored_by`/`applies_to` schema (with the malformed/legacy
  grandfathering split), the memory-file-before-`MEMORY.md` write ordering,
  the extracted atomic-write helper, the `lrh-closeout` migration, and
  `lrh memory repair` as a fast follow-up within this same item (per the
  proposal's Stage 1a framing).
- **WI-LRH-MEMORY-ARCHIVE-SIDE** — `lrh memory sync`, the
  snapshot-before-overwrite mirroring invariant, and the shared
  `mirror_file`/`mirror_tree` primitive.
- **WI-LRH-MEMORY-READ-SIDE** — `lrh memory read`/`search`, following
  `lrh search`'s deterministic-substring precedent.
- **WI-LRH-MEMORY-PORTABILITY** — `lrh memory export`/`import`/`transfer`,
  blocked on resolving the proposal's default-selection-policy and
  bundle-format Open Questions before implementation starts.

## Exit Criteria

See frontmatter `exit_criteria:` above.

## Non-Goals

- Does not implement automatic transfer-on-bucket-creation — the proposal
  explicitly defers this (Decision 8) to a later proposal or amendment.
- Does not retroactively migrate the 19 already-known non-conforming
  memory files — `repair` supplies the tool; running it against the
  existing corpus is a separate operational step, not a WI deliverable.
- Does not resolve the archive-root storage-location question — deferred
  the same way the sibling `PROP-LRH-SESSION-ARCHIVE-SYNC` defers it.

## Open Questions

Carried forward from the proposal, relevant to sequencing:

- MCP-tool delivery vs. CLI-only (affects whether
  WI-LRH-MEMORY-WRITE-SIDE's scope needs to widen).
- WI-LRH-MEMORY-PORTABILITY's two blocking Open Questions
  (default-selection policy, bundle format) should be resolved before that
  WI is drafted in detail — noting this rather than guessing an answer
  here.

## Relationship to Design

- Design proposal: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
- Backlog entry: `project/design/backlog.md`, "lrh memory command to make
  cross-agent memory writes well-formed by construction"
