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
  - lrh sessions sync discovers and mirrors files nested under a matched <slug>/<session-id>/ directory, preserving relative path at the destination
  - A nested directory whose owning top-level transcript lives in a different bucket is archived under the owning bucket's slug, not the bucket it physically sits in
  - An orphaned nested directory with no matching top-level transcript anywhere is archived under its own local bucket, not dropped
  - The global session-id index excludes memory/ and any other non-session subdirectory
  - mirror_transcript's atomic-write and never-shrink invariant is reused unchanged for nested files, not reimplemented
  - reconcile_child_id_aliases is invoked only for depth-1 (top-level) transcripts; nested files are archived but never fed into alias reconciliation
  - --dry-run output reports the correct nested destination path, including owning-bucket redirection
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

`discover_transcripts` in `src/lrh/prompt_workflow_sessions.py` is
`claude_projects_root.glob("*/*.jsonl")` — exactly one level deep.
`_run_sync` in `src/lrh/sessions_workflow.py` derives
`project_slug = transcript.parent.name`, which for a nested file evaluates to
the literal string `"subagents"` rather than the real project slug.
`mirror_transcript` in `src/lrh/prompt_workflow_sessions.py` flattens
the destination to `source.name`. Chained, `lrh sessions sync` silently never
archives subagent transcripts, `.meta.json` sidecars, or `tool-results/`
files anywhere in the system today. (Line numbers are intentionally omitted
here — cited numbers already drifted twice between this item's design pass
and its own PR review; cite file + symbol name instead and let an
implementor locate the current line.)

Confirmed via the only existing "nested" test,
`test_finds_nested_jsonl_files` in
`tests/assist_tests/prompt_workflow_sessions_test.py`, which tests
discovery across sibling project-slug directories only — session-depth
nesting was never in scope. `git grep -n subagent` across both source files
and the governing proposal
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

- Extend discovery to walk session-id subdirectories matched against a
  global index of all discovered top-level transcripts — not a same-bucket
  sibling check, which fails the motivating cross-bucket case (see Required
  Changes #2).
- Extend `mirror_transcript`'s destination computation to preserve relative
  path structure for nested files, attached to the transcript's *owning*
  bucket rather than whichever bucket the nested directory physically sits
  in.
- Gate `reconcile_child_id_aliases` to top-level transcripts only.
- Correct `_run_sync`'s `--dry-run` reporting for nested destinations.

## Required Changes

1. Replace `discover_transcripts`'s `list[Path]` return with a small
   dataclass carrying `(path, slug, relative_path)`, so callers never
   re-derive slug from directory position the way `_run_sync` does today.
2. **Match against a global session-id index, not a same-bucket sibling.**
   A same-bucket-only discriminator (recurse into `<slug>/<session-id>/`
   iff a sibling `<slug>/<session-id>.jsonl` exists in that *same* slug)
   fails the motivating case in Problem/Context: the 21-file fragment sat
   in a dead worktree bucket while its owning top-level transcript lived in
   a different, canonical bucket — no same-bucket sibling ever existed.
   Build one pass over all discovered top-level transcripts first (a
   `session-id -> owning slug` map across every bucket), then for each
   candidate `<slug>/<session-id>/` subdirectory, look up `<session-id>` in
   that global map:
   - **Found, in this same slug** — top-level and nested content agree;
     mirror as today's design intended.
   - **Found, in a *different* slug** — archive the nested content under
     the *owning* slug (where the map says the real top-level transcript
     lives), not the slug the subdirectory physically sits in. This is the
     case that motivated this work item.
   - **Not found anywhere** — an orphaned subdirectory with no matching
     top-level transcript at all (e.g. the host session's own transcript
     was since pruned). Archive it under its own local bucket as a
     fallback rather than silently dropping it; note this case is
     necessarily best-effort, since no owning slug can be determined.
   This still needs no hardcoded subdirectory-name allowlist (`subagents/`,
   `tool-results/`) and still naturally excludes `memory/` (no top-level
   `memory.jsonl` transcript is ever discovered, so it can never appear in
   the session-id map), so this cannot collide with the separate,
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
- A nested directory whose owning top-level transcript lives in a
  *different* bucket is still discovered and archived under the owning
  bucket's slug — the motivating cross-bucket case is covered, not just
  the same-bucket case.
- An orphaned nested directory with no matching top-level transcript
  anywhere is still archived (under its own local bucket), not silently
  dropped.
- The global session-id index correctly excludes `memory/` and any other
  non-session subdirectory (no top-level `memory.jsonl` transcript is ever
  discovered, so `memory/` never appears in the index).
- `reconcile_child_id_aliases` is never invoked for a nested file.
- `--dry-run` reports the true nested destination path, including the
  owning-bucket redirection for the cross-bucket case.
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
  one-level glob; bounded by the global-index lookup, which limits the
  walk to real session directories rather than arbitrary depth.
- Building the global session-id index requires one full pass over all
  top-level transcripts before nested discovery can run — a second pass
  over the same tree `discover_transcripts` already walks once. Session
  IDs are UUIDs, so cross-bucket collision in the index is not a realistic
  concern; the cost is purely the extra pass, not correctness.
- Changes two function signatures with existing dedicated test coverage —
  regressions would surface as test failures, not silent behavior change.
