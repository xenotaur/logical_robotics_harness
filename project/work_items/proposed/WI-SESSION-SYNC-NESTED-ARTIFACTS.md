---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-SYNC-NESTED-ARTIFACTS
title: lrh sessions sync — discover and archive nested session artifacts
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
depends_on:
  - WI-SESSION-ARCHIVE-SYNC-RECONCILER
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_session_transcript_schema
  - implement_memory_archival
  - migrate_existing_archive_layout
acceptance:
  - lrh sessions sync discovers and mirrors files under <slug>/<session-id>/ whenever a sibling <slug>/<session-id>.jsonl exists, preserving the relative path at the destination
  - Discovery recurses only into a session-id directory with a matching sibling top-level transcript; unrelated directories (e.g. memory/) are never walked
  - mirror_transcript's atomic-write and never-shrink invariant is reused unchanged for nested files, not reimplemented
  - reconcile_child_id_aliases is invoked only for depth-1 (top-level) transcripts; nested files are archived but never fed into alias reconciliation
  - --dry-run output reports the correct nested destination path
  - Already-archived top-level content (raw/<slug>/<file>.jsonl) is unchanged — no migration step
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/sessions_workflow.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
---

# lrh sessions sync — discover and archive nested session artifacts

## Summary

Extend `lrh sessions sync`'s default discovery and mirroring to walk
session-adjacent nested content — subagent transcripts, their `.meta.json`
sidecars, and `tool-results/` files — not just the top-level
`<slug>/<session-id>.jsonl` transcript it archives today.

## Problem / Context

`discover_transcripts` (`src/lrh/prompt_workflow_sessions.py:245`) is
`claude_projects_root.glob("*/*.jsonl")` — exactly one level deep.
`_run_sync` (`src/lrh/sessions_workflow.py:134`) derives
`project_slug = transcript.parent.name`, which for a nested file evaluates to
the literal string `"subagents"` rather than the real project slug.
`mirror_transcript` (`src/lrh/prompt_workflow_sessions.py:255-291`) flattens
the destination to `source.name`. Chained, `lrh sessions sync` silently never
archives subagent transcripts, `.meta.json` sidecars, or `tool-results/`
files anywhere in the system today.

Confirmed via the only existing "nested" test,
`test_finds_nested_jsonl_files`
(`tests/assist_tests/prompt_workflow_sessions_test.py:246`), which tests
discovery across sibling project-slug directories only — session-depth
nesting was never in scope. `grep -rn subagent` across both source files and
the governing proposal
(`project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`)
returns nothing.

Concretely discovered in the session that produced this work item: a dead
worktree bucket contained a session-id-named subdirectory (10 subagent
`.jsonl` transcripts, 10 `.meta.json` sidecars, 1 `tool-results/` file — 21
files total) belonging to a live, healthy, currently-resumable session whose
own top-level transcript lives in a completely different, canonical bucket.
Invisible to both ad-hoc audit tooling and to `lrh sessions sync` itself.
Manually copied, hash-verified, and tar'd to durable storage as a stopgap
only — this work item is what provides real archive coverage going forward.

The workstream's own stated goal is scope-agnostic on this point: *"so that
no repo-changing agent session is ever lost"*
(`project/workstreams/active/WS-SESSION-ARCHIVE-SYNC.md:8`) — a subagent that
edits files is exactly a repo-changing agent session by that definition.

### Duplication search
- In-repo: No existing implementation found.
- Sibling repos: None identified.
- External libraries: None identified — specific to Claude Code's on-disk transcript layout.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: `subagent` hits in `review-wait-posture` and
  `invocation-and-gate-reset` are both about self-review dispatch mechanics,
  unrelated to archival — not a match.
- Backlog: 12 `subagent` hits, all in the same self-review-mechanism context —
  not a match.
- Recommendation: No action.

## Scope

- Extend discovery in `discover_transcripts` to also walk matched
  session-id subdirectories under each project slug.
- Extend `mirror_transcript`'s destination computation to preserve relative
  path structure for nested files.
- Gate `reconcile_child_id_aliases` to top-level transcripts only.
- Correct `_run_sync`'s `--dry-run` reporting for nested destinations.

## Required Changes

1. Replace `discover_transcripts`'s `list[Path]` return with a small
   dataclass carrying `(path, slug, relative_path)`, so callers never
   re-derive slug from directory position the way `_run_sync:134` does today.
2. Recurse into a `<slug>/<session-id>/` subdirectory **iff** a sibling
   `<slug>/<session-id>.jsonl` exists — a self-describing discriminator that
   needs no hardcoded subdirectory-name allowlist (`subagents/`,
   `tool-results/`) and naturally excludes `memory/` (no sibling
   `memory.jsonl` exists), so this cannot collide with the separate,
   already-backlogged memory-archival gap in `project/design/backlog.md`.
3. Under a matched session directory, discover any regular file, not
   `*.jsonl` only — `.meta.json` sidecars and `tool-results/*.txt` are part
   of the same session fragment per the evidence above.
4. `mirror_transcript`'s destination becomes
   `archive_root / "raw" / slug / relative_path` (`relative_path` is
   `source.name` for top-level files, unchanged from today — no migration
   needed for already-archived content).
5. Gate `reconcile_child_id_aliases` to `len(relative_path.parts) == 1`.
6. Fix `_run_sync`'s `--dry-run` print statement, which currently reports
   the old flat destination shape unconditionally.
7. Update `tests/assist_tests/prompt_workflow_sessions_test.py`: new
   coverage for nested discovery/mirroring (including that `memory/` and
   other non-session directories are correctly excluded), plus updates to
   existing top-level tests for the new return type.

## Non-Goals

- Do not implement the separate memory-archival gap (`memory/` mirroring) —
  tracked independently in `project/design/backlog.md`.
- Do not migrate or rewrite already-archived top-level content.
- Do not add a `--include-subagents`-style opt-in flag — rejected during
  design; the `--exports-dir` opt-in precedent doesn't transfer, since
  subagent transcripts are already local and self-discoverable the same way
  top-level transcripts are.
- Do not implement `lrh sessions report`, index enrichment, or scheduled/hook
  sync — later stages per `WS-SESSION-ARCHIVE-SYNC`'s exit criteria.
- Do not change the `session_transcript` field's scalar/sequence grammar.

## Acceptance Criteria

- `lrh sessions sync` mirrors files nested under a matched
  `<slug>/<session-id>/` directory, preserving relative path at the
  destination.
- The sibling-`.jsonl` discriminator correctly excludes `memory/` and any
  other non-session subdirectory.
- `reconcile_child_id_aliases` is never invoked for a nested file.
- `--dry-run` reports the true nested destination path.
- Already-archived top-level content is byte-identical before and after.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Recursive discovery costs more filesystem calls than the current
  one-level glob; bounded by the sibling-`.jsonl` discriminator, which
  limits the walk to real session directories rather than arbitrary depth.
- Changes two function signatures with existing dedicated test coverage —
  regressions would surface as test failures, not silent behavior change.
