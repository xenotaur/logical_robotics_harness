---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-SYNC-CLOSEOUT-BASELINE
title: Reconcile session archive sync closeout baseline
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
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - docs/reference/cli/sessions.md
  - src/lrh/skills/lrh-closeout/SKILL.md
depends_on:
  - WI-SESSION-ARCHIVE-SYNC-CAPTURE
  - WI-SESSION-ARCHIVE-SYNC-RECONCILER
  - WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT
  - WI-SESSION-SYNC-NESTED-ARTIFACTS
  - WI-SESSION-ARCHIVE-SYNC-REPORT
  - WI-SESSION-ARCHIVE-SYNC-SCHEDULED-CLOSEOUT-SYNC
blocked_by: []
expected_actions:
  - edit_file
  - create_report
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - commit_raw_transcripts
  - print_raw_transcript_bodies
  - modify_session_transcript_schema
  - implement_encrypted_off_machine_archive
  - silently_ignore_archive_gaps
  - trigger_github_review_agents
acceptance:
  - "A post-Stage-1 `lrh sessions report` baseline is recorded with command, timestamp, counts, and representative gap categories without printing transcript bodies"
  - "Remaining post-Stage-1 pending, dangling, and unarchived records are classified as fixed, expected exception, or linked follow-up work"
  - "The weekly scheduled-sync exit criterion is resolved explicitly as either documented local setup, confirmed host configuration, or a follow-up/blocker"
  - "`PROP-LRH-SESSION-ARCHIVE-SYNC` and `WS-SESSION-ARCHIVE-SYNC` are updated consistently, or a concrete blocker is recorded instead of closing"
  - "`lrh validate` reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - validation_output
artifacts_expected:
  - project/workstreams/resolved/WS-SESSION-ARCHIVE-SYNC.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/evidence/EV-0012.md
  - project/sessions/index.jsonl
  - project/executions/
---

## Summary

Reconcile the final closeout baseline for `WS-SESSION-ARCHIVE-SYNC` by
recording the current post-Stage-1 archive coverage report, classifying
remaining gaps, resolving the weekly scheduled-sync criterion, and either
closing/adopting the workstream honestly or recording the blocker that prevents
closeout.

## Problem / Context

`WS-SESSION-ARCHIVE-SYNC` has delivered all listed implementation leaves, but
its exit criteria require more than resolved work items: `/lrh-closeout` sync
integration, weekly scheduled sync configuration, a clean post-Stage-1
`lrh sessions report`, `lrh validate`, and an advanced/adopted
`PROP-LRH-SESSION-ARCHIVE-SYNC`. A post-Stage-1 report run from the Stage 1
merge timestamp (`2026-08-06T08:39:36+00:00`) on 2026-08-23 found
`records_checked 443`, `pointers_checked 436`, `pending 39`, `dangling 87`,
`unarchived 75`, and `unsupported 0`, so closing the workstream without a
baseline decision would create a false sense of archive completeness. The
Stage 3 report item intentionally made gaps visible; this item decides what to
do with those visible gaps before closeout.

### Duplication search

- In-repo: No duplicate closeout-baseline work item found. Related proposed
  follow-ups exist: `WI-CODEX-SESSION-ID-RESOLVER` covers Codex pointer
  resolution, and `WI-PROJECT-SLUG-SYMLINK-RESOLUTION` covers Claude bucket
  slug correctness; neither owns the workstream closeout/adoption decision.
- Sibling repos: None identified for this LRH control-plane closeout decision.
- External libraries: None identified. This is LRH-specific control-plane
  reconciliation, not a general backup or archive-library problem.
- Recommendation: Proceed with a narrow closeout-baseline operation that links
  or defers targeted follow-ups rather than duplicating them.

### Demand search

- Work items: No existing proposed `WI-SESSION-ARCHIVE-SYNC-CLOSEOUT-BASELINE`
  or equivalent was found.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` and `WS-SESSION-ARCHIVE-SYNC`
  create the demand by requiring a clean/auditable closeout state.
- Backlog: Related archive/sync concerns exist, but no matching
  closeout-baseline item was found.
- Recommendation: Link this item to `WS-SESSION-ARCHIVE-SYNC` and use it to
  decide whether the workstream can close now, closes with documented
  exceptions, or needs additional follow-up leaves.

## Scope

- Run and record a metadata-only post-Stage-1 `lrh sessions report` baseline.
- Classify remaining `pending`, `dangling`, and `unarchived` results without
  exposing raw transcript content.
- Resolve the meaning of the weekly scheduled-sync exit criterion in light of
  the documented human-controlled `launchd` setup.
- Update the session archive sync proposal/workstream lifecycle state only if
  the closeout criteria are honestly satisfied or explicitly amended by human
  decision.
- Link narrow unresolved issues to existing or new follow-up work instead of
  hiding them inside workstream closeout prose.

## Required Changes

1. Run or refresh
   `lrh sessions report --project-root . --since-created-at 2026-08-06T08:39:36+00:00 --format json`
   and summarize counts plus representative categories in a committed
   metadata-only evidence artifact.
2. Review remaining `pending`, `dangling`, and `unarchived` entries and
   classify each class of gap as fixed during this item, expected historical
   residue, or follow-up work.
3. Evaluate whether proposed items such as `WI-CODEX-SESSION-ID-RESOLVER` and
   `WI-PROJECT-SLUG-SYMLINK-RESOLUTION` should be linked as follow-ups or
   blockers.
4. Decide and record what "weekly scheduled sync is configured" means for
   closeout: documented setup path exists, host-local setup has been confirmed,
   or closeout remains blocked.
5. Update `PROP-LRH-SESSION-ARCHIVE-SYNC` lifecycle metadata and bucket
   location if adoption/implementation is justified.
6. Update `WS-SESSION-ARCHIVE-SYNC` work-item list, exit criteria, status,
   stage, and bucket location consistently if closeout is justified.
7. Run validation and leave no raw transcript content, absolute private archive
   paths, or secret-bearing data in committed files.

## Non-Goals

- Do not commit raw transcript exports, raw JSONL transcript files, Codex raw
  captures, or `/export` logs.
- Do not print raw transcript bodies as part of baseline recording.
- Do not change the `session_transcript` grammar.
- Do not implement encrypted or off-machine archive backup.
- Do not solve every archive quality follow-up unless it is required for this
  closeout decision.
- Do not trigger GitHub review agents manually.

## Acceptance Criteria

- A post-Stage-1 `lrh sessions report` baseline is recorded with command,
  timestamp, counts, and representative gap categories without printing
  transcript bodies.
- Remaining post-Stage-1 pending, dangling, and unarchived records are
  classified as fixed, expected exception, or linked follow-up work.
- The weekly scheduled-sync exit criterion is resolved explicitly as either
  documented local setup, confirmed host configuration, or a follow-up/blocker.
- `PROP-LRH-SESSION-ARCHIVE-SYNC` and `WS-SESSION-ARCHIVE-SYNC` are updated
  consistently, or a concrete blocker is recorded instead of closing.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh sessions report --project-root . --since-created-at 2026-08-06T08:39:36+00:00 --format json`
- `lrh validate`

## Risk Notes

- False confidence is the main risk: a closeout that says the archive invariant
  is satisfied while the report still shows unclassified gaps would weaken the
  point of the whole workstream.
- The report may include historical or expected gaps; the task is not
  necessarily to force all counts to zero, but to make every remaining class
  explicit and actionable.
- Weekly scheduling has host-local state that may not be fully repo-observable,
  so the implementation must distinguish documented setup from verified local
  installation.
