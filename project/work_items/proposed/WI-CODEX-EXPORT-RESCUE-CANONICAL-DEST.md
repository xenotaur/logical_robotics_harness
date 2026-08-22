---
resolution: null
blocked_reason: null
blocked: false
id: WI-CODEX-EXPORT-RESCUE-CANONICAL-DEST
title: Point rescue_codex_exports at the canonical durable archive and consolidate stranded exports
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
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_script
forbidden_actions:
  - force_push
  - delete_branch
  - print_transcript_body
acceptance:
  - experimental/rescue_codex_exports/move_exports.py's default --dest no longer points at ~/.lrh/private/codex, and instead points at a location under the canonical archive root (~/.local/share/lrh/session-archive/codex/), distinct from the date-partitioned exports/<YYYY>/<MM>/ tree the routine capture path writes to
  - experimental/rescue_codex_exports/README.md's ownership table no longer calls ~/.lrh/private/codex/ "the durable archive itself"
  - project/design/backlog.md's rescue_codex_exports entry no longer states WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT "remains proposed" (it is resolved, PR #579) and links this item as the follow-up that closes the loop
  - All directories currently under ~/.lrh/private/codex/ (verified via MIGRATION_LOG.md) have been consolidated into the new canonical rescue destination using move_exports.py's existing copy-verify-delete flow, with no transcript body text printed during the run
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - experimental/rescue_codex_exports/move_exports.py
  - experimental/rescue_codex_exports/README.md
  - project/design/backlog.md
---

# Point rescue_codex_exports at the canonical durable archive and consolidate stranded exports

## Summary

`experimental/rescue_codex_exports/move_exports.py` still defaults to
`--dest ~/.lrh/private/codex`, a stopgap-era destination that predates
`WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT` landing (PR #579) and choosing
`~/.local/share/lrh/session-archive` as the actual durable archive. Point the
script at the canonical location, correct the two docs that still describe
the old destination as authoritative, and run the one-time consolidation of
everything already stranded there.

## Problem / Context

`experimental/rescue_codex_exports/README.md` documents `move_exports.py`'s
default destination as `~/.lrh/private/codex`, "the location `SKILL.md` Step
2 already documents as the durable alternative" — true at the time that tool
was written (noted 2026-08-21, per `project/design/backlog.md:1490`). Since
then, `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT` landed via PR #579 and
changed the skill's actual default to
`~/.local/share/lrh/session-archive/codex/exports/<YYYY>/<MM>/...`
(`project/memory/decision_log.md:29-31`: "PR #579 flipped the skill's
default output... to a **durable, permanent archive** under
`~/.local/share/lrh/session-archive`"). `move_exports.py`'s own default was
never updated to follow, so it has continued consolidating rescued exports
into the now-orphaned `~/.lrh/private/codex/` — most recently
2026-08-22T17:11:30Z per that directory's own `MIGRATION_LOG.md`, one hour
before a routine `/lrh-codex-export` run correctly landed in the real
archive. Two docs are stale as a direct result: `rescue_codex_exports/
README.md`'s ownership table still calls `~/.lrh/private/codex/` "the
durable archive itself," and `project/design/backlog.md:1503` still says
the governing work item "remains `proposed`" (it is `resolved`).

Note also that `~/.lrh/private/` is not the same thing as the *documented*
`.lrh/private/` local-workspace-mode convention
(`project/memory/decision_log.md:455-464`, 2026-04-22 decision) — that
convention describes a per-workspace `<workspace-root>/.lrh/private/`
directory, not a fixed home-directory path. The rescue script's destination
only resembles that name; it is not an instance of it, and should not be
"fixed" by treating it as one.

The canonical archive's layout is date-partitioned
(`~/.local/share/lrh/session-archive/codex/exports/<YYYY>/<MM>/<export-id>/`,
confirmed by direct inspection), which `move_exports.py`'s current
flat-directory placement logic does not reproduce. Rather than extend the
script to infer year/month from each export's own timestamp and match that
partitioning — a real behavior change with its own risk of misplacing files
— the simpler, lower-risk fix is a dedicated sibling directory under the
same canonical root (e.g. `~/.local/share/lrh/session-archive/codex/
rescued/`) that keeps rescued content under the real archive without
touching the routine capture path's own layout logic.

### Duplication search
- In-repo: No existing fix for the stale default found; this is genuinely
  unaddressed.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this specifically.
- Proposals: None found — this is a mechanical follow-up to an already-
  resolved work item and proposal, not new demand.
- Backlog: `project/design/backlog.md:1490-1509` is the related entry; its
  own text ("Status: Stopgap tooling landed; the work item above remains
  proposed") is now stale and should be corrected by this item.
- Recommendation: Update the backlog entry as part of this item's doc
  corrections rather than opening a new one.

## Scope

- Change `move_exports.py`'s default `--dest` constant.
- Correct `rescue_codex_exports/README.md`'s ownership table.
- Correct `project/design/backlog.md`'s stale status note.
- Run the one-time consolidation of everything currently under
  `~/.lrh/private/codex/` into the new destination.

## Required Changes

1. In `experimental/rescue_codex_exports/move_exports.py`, change the
   default `--dest` from `~/.lrh/private/codex` to a new constant under the
   canonical archive root — a dedicated `rescued/` sibling to `exports/`,
   not the date-partitioned `exports/` tree itself (see Problem/Context).
2. Update `experimental/rescue_codex_exports/README.md`'s ownership table
   and usage examples to reflect the new default and its relationship to
   the routine capture path's own `exports/` tree.
3. Update `project/design/backlog.md`'s `rescue_codex_exports` entry: correct
   the stale "`remains proposed`" claim and add a pointer to this work item
   as the closing follow-up.
4. Run `python3 find_exports.py --source ~/.lrh/private/codex` to confirm
   what's there, then `python3 move_exports.py --source ~/.lrh/private/codex
   --dest <new-canonical-rescued-dir> --apply` to perform the one-time
   consolidation, preserving the script's existing copy → re-hash → delete
   safety flow and appending to that destination's own `MIGRATION_LOG.md`.
5. Verify every directory previously listed in
   `~/.lrh/private/codex/MIGRATION_LOG.md` is present at the new location
   with matching content, then confirm `~/.lrh/private/codex/` is empty of
   export directories (the tool empties sources of everything it moves; do
   not manually delete the directory itself as part of this item).

## Non-Goals

- Do not change `move_exports.py`'s file-placement logic to reproduce the
  routine capture path's `exports/<YYYY>/<MM>/` date partitioning — that's a
  larger, riskier behavior change than this item's scope; a dedicated
  `rescued/` sibling directory is sufficient.
- Do not modify the routine `/lrh-codex-export` capture path itself — it
  already writes correctly; this item only fixes the separate rescue tool.
- Do not attempt to reconcile `~/.lrh/private/` naming with the documented
  per-workspace `.lrh/private/` convention — they are unrelated; see
  Problem/Context.
- Do not print any transcript body text at any point during the
  consolidation run.

## Acceptance Criteria

- `move_exports.py`'s default destination points at the canonical archive
  root, not `~/.lrh/private/codex`.
- Both stale docs are corrected.
- All previously-stranded export directories are verified present at the
  new destination with provenance intact in its `MIGRATION_LOG.md`.
- No transcript body text printed during the run.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `python3 experimental/rescue_codex_exports/find_exports.py --source ~/.lrh/private/codex` (pre- and post-consolidation, to confirm nothing valid remains unmoved)

## Risk Notes

- `move_exports.py` refuses overlapping `--source`/`--dest` pairs
  (`codexexportlib.is_unsafe_pair`) and refuses same-name collisions with
  different content — the consolidation run should be dry-run first
  (default behavior, no `--apply`) and reviewed before applying.
- This item's own required changes are almost entirely outside
  `project/` and the committed skill surface (a script default, two docs),
  so the blast radius of a mistake here is small; the higher-risk step is
  the manual `--apply` run against real personal data, which is why it's
  called out as its own required change rather than assumed automatic.
