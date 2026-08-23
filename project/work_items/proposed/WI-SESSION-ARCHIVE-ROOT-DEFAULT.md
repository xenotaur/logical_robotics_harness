---
resolution: null
blocked_reason: null
blocked: false
id: WI-SESSION-ARCHIVE-ROOT-DEFAULT
title: Confirm the archive-root-location decision and wire Claude export-zip ingestion
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
  - change_existing_archive_root_default
acceptance:
  - lrh sessions sync's --exports-dir gains a resolved default derived from resolve_archive_root(), closing the gap recorded in project/design/backlog.md's "lrh sessions sync has no default /export zip location" entry
  - 'PROP-LRH-SESSION-ARCHIVE-SYNC''s "Archive root location" Open Question is resolved and recorded as a Decision in that proposal: the existing resolve_archive_root()/default_archive_root() default (env var + ~/.local/share/lrh/session-archive) is deliberately confirmed as final, not merely left as the unreviewed "starting point" its own docstring currently calls it'
  - WS-SESSION-ARCHIVE-SYNC's "archive-root-location open question is resolved and recorded" exit criterion is satisfied
  - The existing LRH_SESSION_ARCHIVE_ROOT default (~/.local/share/lrh/session-archive) is left unchanged; Codex archive-root resolution and memory-sync's raw/<slug>/memory/ path both continue to work unmodified
  - Full existing test suite for prompt_workflow_sessions.py and sessions_workflow.py still passes
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/sessions_workflow.py
  - src/lrh/prompt_workflow_sessions.py
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - tests/cli_tests/
---

# Record the archive-root-location decision and wire Claude export-zip ingestion

## Summary

`resolve_archive_root()` already implements a default for the
archive-root-location question `PROP-LRH-SESSION-ARCHIVE-SYNC` still lists
as open — but the function's own docstring explicitly disclaims that this
default is a deliberate answer ("only a starting point"). This item closes
that question for real, by making the deliberate decision to keep the
existing default as final, and separately wires
`lrh sessions sync --exports-dir`'s still-genuinely-missing default from
the same resolver.

## Problem / Context

**Correction from PR #608 review (Codex + Copilot, both independently
confirmed):** an earlier draft of this item claimed no archive-root default
resolution existed and proposed adding one with a new default
(`~/Archives/lrh-sessions/`). That was wrong — `default_archive_root()`
and `resolve_archive_root()` (`src/lrh/prompt_workflow_sessions.py:166-191`)
already implement exactly this: an `LRH_SESSION_ARCHIVE_ROOT` env var,
falling back to `~/.local/share/lrh/session-archive`. Both Codex's export
pipeline (`resolve_codex_archive_root()`, `codex_archive.py:64-72`) and
memory sync (`prompt_workflow_memory.py:693`) already call this same shared
resolver. Proposing a *different* default would have split new data from
the existing archive and directly contradicted this item's own acceptance
criterion that Codex resolution remain unchanged — this item's scope is
corrected below to not touch that resolver's behavior at all.

`PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Questions section
(`project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md:384-390`)
still describes this as deferred, and the shipped code agrees with it —
**correction from a second self-review round on PR #608 (confirmed by
direct re-read):** `default_archive_root()`'s own docstring
(`prompt_workflow_sessions.py:172-178`) states plainly: "The proposal's
archive-root-location open question is not resolved by this default -- it
is only a starting point." An earlier draft of this item's Problem/Context
claimed the code already answered the question — that overstated what the
prior implementer actually committed to. This item's real work is making
the deliberate decision the code's own docstring says hasn't been made
yet, using the reasoning already gathered this session: the default
(`~/.local/share/lrh/session-archive`) is XDG-Base-Directory-compliant,
confirmed not to sit under any Google-Drive-synced tree on this machine,
and already the real, populated archive location in production use — good
enough reasons to confirm it as final rather than revisit it, but that
confirmation has to actually happen and be recorded, not be assumed from
the code's mere existence.

The `--exports-dir` gap is real and independent of the above:
`lrh sessions sync`'s `--exports-dir` flag has no default and export
harvest is skipped entirely when omitted
(`project/design/backlog.md:1154-1174`, noted 2026-08-07):

> "there is no established OS-level or LRH convention for where a user's
> downloaded `session-export-*.zip` files live... A wrong guess (e.g.
> defaulting to `~/Downloads`) risks silently harvesting unrelated files or
> missing the real location on a differently configured machine."

This can be wired to a resolved default now, using the archive root that
already exists, without needing to invent or choose a new one.

### Duplication search
- In-repo: `git grep -n "resolve_archive_root\|default_archive_root\|LRH_SESSION_ARCHIVE_ROOT" -- src/` finds the existing implementation at
  `src/lrh/prompt_workflow_sessions.py:166-191` — the archive-root-default
  half of this item is already implemented; only the `--exports-dir` wiring
  remains.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, scoped only to the `--exports-dir` gap and the
  proposal-text correction.

### Demand search
- Work items: None found requesting this directly.
- Proposals: `PROP-LRH-SESSION-ARCHIVE-SYNC` (proposed) contains the
  now-stale Open Question this item resolves by recording, not re-deciding.
- Backlog: Direct match — `project/design/backlog.md:1154-1174` ("`lrh
  sessions sync` has no default `/export` zip location") — this is the part
  of the item that is genuinely unimplemented.
- Recommendation: Record the archive-root decision in
  `PROP-LRH-SESSION-ARCHIVE-SYNC` and close the matching backlog entry as
  part of this work.

## Scope

- Wire `lrh sessions sync --exports-dir`'s default from the existing
  `resolve_archive_root()`.
- Make the deliberate decision to confirm the existing archive-root default
  as final, and record it as a Decision in `PROP-LRH-SESSION-ARCHIVE-SYNC`,
  replacing its Open Question text — not merely note that code already
  exists, since its own docstring says that alone doesn't answer the
  question.
- Do **not** change `resolve_archive_root()`'s existing default or add a
  new env var — both already exist and are correct as shipped.

## Required Changes

1. In `src/lrh/sessions_workflow.py`, give the `--exports-dir` CLI flag a
   default value derived from `resolve_archive_root()` (e.g. an
   `incoming/` subdirectory under it), rather than requiring it on every
   invocation.
2. Update `PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Questions section: replace
   the "Archive root location — Deferred to a design discussion" text with
   a recorded Decision that deliberately confirms the existing
   `resolve_archive_root()`/`default_archive_root()` default
   (`prompt_workflow_sessions.py:166-191`) as final, citing the env var
   name, default path, and the rationale (XDG-compliant, confirmed
   non-Drive-synced, already the real populated archive). Also update
   `default_archive_root()`'s own docstring, which currently states the
   opposite ("not resolved by this default -- it is only a starting
   point").
3. Close `project/design/backlog.md:1154-1174`'s "`lrh sessions sync` has
   no default `/export` zip location" entry, noting the `--exports-dir`
   fix landed here.

## Non-Goals

- Do not change `resolve_archive_root()`'s existing default location or
  introduce a second env var — the existing implementation is correct and
  already shared by Codex and memory sync.
- Do not build a `lrh meta config`-based configuration surface — that
  surface does not yet support non-boolean values
  (`project/design/backlog.md:1170`).
- Do not migrate the user's already-downloaded zips sitting in a
  Drive-synced staging folder — a separate, deferred operational step.
- Do not add Jules ingestion — tracked separately in
  `WI-SESSION-SYNC-JULES-INGESTION`.

## Acceptance Criteria

- `lrh sessions sync --exports-dir` has a working resolved default derived
  from `resolve_archive_root()`.
- `PROP-LRH-SESSION-ARCHIVE-SYNC`'s Open Question is resolved and recorded
  as a deliberate Decision confirming the existing default, not merely
  observed as already implemented — `default_archive_root()`'s docstring
  is updated to match.
- `WS-SESSION-ARCHIVE-SYNC`'s matching exit criterion is satisfied.
- `resolve_archive_root()`'s existing default and behavior are unchanged;
  Codex archive-root resolution and memory sync are unaffected.
- Full existing test suite passes; `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- Changing `--exports-dir`'s default behavior could start silently
  harvesting files from a directory that previously had to be named
  explicitly; document the new default clearly in the command's help text
  so this isn't a surprise on first run after the change.
- Verify no other call site outside `sessions_workflow.py` assumes
  `--exports-dir` is always explicit before relying on the new default.
