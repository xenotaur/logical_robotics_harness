---
id: WI-SESSION-INDEX-WRITTEN-BRANCHES-HISTORY
title: "Retain prior branches in written_branches when a session's branch changes"
type: deliverable
status: proposed
blocked: false
blocked_reason: null
resolution: null
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "record_session_observation keeps a session's previous branch in written_branches whenever a later observation for the same host_id sets a different non-empty branch; branch itself stays latest-wins"
  - "An observation with the same branch, with no branch, or with an empty-string branch leaves both branch and written_branches unchanged"
  - "Explicit --written-branch values still union in as before, and the stored list stays sorted and duplicate-free"
  - "The index is still byte-stable across repeated identical observations"
  - "Docs that describe written_branches as reserved/unused (the prompt_workflow_sessions.py module docstring, the --written-branch help, and execution-session-reference.md in src/ and every tracked install copy) are updated to describe the new behavior"
  - "scripts/test passes with new unit tests covering branch change, same branch, omitted branch, empty-string branch, and the explicit --written-branch union; lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
  - src/lrh/prompt_workflow.py
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
  - .claude/skills/lrh-implement/references/execution-session-reference.md
  - .agents/skills/lrh-implement/references/execution-session-reference.md
  - .gemini/plugins/lrh/skills/lrh-implement/references/execution-session-reference.md
---

## Summary

`project/sessions/index.jsonl` keeps one row per Claude.app host session.
`branch` is latest-wins, and `written_branches` was meant to hold the other
branches a session wrote to. Nothing ever fills it, though: it only grows
from `lrh prompt record-session-alias --written-branch`, and no skill passes
that flag. So each time a long session moves to a new PR branch, the
previous branch name is lost. Make `_merge` in
`src/lrh/prompt_workflow_sessions.py` add the outgoing branch to
`written_branches` whenever an observation replaces it with a different
one, so the index keeps the session's branch history automatically for
every caller.

## Problem / Context

`_merge` (`src/lrh/prompt_workflow_sessions.py`) treats `title` and `branch`
as latest-wins scalars, and `child_ids`, `prs` and `written_branches` as
unioned sets. The `--written-branch` flag (`src/lrh/prompt_workflow.py`) is
documented as "Reserved for Stage 3 fork stitching". The execution-session
reference (`src/lrh/skills/lrh-implement/references/execution-session-reference.md`)
says the same: "reserved for Stage 3's fork stitching, unused until then".

`PROP-LRH-SESSION-ARCHIVE-SYNC` planned Stage 3 to enrich the index ("fork
stitching via branch/PR"). Stage 3 shipped as the `lrh sessions report`
coverage check instead, and nothing ever wrote `written_branches`.

Observed on `origin/main` (2026-10-12): all 48 rows have an empty
`written_branches`, and 31 rows list more than one PR. Each of those 31 has
silently lost every branch but its last. Example: host `5a942286…` lists
PRs #793, #804, #808, #816 and #828 but keeps only
`branch: xenotaur/chore/normalize-claude-app-agent-field`. A substitute
self-review on PR #828 surfaced this; it is recorded as a follow-up in that
PR's records.

The data loss is limited: each PR still records its head branch on GitHub.
But the index is supposed to be the local, offline place for
session-to-branch lineage, and this design work, when it lands, would be
the first thing to write the reserved field.

Three call paths set `branch`. All of them go through
`record_session_observation` and benefit without changes:
- `lrh prompt record-session-alias` (`/lrh-implement` Step 9,
  `/lrh-closeout`);
- the export-zip harvest in `sync_export`;
- the child-alias reconciler. This path never passes a branch, so it is
  unaffected.

**Prior art check:**
- *Duplication search:* searched `project/work_items/`, `project/design/`,
  `project/workstreams/` and the open PRs for `written_branches`,
  `record-session-alias` and session alias. No existing work item or
  backlog entry covers this. `WS-SESSION-ARCHIVE-SYNC` and its work items
  are resolved. Open PR #797 edits `prompt_workflow_sessions.py`, but only
  for Antigravity session-id resolution, not `_merge`. Open PRs #831, #832
  and #833 touch `index.jsonl` only as their own session records.
- *Demand search:* the only demand found is `PROP-LRH-SESSION-ARCHIVE-SYNC`'s
  unshipped Stage 3 "fork stitching via branch/PR" intent, and the
  "recovering `written_branches`" note in `persist_export_metadata`'s
  docstring. This work item implements the simplest part of that intent.

## Scope

- In `_merge`, when an incoming `branch` is non-empty and differs from the
  existing non-empty `branch`, add the existing branch to `written_branches`
  before replacing it.
- Unit tests in `tests/assist_tests/prompt_workflow_sessions_test.py`.
- Wording updates where `written_branches` is described as reserved/unused:
  - the module docstring of `src/lrh/prompt_workflow_sessions.py`
    ("branch/written_branches fields reserved for later fork stitching");
  - the `--written-branch` help text in `src/lrh/prompt_workflow.py`;
  - `execution-session-reference.md` in `src/`, plus re-rendered
    `.claude`, `.agents` and `.gemini` copies, each regenerated one skill at
    a time via `lrh skills install --source <one-skill scratch dir>`.

## Required Changes

1. `src/lrh/prompt_workflow_sessions.py` `_merge`: if `existing` has a
   non-empty `branch`, the incoming `branch` is non-empty (truthy, not
   merely `is not None`), and `branch != existing.branch`, add
   `existing.branch` to the `written` set. An empty-string incoming
   `branch` must be treated like an omitted one: it must not replace the
   existing `branch` or add anything to history. `--branch ""` and export
   metadata with `"branch": ""` both reach `_merge` as `""`; see
   `sync_export`. Keep `branch` latest-wins for non-empty values and keep
   `written_branches` sorted. Update the `record_session_observation`
   docstring, and the module docstring at the top of the file ("reserved
   for later fork stitching"), to describe the new behavior.
2. `tests/assist_tests/prompt_workflow_sessions_test.py`: add tests for:
   - a branch change that preserves the old branch;
   - a repeated identical branch with no history entry;
   - an omitted branch that keeps both the branch and the history;
   - an empty-string branch that leaves both `branch` and
     `written_branches` unchanged;
   - the history plus an explicit `written_branches` union, sorted and
     deduplicated.

   Extend `test_title_and_branch_latest_wins` to assert `written_branches ==
   ("old-branch",)`.
3. `src/lrh/prompt_workflow.py`: change the `--written-branch` help from
   "Reserved for Stage 3 fork stitching." to say it records additional
   branches, and that prior branches are added automatically when `--branch`
   changes.
4. `src/lrh/skills/lrh-implement/references/execution-session-reference.md`:
   replace "reserved for Stage 3's fork stitching, unused until then" (and
   the "reserved for later fork stitching" phrasing) with the new behavior.
   Regenerate the `lrh-implement` install copies under `.claude/skills/`,
   `.agents/skills/` and `.gemini/plugins/lrh/skills/`.

## Non-Goals

- Does not backfill the existing 48 rows (that would need a per-PR
  head-branch lookup). That is a possible separate one-off.
- Does not change the `branch` latest-wins semantics, the
  `session_transcript` grammar, or the index file format and keys.
- Does not implement broader fork stitching (cross-host linking by shared
  branch/PR) or change `lrh sessions discover`/`link`/`report`.
- Does not change any skill's call to `record-session-alias`.

## Acceptance Criteria

- A later observation that sets a different non-empty `branch` keeps the
  previous branch in `written_branches`; `branch` stays latest-wins.
- The same branch, an omitted branch, or an empty-string branch leaves
  both `branch` and `written_branches` unchanged.
- Explicit `--written-branch` values still union in; the list stays sorted
  and duplicate-free.
- The index stays byte-stable across repeated identical observations.
- The `prompt_workflow_sessions.py` module docstring, the CLI help, and the
  `src/` and all install copies of `execution-session-reference.md`
  describe the new behavior.
- `scripts/test` passes with the new tests, and `lrh validate` reports 0
  errors.

## Validation

- scripts/version tools
- scripts/format --check --diff
- scripts/lint
- scripts/test tests/assist_tests/prompt_workflow_sessions_test.py
- scripts/test
- lrh validate
- lrh skills check --local --target all --source current-repo
- git grep -n "unused until then\|reserved for later fork stitching" -- src/lrh .claude/skills .agents/skills .gemini/plugins/lrh/skills (must return nothing)

## Risk Notes

- The export-zip harvest (`sync_export`) can apply an older export's
  `branch` after a newer one. Today that silently overwrites the newer
  branch. With this change the newer branch is kept in `written_branches`
  instead of being lost, which is strictly better, though `branch` may
  still briefly show an older value until the next live observation.
- Every later `record-session-alias` call will produce larger
  `index.jsonl` diffs as history accumulates. This is expected and
  reviewable.
- `.gemini` copies are test-pinned since PR #819. Regenerate the one
  skill, not a full install.
