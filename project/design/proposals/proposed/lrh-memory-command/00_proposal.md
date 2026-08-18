---
id: PROP-LRH-MEMORY-COMMAND
type: design_proposal
title: LRH Memory Command — Validated Cross-Agent Writes and Durable Archival for Claude Code Memory
status: proposed
created_on: 2026-08-18
updated_on: 2026-08-18
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/backlog.md
  - experimental/rescue_claude_sessions/findings.md
  - experimental/rescue_claude_sessions/README.md
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
---

# LRH Memory Command — Validated Cross-Agent Writes and Durable Archival for Claude Code Memory

## Summary

This proposal establishes an `lrh memory` command family that makes malformed writes to Claude Code's per-project memory corpus (`~/.claude/projects/<slug>/memory/*.md`) structurally impossible, and closes the separate gap that no durable archive covers memory at all. It defines a write-side surface (`lrh memory write`/`list`/`validate`) that validates frontmatter, updates `MEMORY.md` atomically in the same operation, resolves the corpus path internally, and records `authored_by`; and an archive-side surface (`lrh memory sync`) that mirrors the corpus into the same durable archive `lrh sessions sync` already maintains for transcripts, using a snapshot-before-overwrite invariant suited to edited (not append-only) files.

## Background / Motivation

Multiple agents — Claude and Codex confirmed, others plausible — write directly into Claude Code's memory files today, with no shared tooling and no validation. `experimental/rescue_claude_sessions/findings.md` audited all 461 memory files across 5 project buckets during an unrelated migration and found 19 lacking Claude's required frontmatter (`name`, `description`, `metadata.type`). Codex was caught writing one live, during an LCATS closeout, with no `MEMORY.md` entry — unreachable by recall despite the write succeeding. In a separate bucket, an index landed at the bucket root instead of `memory/MEMORY.md`, orphaning all three files there. The interleaving analysis in that document rules out a format migration: conforming and non-conforming files land on the same days across two weeks, meaning two writers with two conventions operated concurrently, not a one-time transition. Nothing was lost — the ineffective writes just accumulated silently, which is the actual danger: a memory that fails to register gives no error to either the writing agent or the human.

A second, independently discovered gap compounds the first. `experimental/rescue_claude_sessions/README.md` documents that `lrh sessions sync` mirrors `<project-slug>/*.jsonl` into a durable local archive under `~/.local/share/lrh/session-archive`, with a never-shrink invariant protecting against silent data loss. Memory gets none of this: after a full sync of 187 transcripts, `find <archive-root> -name '*.md'` returned zero results and no `memory/` directory existed anywhere under the archive root. During the rescue this session was built from, the only backup of 296 memory files was a tarball written to `/private/tmp`, which macOS is free to reclaim — caught only because the migration happened to need a snapshot step, not because anything alerted on the gap. `project/design/backlog.md`'s entry for this proposal's topic calls the archival gap "arguably the larger half of the problem": the write-side fix stops new malformed memories, but nothing today makes memory *survivable* at all, malformed or not.

Both gaps share a root cause and a fix pattern already proven in this codebase. The root cause is that memory is **path-keyed agent state** — identical in kind to the transcript-archival problem `PROP-LRH-SESSION-ARCHIVE-SYNC` solved: state that lives outside the repository, addressed by a derived directory name, invisible to `git`, and silently absent rather than loudly broken when something goes wrong. That proposal's `lrh sessions` command family (`sync`/`discover`/`link`), its `project_slug_for_path()` path resolver, and its atomic-write + never-shrink mirroring are the direct precedent this proposal extends into a second corpus rather than re-derives.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. `grep -rl "lrh memory"` across `src/`, proposals, workstreams, and work items returns nothing; `grep -rli "memory"` across `src/lrh/*.py` turns up only unrelated uses (in-memory data structures, and LRH's own separate `project/memory/decisions/` decision log, which is a repo-tracked artifact distinct from Claude Code's per-slug agent memory corpus). The closest adjacent code is `experimental/rescue_claude_sessions/bucketlib.py`'s `slugify()`, explicitly scoped as migration/recovery tooling rather than a production command — its README's own promotion policy names only the read-only audit as a promotion candidate. The production equivalent already exists and is the one to reuse: `project_slug_for_path()` at `src/lrh/prompt_workflow_sessions.py:515`, already battle-tested against the `.claude/worktrees/...` slug edge case.
- Sibling repos: None identified — no sibling repository was named as a candidate host for this capability.
- External libraries: None identified. This targets Claude Code's undocumented, reverse-engineered on-disk memory layout; no external library or service targets it.
- Recommendation: **Proceed**, reusing `project_slug_for_path` and the `<noun>_workflow.py` CLI-wiring pattern (`sessions_workflow.py`, `prompt_workflow_sessions.py`) rather than introducing a new command-registration style.

### Demand search
- Work items: None found requesting this specifically.
- Proposals: None found requesting this specifically. (`project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md` is the closest sibling — it solves the isomorphic problem for transcripts and is the pattern this proposal extends — but it does not itself request memory coverage.)
- Backlog: Found — `project/design/backlog.md`, entry "`lrh memory` command to make cross-agent memory writes well-formed by construction," including the archival-gap addendum appended 2026-08-18. This proposal is the design response to that entry, not independent work.
- Recommendation: **Offer to close/link** the backlog entry once implementation work items exist (this proposal is documentation-only and does not itself close it).

## Design Decisions

### Decision 1: One command family or two independent pieces

Options considered:
- A single `lrh memory` change landing write-side and archive-side together, since they share a topic and a path-resolution helper.
- Two independently reviewable pieces under the same `lrh memory` noun: a write-side surface and an archive-side surface, sharing only `project_slug_for_path` and an extracted atomic-write helper.

**Chosen: two independent pieces.** They have materially different risk profiles — write-side changes agent-facing behavior (a bad validation rule could block a legitimate write), archive-side is purely additive backup with no read-path impact — and the backlog record itself notes the archival gap "is independent of the write-side idea and could land first." Splitting keeps each reviewable and revertible on its own schedule.

### Decision 2: Write-side command surface

Options considered:
- A single `lrh memory write` command only, leaving recall/audit to existing tools.
- `write` plus `list` (index dump) and `validate` (read-only conformance audit, promoting the detector logic already prototyped in `experimental/rescue_claude_sessions/audit_buckets.py`).

**Chosen: `write` + `list` + `validate`.** `write` alone satisfies the structural-soundness goal but leaves no cheap way to check corpus health or list current state without hand-reading `MEMORY.md`, which is exactly the file the findings show can be wrong. `validate` also gives future cleanup work (retroactively fixing the 19 known non-conforming files) a tool to check against, without this proposal itself performing that migration.

### Decision 3: Frontmatter schema — `authored_by` and `applies_to`

Options considered:
- Leave the schema as-is (`name`, `description`, `metadata.type`) and rely on file-naming convention (e.g. `feedback_codex_*`) for attribution, as currently happens informally.
- Add `metadata.authored_by` (required) and `metadata.applies_to` (optional list, default `[authored_by]`).

**Chosen: add both fields.** Naming convention is exactly what failed silently in the findings — attribution confidence for the Aug 3 Velumin files is "inference from naming... not proof." `authored_by` makes attribution a validated field, not a guess, and directly addresses the semantic-contamination defect: the LCATS file Codex wrote is Codex-specific sandbox guidance sitting where a Claude session would read it as guidance for itself. `applies_to` lets one agent deliberately write guidance for another without that ambiguity.

### Decision 4: Path resolution and atomic-write reuse

Options considered:
- Reimplement slug resolution and atomic writes locally in the new memory module.
- Reuse `project_slug_for_path()` directly from `prompt_workflow_sessions.py`, and extract the currently-private `_atomic_write`/`_atomic_write_bytes` into a shared module as part of this work.

**Chosen: reuse and extract.** Reimplementing slug resolution risks reintroducing the exact bug class this proposal exists to prevent (an earlier revision of `project_slug_for_path` broke every `.claude/worktrees/` path by replacing the wrong character). The atomic-write functions are already file-local and this is the first real second consumer — the natural point to extract them rather than add a third copy-paste later. The direct import from a sessions-named module is a minor layering smell, noted as an Open Question below rather than solved here.

### Decision 5: Archive-side — extend `lrh sessions sync` or add `lrh memory sync`

Options considered:
- Extend `lrh sessions sync` to also mirror `memory/` alongside `*.jsonl`, per the backlog's own candidate fix — one sync ritual, reuses existing glob/archive-root plumbing almost verbatim.
- Add a new, independent `lrh memory sync` subcommand under the new `lrh memory` noun, sharing a small extracted mirror helper with `sessions sync` but landing and reverting separately.

**Chosen: new `lrh memory sync` subcommand.** Extending `sessions sync` would couple this proposal's two independently-scoped pieces into shared CLI wiring, undermining Decision 1, and would leave the README's existing ownership table ("`lrh sessions` owns durable transcript archive") inaccurate without an edit. A separate command keeps discovery honest (an agent grepping for "memory" finds it under its own name) at the cost of a second sync command to remember — judged acceptable since both can be chained in the same runbook step where needed.

### Decision 6: Archive mirroring invariant — never-shrink vs. snapshot-before-overwrite

Options considered:
- Reuse `mirror_transcript`'s never-shrink invariant as-is: refuse to copy a source smaller than the already-archived copy, even with a newer mtime.
- Snapshot-before-overwrite: compare by content hash (not size/mtime), and on any change, copy the *currently archived* file to a timestamped history path before overwriting it with the new content — never deleting a snapshot.

**Chosen: snapshot-before-overwrite.** The never-shrink invariant's precondition is that the source is append-only, which holds for JSONL transcripts but not for memory: the installed `consolidate-memory` skill exists specifically to merge duplicates and prune stale entries, so legitimate shrinkage is routine, expected behavior, not a corruption signal. Applying never-shrink as-is would make consolidation indistinguishable from data loss and block it. Snapshot-before-overwrite preserves the same underlying goal — no version is ever unrecoverable — without penalizing legitimate edits, and reuses the codebase's existing atomic-write primitive rather than inventing a new mechanism.

## Non-Goals

- Does not implement a full search/recall API beyond `lrh memory list` — relevance-ranked or semantic query over the corpus is a possible future extension, not committed here (see Open Questions).
- Does not modify `lrh sessions sync`'s existing behavior — transcript mirroring, its never-shrink invariant, and its archive-root resolution are unchanged by this proposal (Decision 5).
- Does not retroactively migrate or fix the 19 already-known non-conforming memory files found in the findings audit — this proposal governs new writes going forward; `lrh memory validate` supplies the tool that retroactive cleanup work would use, but performing that cleanup is separate scope.
- Does not resolve the archive-root's ultimate storage location or backup/sync-arrangement question — deferred the same way `PROP-LRH-SESSION-ARCHIVE-SYNC` defers it, for the same reason (interacts with the user's own backup and file-sync setup).
- Does not cover any Codex-native or other agent-native memory mechanism outside Claude Code's `~/.claude/projects/<slug>/memory/` layout — scoped strictly to the corpus the findings evidence actually covers.
- Does not add enforcement that prevents an agent from bypassing this command and writing memory files directly — v1 makes correct writes easy and structurally sound when the command is used; it does not (yet) make direct writes impossible (see Open Questions).

## Open Questions

This proposal is deliberately held at `proposed` with implementation on hold specifically to leave room to widen scope before work items are drafted. Known open questions:

- **CLI-only or also an MCP tool?** The findings show Codex writing memory files directly rather than through any shared tool. If Codex (or other agents) don't reliably shell out to `lrh`, a CLI-only surface may not actually get adopted by the agent that caused the original incident. Should this ship as an MCP-exposed tool as well, so an agent calls it as a tool rather than a subprocess? This changes the delivery mechanism, not just the implementation, so it's worth resolving before work items are scoped.
- **Voluntary convention or enforced?** V1 makes correct writes *easy*; it doesn't make incorrect direct writes *impossible*, since nothing stops an agent from still hand-writing a `.md` file. Is a lint/audit-on-sync check (surfacing non-conforming files at `lrh memory sync` time, using the same detector `validate` implements) sufficient, or does this need something closer to enforcement?
- **`authored_by` provenance.** Should the caller always pass `--agent` explicitly, or can/should it be auto-detected from environment (analogous to how `session_transcript` capture already reads `CLAUDE_CODE_HOST_SESSION_ID`) to reduce the chance an agent forgets or misidentifies itself?
- **Archive retention/versioning mechanism.** Snapshot-before-overwrite (Decision 6) grows the history directory unboundedly, acceptable at today's corpus size (~461 files total) but not necessarily indefinitely. Is a loose timestamped-file history sufficient long-term, or should the memory archive subtree instead be a git repository (free diffability and dedup, at the cost of a git dependency for this one subtree)?
- **Layering of `project_slug_for_path`.** Decision 4 imports a sessions-named module's function from a memory-named module. Worth a small extraction to a shared `claude_code_paths`-style module, or is the cross-import acceptable as-is?
- **Scope beyond this repo's evidence.** The findings audit covered 5 project buckets on one machine. Is there a broader "validate any agent's writes to any path-keyed state" service this proposal is implicitly the first instance of, or is memory specifically the right and sufficient scope?

## Implementation Plan

Pending resolution of the Open Questions above, the current decomposition (subject to change) is two independent work items sharing the helpers from Decisions 4 and 6:

- **WI-A (write-side):** `lrh memory write`/`list`/`validate`, the `authored_by`/`applies_to` schema addition (recorded as a short `project/memory/decisions/DEC-*` entry alongside this work, following the precedent of `WI-GATE-POLICY-CASCADE-STAGE3`'s comparable schema/policy decisions), and extraction of the shared atomic-write helper.
- **WI-B (archive-side):** `lrh memory sync`, built on the extracted atomic-write helper and a new shared `mirror_file`/`mirror_tree` primitive (generalizing `mirror_transcript`) implementing the snapshot-before-overwrite invariant from Decision 6.

Both work items, once drafted, should offer to close/link `project/design/backlog.md`'s entry per the Prior Art Check demand-search verdict.

## Cross-References

- Backlog entry: `project/design/backlog.md`, "`lrh memory` command to make cross-agent memory writes well-formed by construction"
- Evidence: `experimental/rescue_claude_sessions/findings.md`
- Ownership/runbook context: `experimental/rescue_claude_sessions/README.md`
- Sibling proposal (transcript archival precedent this extends): `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Existing production helper to reuse: `src/lrh/prompt_workflow_sessions.py:515` (`project_slug_for_path`)
- Existing archival precedent to extend: `src/lrh/prompt_workflow_sessions.py:255` (`mirror_transcript`, never-shrink invariant)
