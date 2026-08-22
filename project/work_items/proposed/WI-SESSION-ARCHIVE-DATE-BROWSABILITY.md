---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-DATE-BROWSABILITY
title: Investigate and resolve Claude raw-archive date-browsability vs. Codex's date-partitioned layout
type: investigation
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - migrate_existing_raw_archive_without_confirmation
acceptance:
  - The layout asymmetry (Codex exports/<YYYY>/<MM>/... vs. Claude raw/<slug>/<session-id>.jsonl) and its load-bearing consumers are documented with evidence
  - At least the four candidate approaches the user named, plus a non-physical view/index approach, are presented to the user with pros/cons before any implementation begins
  - The user has explicitly chosen a direction before any code change or migration is made
  - The chosen direction is implemented (or, if the decision is to wait/defer, that decision and its trigger condition are recorded instead)
  - If any existing archived file is moved or restructured, bucketlib.archived_copy()'s independent path re-derivation and prompt_workflow_memory.py's memory-sync path convention are confirmed still correct, not just the primary sync path
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - investigation_notes
artifacts_expected:
  - investigation_notes
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/sessions_workflow.py
  - experimental/rescue_claude_sessions/bucketlib.py
---

# Investigate and resolve Claude raw-archive date-browsability vs. Codex's date-partitioned layout

## Summary

Codex exports are organized for human browsing by date
(`~/.local/share/lrh/session-archive/codex/exports/<YYYY>/<MM>/<export-id>/`);
Claude's mirrored session archive is not
(`~/.local/share/lrh/session-archive/raw/<project-slug>/<session-id>.jsonl`).
At hundreds of sessions, the flat slug-keyed layout is harder to browse than
the date-partitioned one. Investigate the real options for resolving this
asymmetry and land on a decision with the user before implementing anything.

## Problem / Context

`mirror_transcript()` (`src/lrh/prompt_workflow_sessions.py:307-353`)
computes the Claude archive destination purely from project-slug and
session-id (`prompt_workflow_sessions.py:340`) — no timestamp of any kind is
used. This mirrors Claude Code's own on-disk `~/.claude/projects/<slug>/`
naming convention, per `project_slug_for_path()`'s own docstring
(`prompt_workflow_sessions.py:669-686`), which appears to be the only reason
for the current shape — no design rationale for "why not date" was found in
`PROP-LRH-SESSION-ARCHIVE-SYNC` or `project/memory/decision_log.md`.

This shape is not purely cosmetic, though — two other places independently
depend on it:

- `experimental/rescue_claude_sessions/bucketlib.py:50`'s `archived_copy()`
  **independently re-derives** the same `raw/<slug>/<session-id>.jsonl`
  path to check whether a live transcript has already been archived;
  `archive_split_transcripts.py:144-154` gates a destructive operation
  (moving stale duplicates aside) on that check.
- `src/lrh/prompt_workflow_memory.py:693` writes memory sync to
  `raw/<slug>/memory/**`, explicitly documented as matching `sessions
  sync`'s own `raw/<slug>/` layout (lines 654-656).

There is also no cheap, reliable date signal available today: a Claude
session JSONL's `timestamp` field is not on line 1 (first appears around
line 4 in a sampled live transcript), and file mtime — the only other
candidate — reflects when a file was last touched or copied, not
necessarily when the session happened, so naively bucketing by mtime risks
misdating sessions moved or resynced later.

A prior design pass in this session recommended, as a starting point, *not*
physically migrating `raw/` at all: instead building a date-organized view
(index or symlink tree) alongside the existing slug-keyed layout, since
`lrh sessions report` is already a planned-but-unimplemented Stage 3
feature (`src/lrh/sessions_workflow.py:11,73`) that a view like this would
naturally extend. That recommendation is the **starting point for this
investigation, not its predetermined conclusion** — the user has asked that
this item genuinely re-open the option set at implementation time.

### Duplication search
- In-repo: No existing date-organized view or migration tooling found for
  the `raw/` archive.
- Sibling repos: None identified.
- External libraries: None identified — this is LRH-specific archive
  layout policy.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly; this item originates
  from a same-session observation, not a pre-existing request.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` documents the current `raw/`
  layout as a given (`00_proposal.md:210`) but does not discuss
  date-browsability.
- Backlog: No matching entries found.
- Recommendation: No action beyond this item.

## Investigation Goals

Present the user with, at minimum, these candidate directions before any
implementation, and let them choose (or propose a variant/combination):

1. **A non-physical date-organized view** (index or symlink tree) over the
   existing slug-keyed `raw/` archive, generated at sync time from the
   timestamp `lrh sessions sync` already observes when it mirrors a file —
   no migration, no change to either load-bearing consumer above. (Prior
   recommendation; not predetermined.)
2. **Better timestamping** — establish a reliable, cheap date signal (e.g.
   read past the JSONL header lines once and cache the result, or define
   and document a trustworthy mtime-preservation contract through the
   mirror path) as a prerequisite for any date-based feature, view or
   otherwise.
3. **Fix save-and-search going forward, with backward compatibility to the
   old view** — change `mirror_transcript()`'s destination for newly
   synced sessions only, leaving already-archived sessions in place under
   the old shape, with both shapes supported by any tooling that reads the
   archive.
4. **Wait as sessions accumulate** — defer any change until the volume or
   pain justifies the migration cost; record the trigger condition (e.g. a
   session count threshold) that should prompt revisiting this item.
5. **Migrate after all existing sessions are closed** — a one-time physical
   migration of the full `raw/` tree to a date-based layout, performed only
   once no session is actively writing to it, updating both dependent
   consumers (`bucketlib.archived_copy()`, `prompt_workflow_memory.py`'s
   memory-sync path) in lockstep.

For each, evaluate against: risk to the two documented load-bearing
consumers, migration cost for already-archived sessions, and whether it
actually solves the stated browsing problem at hundreds-of-sessions scale.

## Suggested Diagnostics

- Confirm current archive size (`find <archive-root>/raw -name '*.jsonl' |
  wc -l`) to ground "hundreds of sessions" against the actual count.
- Confirm whether `lrh sessions sync` has access to a trustworthy
  per-session timestamp at mirror time (it observes the live source file
  directly, before any copy-related mtime changes could occur) as the basis
  for option 1's index, if chosen.
- Re-verify `bucketlib.archived_copy()` and the `prompt_workflow_memory.py`
  memory-sync path against current code before finalizing any option that
  touches the physical layout, since prior findings could drift.

## Non-Goals

- Do not implement any specific option until the user has chosen one.
- Do not touch Codex's `exports/<YYYY>/<MM>/` layout — it is not part of
  the asymmetry being resolved and is not itself load-bearing elsewhere.
- Do not silently migrate or restructure existing archived files as a side
  effect of investigation.

## Acceptance Criteria

- Options are presented and a direction is explicitly chosen by the user.
- The chosen direction is implemented, or a defer decision with a trigger
  condition is recorded.
- Both documented load-bearing consumers are confirmed correct if the
  physical layout changes.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `scripts/test` (if any code changes are made)

## Risk Notes

- The two independent path-construction sites
  (`mirror_transcript`/`bucketlib.archived_copy()`) are the main regression
  risk for any option that touches the physical layout — changing one
  without the other breaks `archive_split_transcripts.py`'s dedup-gate
  check silently, which given its own stated safety posture ("Archive
  stale transcripts; never delete... Only archive a copy proven to be a
  byte-exact prefix") is a real, not hypothetical, risk.
