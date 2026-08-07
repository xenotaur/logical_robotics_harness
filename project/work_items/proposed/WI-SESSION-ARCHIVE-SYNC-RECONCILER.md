---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-SYNC-RECONCILER
title: lrh sessions sync, discover, and link — archive reconciler
type: deliverable
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
depends_on:
  - WI-SESSION-ARCHIVE-SYNC-CAPTURE
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_sessions_report
  - implement_index_enrichment
  - implement_scheduled_or_hook_sync
  - modify_session_transcript_schema
acceptance:
  - lrh sessions sync mirrors ~/.claude/projects/**/*.jsonl into a configurable local archive root, raw-file-first ordering, and re-copies (never truncates/shrinks/deletes) a growing transcript by comparing size/mtime, not mere existence
  - lrh sessions sync harvests /export zip metadata.json (sessionId, cliSessionId, prNumber, prs[], branch, title) and upserts matching entries into project/sessions/index.jsonl via the existing record_session_observation primitive, without copying transcript bodies or logs
  - Child-id alias collection scans distinct line-level sessionId values inside each JSONL, not just filename stems, so forked lineages are not left with incomplete alias sets
  - lrh sessions discover lists sessions for a project with archive/export awareness, surfacing the host id where harvest has resolved one
  - lrh sessions link can promote a bare child id to a host-keyed session_transcript pointer once harvest makes that resolution authoritative
  - No change to the session_transcript scalar/sequence grammar or its validator rules
  - Any edit to src/lrh/skills/ is mirrored identically in .claude/skills/, verified by diff -r exiting 0
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/prompt_workflow.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
  - tests/cli_tests/prompt_test.py
  - project/design/backlog.md
---

# lrh sessions sync, discover, and link — archive reconciler

## Summary

Implement `lrh sessions sync` (local transcript archive reconciler: raw-JSONL
mirror plus `/export` metadata harvest) and `lrh sessions discover`/`link`,
Stage 2 of `WS-SESSION-ARCHIVE-SYNC`.

## Problem / Context

Stage 1 (`WI-SESSION-ARCHIVE-SYNC-CAPTURE`, resolved via PR #498) closed the
*forward* half of the identity-mapping gap — new sessions now capture both
ids going forward. It did not touch the *retroactive* half: sessions whose
transcripts already exist on disk or in `/export` zips, and the ~30-day
Claude Code retention window that keeps eroding them
(`PROP-LRH-SESSION-ARCHIVE-SYNC` measured 28%→14% dangling-pointer
resolution over just six days). This item builds the reconciler that
mirrors transcripts into a durable local archive and harvests `/export`
`metadata.json` — the only artifact that maps host↔child↔PR for pointers
that already dangle (Decision 1).

### Duplication search
- In-repo: No existing implementation. `src/lrh/prompt_workflow_sessions.py`'s
  `record_session_observation()` (Stage 1) is the merge/upsert primitive this
  item's harvest logic should call, not duplicate.
- Sibling repos: None identified.
- External libraries: None identified for adoption as a whole; rsync/
  restic-style idempotent-mirror semantics are adopted internally per the
  proposal.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-EXEC-SESSIONS-DISCOVERY` (PR #435) requested `discover`/
  `link` but was closed unmerged and reconciled against this design — four
  of its five acceptance criteria didn't hold once archive/export-harvest
  awareness became part of the design (see its closing comment for detail).
  Its three carry-forward items — permissive-with-a-gate `forbidden_actions`,
  append-safety, complete child-id aliases — are incorporated below.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` (Decision 1, Decision 2,
  Implementation Plan Stage 2) is the governing design.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Implement `lrh sessions sync`: configurable local archive root; raw-JSONL
  mirror (append-safe, raw-file-first ordering); `/export` zip
  `metadata.json` harvest, upserted into `project/sessions/index.jsonl`.
- Implement `lrh sessions discover` and `lrh sessions link`, archive/harvest
  aware (unlike PR #435's local-filesystem-only design).
- Reuse Stage 1's `record_session_observation` merge primitive rather than
  reimplementing index-write logic.

## Required Changes

1. Extend `src/lrh/prompt_workflow_sessions.py` (or a sibling module) with
   archive-mirror logic: copy `~/.claude/projects/**/*.jsonl` to a
   configurable local root, comparing size/mtime to detect growth and
   re-copying (never leaving a shorter archived copy than the source).
2. Add `/export` zip parsing: read `metadata.json` (`sessionId`,
   `cliSessionId`, `prNumber`, `prs[]`, `branch`, `title`) without extracting
   transcript bodies or `logs/`; call `record_session_observation` to upsert
   the resulting host↔child↔PR mapping.
3. Add child-id alias collection that scans distinct line-level `sessionId`
   values inside each JSONL (not just the filename stem) — the case that
   PR #435's closing comment documents concretely (a file named `f1e9c968…`
   contains an in-file `sessionId` of `aff3efd3…` appearing in no filename
   anywhere).
4. Add `lrh sessions sync`, `discover`, `link` CLI subcommands to
   `src/lrh/prompt_workflow.py` (or a new `sessions` subparser group in
   `src/lrh/cli/main.py`, whichever fits existing conventions better —
   implementor's judgment, consistent with the codebase).
5. Update both skill mirrors' reference docs
   (`src/lrh/skills/lrh-implement/references/execution-session-reference.md`
   and any closeout-workflow reference) to describe `sync`/`discover`/`link`.
6. Add unit tests: archive mirroring (growth re-copy, no-truncation
   invariant), export-metadata parsing, alias collection from line-level
   `sessionId` values, and CLI wiring.

## Non-Goals

- Does not implement `lrh sessions report` — Stage 3.
- Does not implement index *enrichment* (era-general keys beyond
  `claude-app:`, dedup latest-wins across multiple export zips) — Stage 3
  builds on Stage 1's index, this item only writes to it via the existing
  primitive.
- Does not implement the weekly scheduled sync or the `SessionEnd` hook —
  Stage 4.
- Does not change the `session_transcript` scalar/sequence grammar or its
  `lrh validate` rules.
- Does not build the encrypted off-machine archive tier — permitted by the
  proposal but explicitly deferred.
- Does not resolve the archive-root-location open question itself, but must
  make the root configurable per that question's eventual resolution.

## Acceptance Criteria

- `lrh sessions sync` mirrors transcripts into a configurable local archive,
  re-copying (never truncating) a growing source.
- `lrh sessions sync` harvests `/export` `metadata.json` and upserts entries
  into `project/sessions/index.jsonl` via the existing merge primitive, never
  copying transcript bodies or logs.
- Child-id alias collection scans line-level `sessionId` values, not just
  filenames.
- `lrh sessions discover`/`link` are archive/harvest-aware.
- No change to `session_transcript` grammar or validator.
- `diff -r src/lrh/skills/ .claude/skills/` exits 0 for any touched skill.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`

## Risk Notes

- Export-zip parsing touches user-authored session data (bundled `logs/`,
  `local-session-state.json`); scope strictly to `metadata.json` fields only,
  per Decision 2's non-goal against copying bodies/logs.
- Archive-mirror re-copy logic must be genuinely atomic (temp-write + rename)
  to honor the never-truncate invariant under interruption.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SESSION-ARCHIVE-SYNC.md`
- Design: `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Superseded prior art: PR #435 (`WI-EXEC-SESSIONS-DISCOVERY`, closed unmerged)
