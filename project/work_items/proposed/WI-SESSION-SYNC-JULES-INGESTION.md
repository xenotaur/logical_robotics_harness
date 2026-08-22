---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-SYNC-JULES-INGESTION
title: Add Jules session-export ingestion to the lrh sessions archive
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
related_design:
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/contributor-identity-contract/00_proposal.md
depends_on:
  - WI-SESSION-ARCHIVE-ROOT-DEFAULT
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_shared_backend_abstraction
acceptance:
  - A new lrh conversation command ingests a Jules session-export zip (jules_session_<id>.zip) and writes its content under the canonical archive root's jules/ subdirectory, mirroring the existing CODEX_ARCHIVE_SUBDIR convention
  - The Jules zip's internal structure is reverse-engineered and documented (in code comments or a short README section) before any parsing logic is written, matching how Claude's and Codex's export formats were each documented before their own ingestion code was written
  - Ingestion writes per-attempt metadata (e.g. attempt.json) into the archive alongside imported content, mirroring Codex's import-codex-exports convention, rather than an entry in project/sessions/index.jsonl, whose SessionRecord schema is Claude-specific (host_id-keyed) and out of scope to change here
  - project/executions/README.md's session_transcript pointer-scheme table is extended to document both the new jules: form and the currently-undocumented but already-valid codex-app: form, for use when a Jules-authored session gets its own execution record
  - Re-ingesting the same zip is detected and skipped (or explicitly updated per a defined rule), never blindly re-copied
  - No shared SessionBackend/adapter interface is introduced; the Jules pipeline is implemented as its own separate command, mirroring the existing Codex pipeline's shape (per Option 4 of the governing design discussion)
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/
  - src/lrh/cli/main.py
  - project/executions/README.md
  - tests/assist_tests/
---

# Add Jules session-export ingestion to the lrh sessions archive

## Summary

Give Jules session-export zips (`jules_session_<id>.zip`) a real, governed
home in the `lrh sessions` archive, by adding a Jules-specific ingestion
command that mirrors Codex's existing separate-pipeline pattern rather than
building a new shared backend abstraction.

## Problem / Context

Jules sessions have no footprint anywhere in this codebase today: a
repo-wide grep for `jules` in `src/lrh/` and `experimental/` returns zero
hits for session/transcript handling — Jules is referenced only as a
PR-review-bot identity (`google-labs-jules`, in
`project/design/proposals/proposed/contributor-identity-contract/00_proposal.md`
and `/lrh-pr-triage`), never as a session source. In practice, Jules export
zips are downloaded manually and moved by hand into a staging folder
alongside Claude's `session-export-*.zip` files, with no archival or index
entry at all.

The chosen approach follows the pattern this codebase already used
successfully for Codex: `src/lrh/conversations/codex_archive.py` implements
a wholly separate discovery/export pipeline for Codex, sharing only
`resolve_archive_root()` with Claude's `lrh sessions sync`
(`resolve_codex_archive_root()` at `codex_archive.py:64-72` calls the shared
resolver and appends `CODEX_ARCHIVE_SUBDIR`). This item does the same for
Jules rather than generalizing a shared interface — per the governing design
discussion's Option 4, a shared `SessionBackend` abstraction was considered
and explicitly rejected as premature given how structurally different the
three backends are (Claude: live local JSONL keyed by resolved-path slug;
Codex: remote thread/task ids via app-server export; Jules: manually
downloaded zip exports with no local live presence at all).

The identity/pointer layer this new ingestion writes into is already
backend-agnostic: `agent:` is an open string and `session_transcript:` is a
scheme-prefixed `<backend>:<id>` pointer
(`project/executions/README.md:50,57-69`), generalized on purpose per the
2026-07-23 "Backend-Agnostic Session Pointer Grammar" decision
(`project/memory/decision_log.md:127-157`). This item adds the missing
`jules:` row to that documented table — and, since it's already being
touched, the currently-undocumented but already-valid `codex-app:` form as
well.

### Duplication search
- In-repo: No existing Jules ingestion of any kind found
  (`git grep -n "jules.*session\|jules.*archive\|jules.*export"` across
  `src/` and all planning directories returns zero hits — `git grep` used
  rather than filesystem `grep -rl`, per repo convention, so nested
  worktree checkouts under `.claude/worktrees/` don't skew the result).
- Sibling repos: None identified.
- External libraries: None identified — Jules' export zip format is
  undocumented and reverse-engineering it is part of this item's own scope.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting Jules ingestion specifically.
- Proposals: `contributor-identity-contract` (proposed) already models
  Jules as an agent identity for authorship purposes, giving a reusable
  naming convention (`id: jules` → `github: google-labs-jules`) worth
  reusing for this item's own identity labeling.
- Backlog: No entry found specific to Jules; the general archive-root gap
  (`backlog.md:1154-1174`) is addressed by the sibling item
  `WI-SESSION-ARCHIVE-ROOT-DEFAULT`, which this item depends on.
- Recommendation: No action beyond the dependency already recorded.

## Scope

- Reverse-engineer and document the Jules session-export zip format.
- Add a new `lrh conversation` subcommand to ingest a Jules export zip.
- Write ingested content under the canonical archive root's `jules/`
  subdirectory.
- Write per-attempt archive metadata on ingestion, mirroring Codex's
  `attempt.json` convention.
- Extend the documented `session_transcript:` pointer-scheme table with
  `jules:` and `codex-app:`.

## Required Changes

1. Reverse-engineer `jules_session_<id>.zip`'s internal structure (a sample
   set is available in the user's local staging folder) and document the
   findings before writing any parser.
2. Add a new module under `src/lrh/conversations/` (e.g.
   `jules_archive.py`) implementing zip ingestion, modeled on Codex's
   *import*-shaped commands (`import-codex-exports` /
   `convert-codex-file` in `src/lrh/conversations/codex_archive.py`) rather
   than its live-thread-archiving command (`archive-codex-thread`), since
   Jules exports arrive as pre-made zips with no live queryable endpoint.
3. Register the new command under the existing `conversation` CLI subtree
   (`src/lrh/cli/main.py:104-139`), alongside the Codex commands.
4. Call `resolve_archive_root()` (extended by
   `WI-SESSION-ARCHIVE-ROOT-DEFAULT`) and append a new `JULES_ARCHIVE_SUBDIR`
   constant, mirroring `CODEX_ARCHIVE_SUBDIR`.
5. On successful ingestion, write per-attempt metadata (e.g. `attempt.json`)
   into the archive, mirroring Codex's `import-codex-exports` convention.
   Do not write an entry into `project/sessions/index.jsonl` — its
   `SessionRecord` schema is keyed by a plain, Claude-specific `host_id`
   with no scheme-qualified pointer concept
   (`src/lrh/prompt_workflow_sessions.py:32-52`); a `jules:<id>` pointer
   belongs in the `session_transcript:` grammar (Required Change #7), a
   different registry with a different purpose (execution-record
   provenance, not archived-session bookkeeping).
6. Add re-ingestion detection (e.g. content-hash or id-based dedup),
   following the "never silently re-copy" convention already established
   for Claude's `mirror_transcript()`/`mirror_file_with_snapshot()`
   (`src/lrh/prompt_workflow_sessions.py:307-447`).
7. Update `project/executions/README.md`'s pointer-scheme table
   (lines ~57-69) to add `jules:<id>` and `codex-app:<id>`.

## Non-Goals

- Do not build a shared `SessionBackend`/adapter interface spanning Claude,
  Codex, and Jules — explicitly rejected in the governing design discussion
  as premature given the three backends' structural differences. Revisit
  only if a fourth backend's shape reveals real shared structure the
  existing three don't.
- Do not migrate or reconcile the user's already-downloaded, hand-managed
  Jules/Claude zips currently sitting in a Google-Drive-synced staging
  folder — a separate, deferred operational step.
- Do not modify Codex's existing ingestion pipeline beyond what's needed to
  keep it working unchanged.

## Acceptance Criteria

- New Jules ingestion command exists, documented, and working against real
  sample zips.
- Ingested sessions land under the canonical archive root's `jules/`
  subdirectory with per-attempt metadata, not a `project/sessions/
  index.jsonl` entry.
- `session_transcript:` pointer-scheme table documents both `jules:` and
  `codex-app:`.
- No shared backend abstraction introduced.
- Full existing test suite passes; `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- The Jules zip format is currently completely unknown to this codebase;
  the reverse-engineering step could reveal a shape different enough from
  Claude/Codex exports (e.g. multiple sessions per zip, or a different
  identity scheme) to require adjusting this item's scope before
  implementation — flag and reassess if so, rather than forcing a mismatched
  design through.
- Depends on `WI-SESSION-ARCHIVE-ROOT-DEFAULT` landing first; do not begin
  implementation against an unresolved archive root.
- **Correction from PR #608 review (Codex, confirmed):** an earlier draft
  of this item's acceptance criteria required a `jules:<id>` entry in
  `project/sessions/index.jsonl`, conflating that Claude-specific,
  `host_id`-keyed registry with the actually-correct scheme-prefixed
  `session_transcript:` pointer grammar. Fixed above; if a future need for
  scheme-qualified session-index entries emerges, that's a distinct,
  unscoped schema-migration item, not something to fold into Jules
  ingestion.
