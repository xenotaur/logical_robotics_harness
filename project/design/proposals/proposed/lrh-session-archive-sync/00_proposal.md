---
id: PROP-LRH-SESSION-ARCHIVE-SYNC
type: design_proposal
title: LRH Session Archive and Sync — Durable Local Transcript Archive, Reconciler, and Session Index
status: proposed
created_on: 2026-07-23
updated_on: 2026-07-29
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md
  - project/memory/decision_log.md
  - project/executions/README.md
---

# LRH Session Archive and Sync — Durable Local Transcript Archive, Reconciler, and Session Index

## Summary

This proposal establishes a **durable local archive for agent session
transcripts** and the tooling that keeps it reconciled with the LRH control
plane. It defines an `lrh sessions` command family (`sync`, `discover`,
`link`, `report`), a private local archive store outside every repository, a
committed but non-authoritative `project/sessions/` index that records the
session → PR tree, and both-identifier capture at record creation and closeout.
The governing invariant is: **no agent session that changed this repository is
ever lost.**

## Background / Motivation

The repository now records *where* a session lives but has no mechanism that
keeps the session itself alive, and no durable record of the identity needed to
find it. The 2026-07-23 decision-log entry (`project/memory/decision_log.md`)
established that session transcripts are never committed and that the
repository stores only the pointer `session_transcript:
claude-app:<host-uuid-stem>`. That decision deliberately left the other half
open: "Users archive `/export` output and/or JSONL files to local disk."
Nothing verifies that this archiving happens, and — as the design work behind
this proposal discovered — the pointer alone is not enough to find the
transcript even when it survives.

The gap is measured and decaying. Distinct `claude-app:` stems in execution
records, versus how many resolve to an on-disk transcript file by name:

| Date | Distinct sessions | Resolve by name | Dangling |
|---|---|---|---|
| 2026-07-23 | 29 | 8 (28%) | 21 |
| 2026-07-29 | 36 | 5 (14%) | 31 |

The dangling pointers are not (yet) lost data — on 2026-07-23 all 21 were still
recoverable by brute-force searching every local JSONL for a matching
`"prNumber"`. They dangle because of a **missing identity mapping**: execution
records store the *host* session id, transcript files are named by the *child*
SDK id, and on resumed or forked sessions these differ. The resolution rate is
falling because Claude Code prunes `~/.claude/projects/` on an approximately
30-day retention window (independently observed on two workstations: no local
JSONL predates 30 days). Every day, more of the brute-force fallback
evaporates. Three May-era records are already permanently `pending`.

Three properties of the current workflow make this worse than it looks. First,
capture is manual: `/lrh-closeout` only *offers* `/export`, and the offer is
routinely declined because a single session commonly spans several PRs — one
observed session produced seven (PRs 393–399, 401). Second, the natural time to
export (session archival) is decoupled from the events that create
control-plane records (PR merges), so the two drift. Third, the transcript
store is volatile, so a skipped capture becomes permanent loss silently and
without an error anywhere.

Critically, **the identity mapping cannot be reconstructed from raw transcripts
after the fact.** A raw JSONL contains no structured host id (only a child
`sessionId` field; any `local_`-shaped string is an incidental artifact of a
human pasting a URL or an environment dump into the chat). The session-listing
tools return the host id but not the child id. The host↔child mapping exists in
exactly two places: (a) live inside a running session, as the
`CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID` environment
variables; and (b) the `metadata.json` inside a `/export` zip, which carries
`sessionId` (host), `cliSessionId` (child), `prNumber`, `prs[]`, `branch`,
`writtenBranches[]`, `cwd`, and `title` together. Any design that hopes to
resolve pointers must capture the mapping from one of these sources — mirroring
bytes is not enough.

This also needs to generalize backwards. LRH has passed through three eras of
agentic development — GitHub Agents driven by ChatGPT design sessions,
ChatGPT + Codex Cloud, and the current Claude.app era — with different capture
stories and different amounts of surviving evidence (Codex Cloud runs were
never exportable). A session index that could only describe Claude.app sessions
would misrepresent the project's history, so the addressing scheme must
accommodate all three, including honest records of what is already lost.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Related and adjacent:
  `src/lrh/conversations/` (ChatGPT PDF import plus the local sensitivity
  scanner — the earlier era's capture path), `lrh match` (precedent for
  artifact-to-record linkage tooling), and — most importantly —
  `lrh sessions discover` / `lrh sessions link`, which are **already specified
  and deferred** as Stage 3 of `PROP-LRH-EXECUTION-SESSIONS`
  (`WI-EXEC-SESSIONS-DISCOVERY`). That work item now exists as an open PR
  (#435, `lrh sessions discover`/`link` only); this proposal is a strict
  superset. The intended sequence is to land this umbrella proposal first, then
  reconcile #435 against the adopted design (its session history may carry
  nuances not visible in the PR diff).
- Sibling repos: None identified. Taurcode maintains an LRH-like control
  plane, but its execution schema is being phased out in favor of LRH as the
  canonical source; no session archiver is known to exist there or elsewhere.
- External libraries: None identified for adoption as a whole. Community
  Claude Code transcript viewers and exporters exist but none reconcile
  against a control plane or perform PR linkage; general-purpose sync and
  backup tools (rsync, restic, borg) cover raw copying only. Their semantics
  (idempotent mirroring, client-side encryption) are adopted internally
  rather than depended upon.
- Recommendation: **Proceed** — as the fulfilment and extension of
  `PROP-LRH-EXECUTION-SESSIONS` Stage 3, not a new parallel command surface.

### Demand search
- Work items: `WI-EXEC-SESSIONS-DISCOVERY` exists as open PR #435 (scoped to
  `discover`/`link`); this proposal defines the umbrella that expands its scope,
  and #435 is to be reconciled against the adopted design once this proposal
  lands, rather than folded in pre-emptively. `WI-EXEC-SESSIONS-DOCS` and
  `WI-EXEC-SESSIONS-SCHEMA` are adjacent and already **resolved** (they
  documented and added `lrh validate` support for the fields this design
  populates); this proposal neither reopens nor depends on them.
- Proposals: Found `PROP-LRH-EXECUTION-SESSIONS`
  (`implementation_status: partial`) — its deferred Stage 3 is a strict subset
  of this design. Found `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` — its
  "durable private conversation ledger" use case describes this archive at the
  architectural level and supplies the privacy, durability, retention, and
  authority vocabulary this proposal adopts.
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: **Offer to link** — amend `PROP-LRH-EXECUTION-SESSIONS`
  Stage 3 to record that it is fulfilled through this proposal, and record
  storage-class alignment with `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.
  Neither is superseded; both remain governing in their own scope.

## Design Decisions

### Decision 1: Capture — three sources, not one mirror

The identity mapping cannot be derived from raw transcripts (see Motivation),
so capture is designed around the three places the needed data actually exists,
in priority order:

- **Forward capture (primary):** at execution-record creation and at closeout,
  read `CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID` and record
  both — the host stem as the canonical `session_transcript` pointer (already
  the convention) and the child id as an alias. The alias needs a durable home
  the moment it is captured, and the execution-record schema deliberately does
  not change (the `session_transcript` sequence grammar is reserved for genuine
  multi-backend spans, not two ids of one backend). Its home is therefore the
  `project/sessions/` index: Stage 1 lands a **minimal** index — host stem →
  child id(s), title, PRs — alongside the capture, so no captured id is ever
  held only in the live environment. Stage 3 enriches that same index (report,
  era-generality, fork stitching) rather than introducing it. This closes the
  gap for every future record, needs no schema change, and works today.
- **Retroactive mapping:** `lrh sessions sync` harvests `/export` zip
  `metadata.json` — the only artifact that maps host↔child↔PR for pointers that
  already dangle.
- **Content durability:** `lrh sessions sync` mirrors raw
  `~/.claude/projects/**/*.jsonl` into the archive, child-keyed, to preserve
  the actual conversation bytes past the ~30-day retention window.
- **Recovery heuristic (last resort):** where no export and no forward capture
  exist, join the session listing (host + branch + PR) against JSONL metadata
  (child + branch + PR) on branch/PR. This is explicitly heuristic — ambiguous
  on forked or resumed lineages — and never overrides an authoritative source.

Options considered and rejected as the *sole* mechanism: manual `/export`
(empirically failing on coverage — decaying resolution table above); a
push-only session-end hook (best-effort; desktop sessions stay open for days,
so the triggering event is unreliable); and a raw-JSONL-only reconciler (the
original framing of this proposal — rejected because bytes are not identity).
The reconciler is retained for durability and export harvest, but forward
env-var capture is what makes the invariant hold.

This follows the standard data-integrity doctrine that recoverability must be
continuously verified rather than assumed (Google SRE, Ch. 26, "Data
Integrity: What You Read Is What You Wrote") and the defense-in-depth principle
behind the 3-2-1 backup rule: multiple independent capture paths, no single
point of loss.

### Decision 2: Archive store and its policy classes

Options considered: a private local directory (covered by the user's existing
backup regime); a parallel private hosted repository; an encrypted off-machine
backup target.

**Chosen: a private local directory** as the phase-1 store, with an encrypted
off-machine tier explicitly permitted later and not designed out. A plain
hosted repository of raw transcripts is **rejected**, consistent with the
2026-07-23 decision-log entry ("merely relocates the leak") and the sensitivity
scanner contract in `src/lrh/conversations/README.md`. This is reinforced by a
finding from the design work: an `/export` zip bundles not just the transcript
but a `logs/` directory (web logs, ssh logs) and local session state — it is
*more* sensitive than a bare JSONL. Therefore export harvest extracts only the
`metadata.json` identity fields into any index; it never copies transcript
bodies or logs into a committed or shareable artifact.

Archive objects carry the policy vocabulary from
`PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`: privacy `private`, durability
`durable`, retention `keep`, authority `non_authoritative_context`. The archive
layout separates the verbatim artifact from everything derived:

```text
<archive-root>/
  raw/<project-slug>/<child-uuid>.jsonl    # verbatim copy, atomically refreshed
  exports/<session-key>/metadata.json      # harvested identity map (no logs/bodies)
  sessions/<session-key>.json              # derived per-session metadata
  index.jsonl                              # derived roll-up across sessions
```

Transcript JSONLs are append-only and a session can remain active across
several syncs (the multi-PR case), so `sync` **re-mirrors** a session's raw
file while the session is still live — writing to a temp path and renaming, so
each archived copy is atomically complete and never truncated mid-write. The
copy is only treated as final once the session ends. What is immutable is the
archived *content once the session is complete*, not the file across a session's
life; a sync must never leave a shorter copy in place of a longer source. Raw
files are copied before metadata is derived, so a parser defect can never cost
data, and because every index is re-derivable from the archived inputs, the
app's version-dependent transcript schema is not a durability risk.

### Decision 3: In-repo session index

Options considered: (a) a committed generated index at `project/sessions/`;
(b) CLI query only; (c) enrich execution records only.

**Chosen: (a), a committed generated index**, explicitly marked
non-authoritative. Option (b) fails the stated goal: findability would exist
only on the machine holding the archive. Option (c) leaves the tree inverted —
it answers "which session produced this record" but not "which PRs did this
session produce," which is precisely the multi-PR case that motivates the work.

The index is era-general. Each row identifies a session by a scheme-qualified
key (`claude-app:<host-uuid-stem>`, `chatgpt:<pdf-key>`, `codex-cloud:<ref>`),
plus title, era/agent, the PRs it produced, its child-id alias(es), and its
archive status — including `lost`, so that Codex Cloud runs and pre-June
sessions are recorded honestly rather than omitted. The index carries no
transcript content, no absolute paths, and no environment data; it is
regenerated, never hand-edited, and is `non_authoritative_context` in the same
sense as the pointers it complements. Because one session can produce several
export zips, index generation dedups by session key, latest-wins.

### Decision 4: Session identity and the fork boundary

The dangling-pointer problem is a missing mapping, not missing data. The
canonical session key is the **host UUID stem** with `local_` stripped —
matching what execution records already store — and each archived session
record carries the set of **child transcript ids** as aliases.

The host id is **stable for the life of a conversation thread**; a resume
changes only the child id (the JSONL filename), not the host id. A **fork** is
different and must be designed for explicitly: when a session's working
directory is removed (e.g. a git worktree deleted after its PR merges), Claude
Code starts a **new thread with a new host id**, so one continuous stretch of
human work can legitimately span two host ids — and each is correct for the
records it produced. Threads are stitched in the index via `branch` /
`writtenBranches[]` / PR, which the export `metadata.json` and the session
listing both provide. (An earlier draft of this design mischaracterised this as
the host id "rotating on resume"; that was wrong — it is a fork, and
host-canonical identity is sound.)

PR-number matching is retained only as the last-resort recovery heuristic of
Decision 1, never as a primary mechanism.

### Decision 5: Command surface

**Chosen:** extend the reserved `lrh sessions` family rather than introduce a
new one — `sync` (reconcile archive: raw mirror + export-metadata harvest),
`discover` (list sessions for a project), `link` (write `session_transcript`
into an execution record), and `report`
(surface dangling pointers, unarchived repo-changing sessions, and records
still `pending`). `report` is what makes the invariant auditable: it turns "is
anything at risk?" into a command with an answer.

Parsing is defensive — unknown transcript/metadata fields are ignored and index
derivation failures are reported without aborting the raw copy. New Python
functionality carries unit tests per project convention.

### Decision 6: Scheduling

Options considered: closeout-triggered only; scheduled only; both.

**Chosen: both.** `/lrh-closeout` invokes `lrh sessions sync` (replacing the
current manual `/export` offer) so capture is tied to the moment a PR lands,
and a **weekly** scheduled run provides the guarantee that does not depend on
any workflow being followed. Weekly is comfortably inside the ~30-day retention
window, so the invariant holds even for sessions that never reach closeout —
exactly the class the manual workflow loses today. The scheduling mechanism
(launchd, cron, or equivalent) is an implementation detail of that stage.

## Non-Goals

- Does not commit session transcripts, in any form, to this repository — it
  implements the archiving half the 2026-07-23 decision-log entry left to the
  user, and does not revisit that decision.
- Does not copy `/export` logs or transcript bodies into any committed or
  shareable artifact — only `metadata.json` identity fields are harvested for
  the index.
- Does not implement redaction, sanitization, or any public-export pipeline.
  The sensitivity scanner remains reserved for a future promotion path; the
  archive is private and unredacted.
- Does not build the encrypted off-machine tier now — permitted, not designed
  out; phase 1 delivers a local store only.
- Does not change the execution-record schema or the `session_transcript`
  pointer format (both landed in PR #409). The child-id alias is persisted in
  the `project/sessions/` index (introduced minimally in Stage 1), not in a new
  record field.
- Does not supersede `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` or
  `PROP-LRH-EXECUTION-SESSIONS`; it fulfils the latter's deferred Stage 3 and
  stays consistent with the former's storage architecture.
- Does not make transcripts authoritative control state — archived sessions and
  the index are `non_authoritative_context`.
- Does not implement a conversation UI, viewer, MCP surface, or chat-to-run
  cockpit.
- Does not retroactively recover sessions with no surviving transcript or
  export. The three May-era `pending` records stay `pending`; the index records
  them as lost rather than inventing attribution.

## Implementation Plan

Multi-stage and multi-PR; individual work items are defined in the governing
workstream (to be created — see the offer accompanying this proposal). The
proposed delivery order puts the cheap, infrastructure-free forward fix first:

**Stage 1 — Both-identifier capture (the forward fix).** Extend
execution-record creation (`/lrh-implement`) and `/lrh-closeout` to capture
both `CLAUDE_CODE_HOST_SESSION_ID` and `CLAUDE_CODE_SESSION_ID`, recording the
host stem as the `session_transcript` pointer and persisting the child id as an
alias in a **minimal `project/sessions/` index** (host stem → child id(s),
title, PRs) introduced in this stage — so no captured id lives only in the
live environment. Retain the closeout confirm gate (a fork can present a
different host id; the browser URL wins on disagreement) and the existing
`agent` branching (PR #431). No schema change; closes the gap for all future
records; lands standalone and first.

**Stage 2 — Archive and reconciler.** Archive layout and configurable archive
root; `lrh sessions sync` (raw JSONL mirror + `/export` `metadata.json`
harvest, raw-first ordering, defensive parsing); `lrh sessions discover` and
`link`. Open PR #435 already implements `discover`/`link`; it is reconciled
against this design after this proposal lands (see Prior Art Check). Unit tests
over parsing, change detection, and idempotency.

**Stage 3 — Index enrichment and report.** Enrich the `project/sessions/`
index introduced in Stage 1 (era-general keys, fork stitching via branch/PR,
dedup latest-wins) from Stage 1 records and Stage 2 harvest;
`lrh sessions report` for dangling pointers, unarchived sessions, and `pending`
records; bootstrap the index and attempt one-time recovery of the current
dangling pointers from local exports and JSONLs.

**Stage 4 — Scheduling and hook accelerant.** The weekly scheduled
`lrh sessions sync` is **required** — it is the guarantee for sessions that
never reach closeout (Decision 6), so an implementation that omitted it would
violate the retention invariant. The `SessionEnd` hook is the only optional
piece: it reduces capture latency but adds no guarantee the weekly run does not
already provide.

A companion documentation change amends `PROP-LRH-EXECUTION-SESSIONS` Stage 3
to record that it is fulfilled through this proposal.

## Cross-References

- Prior proposal (fulfilled Stage 3):
  `project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md`
- Storage-class vocabulary and general architecture:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Standing decision on transcripts: `project/memory/decision_log.md`
  (2026-07-23 entry)
- Pointer format and the host/child id model:
  `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
  (`### session_transcript`)
- Closeout integration point: `src/lrh/skills/lrh-closeout/SKILL.md`
  (Step 3 session resolution; Step 8 report)
- Overlapping open work to reconcile post-adoption: PR #435
  (`WI-EXEC-SESSIONS-DISCOVERY`, `discover`/`link`)
- Sensitivity scanner contract: `src/lrh/conversations/README.md`
- Related workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`

## Open Questions

- **Archive root location.** Deferred to a design discussion. The candidate
  default is a user-level directory such as `~/Archives/lrh-sessions/`, but the
  choice interacts with the user's backup and file-sync arrangements (notably
  whether the archive sits inside or outside a synced folder, given past
  sync-conflict issues) and with the eventual encrypted off-machine tier. The
  design assumes only that the root is configurable.
- **Fork representation (resolved).** Each execution record's
  `session_transcript` stays single-id for its own thread; a fork-spanning
  stretch of work is stitched in the `project/sessions/` index via `branch` /
  `writtenBranches[]` / PR, not represented as a multi-valued
  `session_transcript` (Decision 4). A record is written from inside one
  thread and cannot itself observe a fork that happens in a later, separate
  thread — only the index, which sees both host ids and their shared
  `branch` / `writtenBranches[]` / PR, can express that relationship. This
  also keeps records immutable at write time: a fork discovered later never
  requires editing an already-landed record. The `session_transcript` sequence
  syntax is reserved for its original purpose — multiple distinct sessions
  contributing to one record — not for fork continuity. Stage 1's index schema
  should support stitching entries by shared branch/PR for this reason.
- Whether the `project/sessions/` index should be regenerated on every closeout
  or only when its content would change, to minimize repository churn. (Leaning
  toward the latter; not load-bearing.)
