---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-ROOT-DEFAULT
title: Resolve archive-root-location default and wire Claude export-zip ingestion
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
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - An LRH_SESSION_ARCHIVE_ROOT env var is resolved by prompt_workflow_sessions.resolve_archive_root(), falling back to a documented default location that is not under any Google-Drive-synced directory (e.g. ~/Archives/lrh-sessions/) when unset
  - lrh sessions sync's --exports-dir gains a resolved default derived from the same root, closing the gap recorded in project/design/backlog.md's "lrh sessions sync has no default /export zip location" entry
  - PROP-LRH-SESSION-ARCHIVE-SYNC's "Archive root location" Open Question is resolved and recorded as a Decision in that proposal, not left open
  - WS-SESSION-ARCHIVE-SYNC's "archive-root-location open question is resolved and recorded" exit criterion is satisfied
  - Existing Codex archive-root resolution (resolve_codex_archive_root in codex_archive.py) continues to work unchanged, since it already calls the shared resolver being extended here
  - Full existing test suite for prompt_workflow_sessions.py and sessions_workflow.py still passes
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - src/lrh/sessions_workflow.py
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - tests/assist_tests/prompt_workflow_sessions_test.py
---

# Resolve archive-root-location default and wire Claude export-zip ingestion

## Summary

Give `lrh sessions sync` a real, resolved default for where the durable
session archive lives, and use that same default to close the long-open gap
where `--exports-dir` has no default value and Claude `session-export-*.zip`
harvest is silently skipped when it is omitted.

## Problem / Context

`PROP-LRH-SESSION-ARCHIVE-SYNC`'s own Open Questions section
(`project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md:384-390`)
defers this explicitly:

> "**Archive root location.** Deferred to a design discussion. The candidate
> default is a user-level directory such as `~/Archives/lrh-sessions/`, but
> the choice interacts with the user's backup and file-sync arrangements
> (notably whether the archive sits inside or outside a synced folder, given
> past sync-conflict issues) and with the eventual encrypted off-machine
> tier."

This is not hypothetical risk: on this machine, the user's own
session-export-zip staging location
(`~/Downloads/0. Development/Sessions/`) resolves through a symlink to
`~/Workspace/Promptspace/Working/`, which is itself a Google Drive Desktop
sync target (confirmed via a live `.tmp.drivedownload/` artifact under
`~/Workspace/`). This is the exact class of location the LRH and LCATS repos
were deliberately moved *out of*, per
`experimental/rescue_claude_sessions/plan.md:9-11`: "The LRH and LCATS
repositories moved from `~/Workspace/...` to `~/Tempspace/Projects/...` to
keep Git worktree churn out of Google Drive's managed storage." Leaving the
session archive itself in a Drive-synced location risks the same corruption
class that effort exists to clean up.

Downstream of the open archive-root question, `lrh sessions sync`'s
`--exports-dir` flag has no default and export harvest is skipped entirely
when omitted (`project/design/backlog.md:1154-1174`, noted 2026-08-07,
explicitly deferred pending this same resolution):

> "there is no established OS-level or LRH convention for where a user's
> downloaded `session-export-*.zip` files live... A wrong guess (e.g.
> defaulting to `~/Downloads`) risks silently harvesting unrelated files or
> missing the real location on a differently configured machine."

The shared resolver this work extends, `resolve_archive_root()` in
`src/lrh/prompt_workflow_sessions.py`, is already the one piece of
infrastructure Codex's separate export pipeline reuses
(`resolve_codex_archive_root()` in `src/lrh/conversations/codex_archive.py`
calls it directly) — this work strengthens that one shared seam rather than
introducing a new one.

### Duplication search
- In-repo: No existing default-resolution implementation found for either
  the archive root or `--exports-dir`; both are genuinely unset today.
- Sibling repos: None identified.
- External libraries: None identified — this is specific to LRH's own
  reverse-engineered archive layout.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` (proposed) already contains the
  matching Open Question this item resolves.
- Backlog: Direct match — `project/design/backlog.md:1154-1174` ("`lrh
  sessions sync` has no default `/export` zip location").
- Recommendation: Resolve `PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Question as
  part of this work and close the matching backlog entry, rather than
  opening a new proposal.

## Scope

- Add a resolved, documented default for the session archive root, exposed
  via an `LRH_SESSION_ARCHIVE_ROOT` env var with a non-Drive-synced default
  location.
- Wire `lrh sessions sync --exports-dir`'s default from the same resolved
  root.
- Record the resolution as a Decision in `PROP-LRH-SESSION-ARCHIVE-SYNC`.

## Required Changes

1. In `src/lrh/prompt_workflow_sessions.py`, extend `resolve_archive_root()`
   (or the call site that currently requires an explicit root) to check
   `LRH_SESSION_ARCHIVE_ROOT` first, then fall back to a documented default
   constant outside any known cloud-sync directory.
2. In `src/lrh/sessions_workflow.py`, give the `--exports-dir` CLI flag a
   default value derived from the resolved archive root (e.g. an
   `incoming/` subdirectory under it), rather than requiring it on every
   invocation.
3. Update `PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Questions section: replace
   the deferred "Archive root location" question with a recorded Decision
   stating the chosen default and env var name.
4. Confirm `resolve_codex_archive_root()` (`codex_archive.py`) is unaffected
   by the change (it should pass through unchanged since it already calls
   the shared resolver).

## Non-Goals

- Do not build a `lrh meta config`-based configuration surface for this —
  that surface does not yet support non-boolean values
  (`project/design/backlog.md:1170`); env var only for now.
- Do not migrate the user's already-downloaded zips sitting in the
  Drive-synced staging folder — that is a one-time operational step,
  deferred pending a separate decision on whether/when to run it.
- Do not add Jules ingestion — tracked separately in
  `WI-SESSION-SYNC-JULES-INGESTION`, which depends on this item for the
  shared root.

## Acceptance Criteria

- `LRH_SESSION_ARCHIVE_ROOT` is resolved with a documented, non-Drive-synced
  default when unset.
- `lrh sessions sync --exports-dir` has a working resolved default.
- `PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Question is resolved and recorded.
- `WS-SESSION-ARCHIVE-SYNC`'s matching exit criterion is satisfied.
- Existing Codex archive-root resolution is unaffected.
- Full existing test suite passes; `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- The chosen default path must not itself accidentally resolve into a
  Drive-synced or iCloud-synced directory on this or any other contributor's
  machine — worth a one-line runtime check or comment warning against
  redefining it into a synced folder.
- Changing `--exports-dir`'s default behavior could start silently
  harvesting files from a directory that previously had to be named
  explicitly; document the new default clearly in the command's help text so
  this isn't a surprise on first run after the change.
