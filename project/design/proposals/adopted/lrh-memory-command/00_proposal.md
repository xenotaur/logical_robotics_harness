---
id: PROP-LRH-MEMORY-COMMAND
type: design_proposal
title: LRH Memory Command — Validated Cross-Agent Writes and Durable Archival for Claude Code Memory
status: adopted
created_on: 2026-08-18
updated_on: 2026-08-19
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

This proposal establishes an `lrh memory` command family that makes malformed writes to Claude Code's per-project memory corpus (`~/.claude/projects/<slug>/memory/*.md`) structurally impossible, and closes the separate gap that no durable archive covers memory at all. It defines a write-side surface (`lrh memory write`/`list`/`validate`) that validates frontmatter, writes the memory file and its `MEMORY.md` index entry as an ordered pair designed to fail toward a detectable, repairable state rather than a silent one (Decision 4), resolves the corpus path internally, and records `metadata.authored_by`; a read-side surface (`lrh memory read`/`search`) for inspecting a corpus without knowing its layout; a portability surface (`lrh memory export`/`import`/`transfer`) that moves curated memories between corpora — the concrete need being that every new workstream subdirectory or worktree starts with a wholly separate, empty memory corpus by construction, verified empirically below; and an archive-side surface (`lrh memory sync`) that mirrors the corpus into the same durable archive `lrh sessions sync` already maintains for transcripts, using a snapshot-before-overwrite invariant suited to edited (not append-only) files. The full ten-command surface — including `lrh memory repair`, a conservative, structural-only fix-up command for memories already on disk — is specified in this proposal; v1 implementation is staged by risk (see Implementation Plan), not all ten at once.

## Background / Motivation

Multiple agents — Claude and Codex confirmed, others plausible — write directly into Claude Code's memory files today, with no shared tooling and no validation. `experimental/rescue_claude_sessions/findings.md` audited all 461 memory files across 5 project buckets during an unrelated migration and found 19 lacking Claude's required frontmatter (`name`, `description`, `metadata.type`). Codex was caught writing one live, during an LCATS closeout, with no `MEMORY.md` entry — unreachable by recall despite the write succeeding. In a separate bucket, an index landed at the bucket root instead of `memory/MEMORY.md`, orphaning all three files there. The interleaving analysis in that document rules out a format migration: conforming and non-conforming files land on the same days across two weeks, meaning two writers with two conventions operated concurrently, not a one-time transition. Nothing was lost — the ineffective writes just accumulated silently, which is the actual danger: a memory that fails to register gives no error to either the writing agent or the human.

A second, independently discovered gap compounds the first. `experimental/rescue_claude_sessions/README.md` documents that `lrh sessions sync` mirrors `<project-slug>/*.jsonl` into a durable local archive under `~/.local/share/lrh/session-archive`, with a never-shrink invariant protecting against silent data loss. Memory gets none of this: after a full sync of 187 transcripts, `find <archive-root> -name '*.md'` returned zero results and no `memory/` directory existed anywhere under the archive root. During the rescue this session was built from, the only backup of 296 memory files was a tarball written to `/private/tmp`, which macOS is free to reclaim — caught only because the migration happened to need a snapshot step, not because anything alerted on the gap. `project/design/backlog.md`'s entry for this proposal's topic calls the archival gap "arguably the larger half of the problem": the write-side fix stops new malformed memories, but nothing today makes memory *survivable* at all, malformed or not.

A third gap was confirmed empirically during this proposal's own design session, against the live `~/.claude/projects/` state on the machine that produced it. Every new workstream subdirectory or git worktree gets a wholly separate, empty memory corpus, because `project_slug_for_path()` keys off the *resolved absolute path* (`src/lrh/prompt_workflow_sessions.py:531`) — a subdirectory or worktree necessarily resolves to a different path than its parent checkout. The worktree this proposal was drafted in has no `memory/` directory at all, versus 139 files (`MEMORY.md` at 123 lines) in the main LRH checkout's bucket. The same pattern holds for the LCATS repository cited as a motivating example: the main `LCATS/LCATS` bucket has 160 memory files (`MEMORY.md` at 129 lines), while every sibling `LCATS/Workstreams/Claude/*` bucket checked (`SecretsLeak`, `SideWork`, `LocalModels`, `MemberImport`) has zero memory files, or no `memory/` directory at all. A session started in any of these fresh buckets is memory-blind to everything the main checkout has learned, with no mechanism today to bring any of it forward.

Both gaps share a root cause and a fix pattern already proven in this codebase. The root cause is that memory is **path-keyed agent state** — identical in kind to the transcript-archival problem `PROP-LRH-SESSION-ARCHIVE-SYNC` solved: state that lives outside the repository, addressed by a derived directory name, invisible to `git`, and silently absent rather than loudly broken when something goes wrong. That proposal's `lrh sessions` command family (`sync`/`discover`/`link`), its `project_slug_for_path()` path resolver, and its atomic-write + never-shrink mirroring are the direct precedent this proposal extends into a second corpus rather than re-derives.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. `grep -rl "lrh memory"` across `src/` returns nothing; the same search across proposals, workstreams, and work items returns only this proposal's own file once it exists, confirming no pre-existing artifact requested this capability by name (not "returns nothing" outright — this proposal necessarily matches its own search once committed). `grep -rli "memory"` across `src/lrh/*.py` turns up only unrelated uses (in-memory data structures, and LRH's own separate `project/memory/decisions/` decision log, which is a repo-tracked artifact distinct from Claude Code's per-slug agent memory corpus) — but a `.py`-only search misses non-Python callers: `src/lrh/skills/lrh-closeout/SKILL.md:403-406` explicitly directs agents to "write the resulting content using the auto-memory system... Update `MEMORY.md` with a pointer," a real, canonical LRH workflow that writes memory directly today and would keep bypassing this proposal's validation if not migrated (see Implementation Plan). The closest adjacent code is `experimental/rescue_claude_sessions/bucketlib.py`'s `slugify()`, explicitly scoped as migration/recovery tooling rather than a production command — its README's own promotion policy names only the read-only audit as a promotion candidate. The production equivalent already exists and is the one to reuse: `project_slug_for_path()` at `src/lrh/prompt_workflow_sessions.py:515`, already battle-tested against the `.claude/worktrees/...` slug edge case. Also adjacent: `lrh search` (dispatched at `src/lrh/cli/main.py:794-800`, implemented in `src/lrh/prompt_workflow_search.py`) already provides deterministic, case-folded substring search — explicitly not semantic ranking, per its own docstring at `prompt_workflow_search.py:46-58` — but scoped to execution records only, with no memory coverage. `lrh memory search` (Decision 7) follows this existing design rather than introducing new search semantics.
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

**Grandfathering — "required" applies to `write`, not retroactively to `validate`'s read of the existing corpus.** `authored_by` is a new field: every one of the roughly 440 memory files that already conform to the pre-existing schema (`name`, `description`, `metadata.type`) necessarily predates it and lacks it. Treating `authored_by` as universally required would make `lrh memory validate` flag nearly the entire corpus as non-conforming, conflating those files with the 19 genuinely broken ones the findings audit identified (missing `name`/`description`/`metadata.type` entirely — a different, worse defect). `validate` must therefore distinguish two tiers: **malformed** (missing the pre-existing required fields — unreachable by recall, the original defect) and **legacy** (conforming to the pre-existing schema, simply predating `authored_by` — reachable and correct, just unattributed). Only `write` enforces `authored_by` as a hard requirement, since it controls a write happening now; `validate` reports legacy files as their own category, not as malformed; and `repair` (Decision 9) is the tool that closes the legacy gap incrementally, file by file, without requiring the whole corpus to be touched in one migration.

### Decision 4: Path resolution and atomic-write reuse

Options considered:
- Reimplement slug resolution and atomic writes locally in the new memory module.
- Reuse `project_slug_for_path()` directly from `prompt_workflow_sessions.py`, and extract the currently-private `_atomic_write`/`_atomic_write_bytes` into a shared module as part of this work.

**Chosen: reuse and extract.** Reimplementing slug resolution risks reintroducing the exact bug class this proposal exists to prevent (an earlier revision of `project_slug_for_path` broke every `.claude/worktrees/` path by replacing the wrong character). The atomic-write functions are already file-local and this is the first real second consumer — the natural point to extract them rather than add a third copy-paste later. The direct import from a sessions-named module is a minor layering smell, noted as an Open Question below rather than solved here.

**Crash consistency across the two writes `write` performs.** The extracted per-file atomic-write helper (temp file + `os.replace`, `prompt_workflow_sessions.py:159-181`) makes each individual write atomic, but `write` performs two of them — the memory file and `MEMORY.md` — and no mechanism makes that *pair* atomic as a group. An interruption between the two renames leaves one of exactly the two defect states this proposal exists to prevent: an unindexed memory file (if interrupted after the first rename), or an index entry pointing at a file that was never written (if interrupted after the second). These two outcomes are not equally bad, so the ordering is a real decision, not an implementation detail: **`write` performs the memory-file rename first, then the `MEMORY.md` rename.** An interruption between them always fails toward the unindexed-file case — content-complete but unindexed — never toward a dangling index entry pointing at nothing. This matters because the unindexed case is not a new failure mode this proposal has to solve from scratch: it is exactly the "legacy"/unindexed category `validate` already detects (Decision 3's grandfathering clause) and `repair` (Decision 9) already exists to fix by adding the missing index line — the ordering choice means a crash mid-write degrades into a state the rest of this proposal already has tooling for, rather than a new, undetectable one. This is not true multi-file atomicity — a journaling or temp-marker mechanism would be needed for that, and is out of scope for v1 as unjustified complexity for a single-file, single-line-index write — but it is a bounded, understood, and self-healing failure mode rather than an unbounded one, which is what "atomic in the same operation" should have meant instead of implying stronger guarantees than the underlying primitive provides.

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

### Decision 7: Read-side surface — `read` and `search`

Options considered:
- Leave `list` (index-only) as the whole read-side surface, per the original draft of this proposal.
- Add `read` (show one memory's full frontmatter + body) and `search` (deterministic substring search across a corpus).

**Chosen: add both.** `list` alone still forces an agent to open a file directly once it knows a name, which is exactly the "know the layout" burden the backlog's read-path goal was meant to remove. `read` is low-risk — the same internal path resolution as every other command, no new mechanism. `search` deliberately does not reach for semantic or embedding-based ranking: `lrh search` already exists in this codebase for execution records and is explicitly deterministic, case-folded substring matching, not a relevance model (`prompt_workflow_search.py:46-58`, `:258-261`). Copying that design keeps `lrh memory search` consistent with the one search precedent this codebase has already chosen, and avoids scope-creeping this proposal into an embeddings project.

### Decision 8: Propagation mechanism — how a fresh, empty corpus gets memory

The third gap in Background/Motivation (fresh workstream/worktree buckets start memory-blind, confirmed empirically against live `~/.claude/projects/` state) is a distinct design question from write-side validation and archival: how does memory *move* from an existing corpus into a new one. Options considered:

- **Symlink the memory directory.** Point a fresh bucket's `memory/` at an existing bucket's `memory/` so they share one corpus.
  - Disqualified. This repo's own governing invariant, from the exact rescue effort that motivated this proposal, is "Symlinking the filesystem is not sufficient" for path-keyed agent state (`experimental/rescue_claude_sessions/README.md`) — and `project_slug_for_path()` calls `.resolve()` (`prompt_workflow_sessions.py:531`), which follows symlinks anyway, so it does not even cleanly solve bucket identity. More decisively: a symlink shares *everything, unconditionally, permanently* — defeating `authored_by`/`applies_to` scoping (Decision 3) — against a corpus that is already substantial relative to a hard, concrete constraint: Claude's own memory instructions state `MEMORY.md` is loaded into every session's context and truncated past 200 lines, and the two corpora measured in Background/Motivation are already at 123 and 129 lines. Unconditional sharing has no way to keep a workstream's index within that budget as it and its source both grow.
- **Curated file-based export/import/transfer.** `export` dumps selected (or, absent a filter, all) memories plus provenance (`exported_from_slug`) to a portable bundle file; `import` validates and writes each bundled memory through the same rules `write` uses; `transfer` is a thin `export`+`import` wrapper through a temp bundle.
  - This is not a new mechanism for this codebase: `lrh sessions sync --exports-dir` already externalizes Claude-Code-managed, path-keyed state (session transcripts) via an export/harvest pattern (`harvest_export_metadata()`, `sync_export()` at `prompt_workflow_sessions.py:401-462`) — export-as-escape-hatch from a bucket is established here, just not yet for memory. Curation is the direct answer to the 200-line ceiling: an operator chooses what's relevant to the new scope instead of blind full-copy. Because `import` reuses `write`'s validation per record, nothing enters a corpus through this path that a direct `write` call would reject. The cost is that it is an explicit step someone has to remember to run, and that duplicated memories can drift from their source with no automatic reconciliation — judged acceptable, and arguably correct: a workstream's understanding legitimately diverges from its parent's over time.
- **Automatic transfer on bucket creation.** A hook (Claude Code `SessionStart`, or an `lrh project init` step) that runs `transfer` the first time an empty-memory bucket is detected.
  - Not disqualified, but deferred. If it defaulted to "transfer everything," it would reintroduce the symlink option's context-budget problem without symlinking's simplicity — the worst of both. A safe version would need a default-selection policy (what counts as "relevant" to a brand-new workstream), which is a project-specific judgment call, not a mechanical one, and its trigger point is unresolved: a Claude Code `SessionStart` hook sits outside `lrh`'s own surface, while `lrh project init` only fires for repositories that go through that specific bootstrap path, not ad hoc workstream subdirectories like the ones that motivated this decision.
- **A shared, non-path-keyed memory store at the Claude Code level.** Not viable from LRH's position — would require a Claude Code product change outside this repo's control, and memory's path-keyed layout is itself undocumented and reverse-engineered (Prior Art Check: "no external library or service targets it").

**Chosen: curated file-based export/import/transfer**, with automatic invocation deferred as a follow-on question (see Open Questions) rather than committed in this proposal. It is the only option that is simultaneously precedented in this codebase, compatible with the 200-line context-budget constraint by construction, and layered on top of — rather than bypassing — the write-side validation Decisions 2 and 3 already establish.

### Decision 9: Retroactive fix-up — `repair`

Options considered:
- Leave retroactive cleanup of already-written, non-conforming memories entirely out of scope, as originally drafted — `validate` can detect but nothing in this proposal can act on what it finds.
- Add `lrh memory repair`, a conservative, structural-only fix-up command scoped to frontmatter and index fields, modeled directly on the "detect, then conservatively repair" split this codebase already uses three times over: `lrh work-items validate`/`lrh work-items organize` (whose own help text reads "Conservatively repair work-item frontmatter and status buckets, including legacy layouts" — `src/lrh/cli/main.py:293-296`), and the equivalent `organize` commands for workstreams and design proposals (`src/lrh/cli/main.py:383,413`).

**Chosen: add `repair`.** It closes the gap the original Non-Goals draft named directly — cleanup of the 19 already-known non-conforming files (`experimental/rescue_claude_sessions/findings.md`) had no tool to act on `validate`'s findings. Scoping it to structural fields only, never body content, follows the "conservatively" framing already established for `organize` rather than inventing a looser repair semantics. Implementation must route through `write`'s own validated path (read the existing file, apply the field patch, call `write`'s logic) rather than writing bytes directly — the same discipline already applied to `import` in Decision 8, so `repair` cannot become a second, less-validated way to produce a memory file.

This raises one question Decision 3 didn't need to answer, because nothing previously edited another agent's memory after the fact: does repairing a memory change who it's attributed to? **Resolved: `repair` preserves the original `authored_by` unless the caller explicitly overrides it.** Repairing a Codex-authored memory's frontmatter as Claude is a structural fix, not a re-authoring — the content and its original authorship claim are unchanged, only its conformance is. An explicit `--set metadata.authored_by=<new-agent>` remains possible for the rarer case where re-attribution is genuinely intended, but that is an opt-in override, never the default effect of running `repair`.

## Non-Goals

- Does not implement semantic or relevance-ranked search — `lrh memory search` is deterministic substring matching, following `lrh search`'s existing design (Decision 7), not an embeddings-based recall model.
- Does not modify `lrh sessions sync`'s existing behavior — transcript mirroring, its never-shrink invariant, and its archive-root resolution are unchanged by this proposal (Decision 5).
- Does not itself perform the retroactive cleanup of the 19 already-known non-conforming memory files found in the findings audit — `lrh memory validate` detects them and `lrh memory repair` (Decision 9) supplies the tool to fix them, but running that cleanup across the existing corpus is a separate operational step, not something this proposal or its work items execute.
- Does not resolve the archive-root's ultimate storage location or backup/sync-arrangement question — deferred the same way `PROP-LRH-SESSION-ARCHIVE-SYNC` defers it, for the same reason (interacts with the user's own backup and file-sync setup).
- Does not cover any Codex-native or other agent-native memory mechanism outside Claude Code's `~/.claude/projects/<slug>/memory/` layout — scoped strictly to the corpus the findings evidence actually covers.
- Does not add enforcement that prevents an agent from bypassing this command and writing memory files directly — v1 makes correct writes easy and structurally sound when the command is used; it does not (yet) make direct writes impossible (see Open Questions).
- Does not automatically transfer memory into a newly created workstream/worktree bucket — `transfer` is an explicit, operator-initiated action in this proposal; automatic invocation on bucket creation is deferred (Decision 8, Open Questions).
- Does not define a default-selection policy for "what memory is relevant to a new workstream" — `export`/`transfer` operate on an explicit `--name`/`--agent` filter or, absent one, the full corpus; a smarter default is out of scope here (see Open Questions).

## Open Questions

This proposal is deliberately held at `proposed` with implementation on hold specifically to leave room to widen scope before work items are drafted. Known open questions:

- **CLI-only or also an MCP tool?** The findings show Codex writing memory files directly rather than through any shared tool. If Codex (or other agents) don't reliably shell out to `lrh`, a CLI-only surface may not actually get adopted by the agent that caused the original incident. Should this ship as an MCP-exposed tool as well, so an agent calls it as a tool rather than a subprocess? This changes the delivery mechanism, not just the implementation, so it's worth resolving before work items are scoped.
- **Voluntary convention or enforced?** V1 makes correct writes *easy*; it doesn't make incorrect direct writes *impossible*, since nothing stops an agent from still hand-writing a `.md` file. Is a lint/audit-on-sync check (surfacing non-conforming files at `lrh memory sync` time, using the same detector `validate` implements) sufficient, or does this need something closer to enforcement?
- **`authored_by` provenance.** Should the caller always pass `--agent` explicitly, or can/should it be auto-detected from environment (analogous to how `session_transcript` capture already reads `CLAUDE_CODE_HOST_SESSION_ID`) to reduce the chance an agent forgets or misidentifies itself?
- **Archive retention/versioning mechanism.** Snapshot-before-overwrite (Decision 6) grows the history directory unboundedly, acceptable at today's corpus size (~461 files total) but not necessarily indefinitely. Is a loose timestamped-file history sufficient long-term, or should the memory archive subtree instead be a git repository (free diffability and dedup, at the cost of a git dependency for this one subtree)?
- **Layering of `project_slug_for_path`.** Decision 4 imports a sessions-named module's function from a memory-named module. Worth a small extraction to a shared `claude_code_paths`-style module, or is the cross-import acceptable as-is?
- **Scope beyond this repo's evidence.** The findings audit covered 5 project buckets on one machine. Is there a broader "validate any agent's writes to any path-keyed state" service this proposal is implicitly the first instance of, or is memory specifically the right and sufficient scope?
- **Automatic-transfer trigger point.** Decision 8 defers automating `transfer` on fresh-bucket creation. If pursued later, does it belong as a Claude Code `SessionStart` hook, an `lrh project init` step, or a new `lrh` bootstrap concept — none of which cleanly cover the ad hoc workstream-subdirectory case that motivated this decision?
- **Default-selection policy for transfer.** Should `export`/`transfer` require at least one filter (`--name`/`--agent`) rather than defaulting to "all," given the 200-line `MEMORY.md` ceiling and that the two corpora measured in Background/Motivation are already at 60%+ of it? An unfiltered `transfer --all` into a bucket that later accumulates its own memories risks the same truncation failure mode this proposal exists to prevent, just delayed.
- **Export bundle format.** Not decided — a single JSON/JSONL file (one memory record per line, including frontmatter, body, and `exported_from_slug` provenance) versus a tar of the raw `.md` files plus a manifest. JSONL is friendlier to diffing and partial reads; a tar preserves the on-disk file shape exactly. Left open for WI-D scoping.

## Implementation Plan

This proposal specifies the full ten-command surface, but v1 does not implement all ten at once — staged by risk and by dependency, pending resolution of the Open Questions above:

- **Stage 1 — WI-A (write-side):** `lrh memory write`/`list`/`validate`, the `authored_by`/`applies_to` schema addition (recorded as a short `project/memory/decisions/DEC-*` entry alongside this work, following the precedent of `WI-GATE-POLICY-CASCADE-STAGE3`'s comparable schema/policy decisions), extraction of the shared atomic-write helper, and migrating `src/lrh/skills/lrh-closeout/SKILL.md:403-406`'s direct-write instruction to call `lrh memory write` instead — otherwise this canonical LRH workflow keeps bypassing the new validation entirely, defeating the proposal's purpose for its most frequent real caller.
- **Stage 1a — fast follow-up on WI-A:** `lrh memory repair` (Decision 9), once `write`'s validated path exists for it to wrap. Named as a fast follow-up rather than folded into WI-A itself so the write-side work item stays scoped to what the original findings audit required; `repair` is the retroactive-cleanup complement to it, not a precondition.
- **Stage 1 — WI-B (archive-side):** `lrh memory sync`, built on the extracted atomic-write helper and a new shared `mirror_file`/`mirror_tree` primitive (generalizing `mirror_transcript`) implementing the snapshot-before-overwrite invariant from Decision 6.
- **Stage 2 — WI-C (read-side):** `lrh memory read`/`search`, following Decision 7. Depends only on the resolved corpus path already established by Stage 1 (or can land independently, since it introduces no new schema or write path) — low-risk, no open questions block it.
- **Stage 3 — WI-D (portability):** `lrh memory export`/`import`/`transfer`, following Decision 8. Depends on `write`'s validation path (Stage 1) for `import`'s per-record checks, and should not start implementation until the default-selection-policy and bundle-format Open Questions above are resolved.
- **Deferred, not yet a work item:** automatic transfer on bucket creation (Decision 8's third option) — explicitly left for a later proposal or amendment once its trigger-point Open Question is resolved.

Stage 1's two work items, once drafted, should offer to close/link `project/design/backlog.md`'s entry per the Prior Art Check demand-search verdict.

## API Sketch

Concrete CLI shape for all ten commands, derived from the Design Decisions above plus the flag conventions already established by `lrh sessions` (`src/lrh/sessions_workflow.py`) and `lrh search` (`src/lrh/prompt_workflow_search.py`). Flags marked "(precedent)" are lifted directly from an existing command rather than invented for this proposal; flags with no such marker are new, decided by the Design Decision cited.

### `lrh memory write`
```
lrh memory write <name>
    --description TEXT --type {user,feedback,project,reference}
    --agent TEXT [--applies-to TEXT[,TEXT...]]
    [--body-file PATH | stdin] [--project-root PATH] [--force]
```
`--type` is Claude's existing `metadata.type` vocabulary (the field missing on 19 files per `experimental/rescue_claude_sessions/findings.md:65-66`). `--agent`/`--applies-to` are Decision 3, verbatim. `--project-root` (precedent: `sessions_workflow.py:69,93,109`). `--force` encodes the "don't silently overwrite another agent's memory" requirement decided in Decision 3's contamination fix; exact enforcement (block vs. warn) is left to Stage 1 implementation.

### `lrh memory list`
```
lrh memory list [--project-root PATH] [--claude-projects-root PATH]
                 [--agent TEXT] [--format {text,json}]
```
`--agent` filter realizes the backlog's stated goal — `authored_by` "so memories can be filtered/scoped by agent" (`experimental/rescue_claude_sessions/findings.md:106-107`). `--format`/`--claude-projects-root` (precedent: `sessions_workflow.py:83-87,94-98`, the `sessions discover` command).

### `lrh memory validate`
```
lrh memory validate [--project-root PATH] [--claude-projects-root PATH]
                     [--format {text,json}]
```
Promotes the detector already prototyped in `experimental/rescue_claude_sessions/audit_buckets.py` — "missing `---` frontmatter with a `name:` field" (`findings.md:30`); `--format json` mirrors that prototype's existing `--json` flag (`audit_buckets.py:171`). Reports two distinct categories per the grandfathering clause in Decision 3: **malformed** (missing `name`/`description`/`metadata.type` — the original 19-file defect) and **legacy** (conforming but missing `authored_by` — not an error, a `repair` candidate).

### `lrh memory sync`
```
lrh memory sync [--claude-projects-root PATH] [--archive-root PATH]
                 [--project-root PATH] [--dry-run]
```
All four flags are precedent, one-for-one with `sessions sync` per Decision 5's explicit commitment to a shared mirror helper: `--claude-projects-root` (`sessions_workflow.py:48-51`), `--archive-root` with its override > env var (`LRH_SESSION_ARCHIVE_ROOT`, `prompt_workflow_sessions.py:210`) > default (`prompt_workflow_sessions.py:219`) precedence (`prompt_workflow_sessions.py:222-232`), `--project-root` (`sessions_workflow.py:69`), `--dry-run` (`sessions_workflow.py:70-74`). No `--exports-dir` equivalent — that is `sessions sync`'s transcript-specific `/export`-zip harvest with no memory analogue.

### `lrh memory read`
```
lrh memory read <name> [--project-root PATH] [--format {text,json}]
```
`list`'s companion — shows the file `list` points at (Decision 7).

### `lrh memory search`
```
lrh memory search <query> [--project-root PATH] [--agent TEXT]
                   [--type {user,feedback,project,reference}]
                   [--case-sensitive] [--format {text,json}]
```
Deterministic, case-folded substring search, copying `lrh search`'s existing design rather than inventing ranking (Decision 7; precedent: `prompt_workflow_search.py:46-58,258-261`).

### `lrh memory export`
```
lrh memory export --output PATH [--project-root PATH]
                   [--name TEXT[,TEXT...]] [--agent TEXT]
```
Dumps selected (or, absent a filter, all) memories plus `exported_from_slug` provenance to a portable bundle (Decision 8). Precedent for export-as-escape-hatch from a path-keyed bucket: `sync_export()`/`harvest_export_metadata()` at `prompt_workflow_sessions.py:401-462`. Bundle format is an Open Question.

### `lrh memory import`
```
lrh memory import --input PATH [--project-root PATH]
                   [--name TEXT[,TEXT...]] [--force] [--dry-run]
```
Validates and writes each bundled memory through `write`'s own rules, per record — not a separate, less-validated write path (Decision 8).

### `lrh memory transfer`
```
lrh memory transfer --from PATH_OR_SLUG --to PATH_OR_SLUG
                     [--name TEXT[,TEXT...]] [--agent TEXT] [--dry-run]
```
Thin `export`+`import` wrapper through a temp bundle (Decision 8); kept thin so `export`/`import` remain independently useful.

### `lrh memory repair`
```
lrh memory repair <name> --set FIELD=VALUE[,FIELD=VALUE...]
                   [--project-root PATH] [--dry-run]
```
Conservative, structural-only fix-up — frontmatter and index fields, never body content (Decision 9; precedent: `lrh work-items organize`'s "conservatively repair" framing, `main.py:293-296`). Preserves the original `metadata.authored_by` unless the caller explicitly includes it in `--set`. Implemented as a thin wrapper over `write`'s own validated path, not a separate write mechanism — same discipline as `import` (Decision 8).

## Cross-References

- Backlog entry: `project/design/backlog.md`, "`lrh memory` command to make cross-agent memory writes well-formed by construction"
- Evidence: `experimental/rescue_claude_sessions/findings.md`
- Ownership/runbook context: `experimental/rescue_claude_sessions/README.md`
- Sibling proposal (transcript archival precedent this extends): `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Existing production helper to reuse: `src/lrh/prompt_workflow_sessions.py:515` (`project_slug_for_path`)
- Existing archival precedent to extend: `src/lrh/prompt_workflow_sessions.py:255` (`mirror_transcript`, never-shrink invariant)
- Existing export precedent to extend: `src/lrh/prompt_workflow_sessions.py:401-462` (`harvest_export_metadata`, `sync_export`)
- Existing search precedent to follow: `src/lrh/prompt_workflow_search.py:46-58,258-261` (`lrh search`, deterministic substring matching)
