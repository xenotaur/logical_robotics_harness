---
resolution: null
blocked_reason: null
blocked: false
id: WI-PROJECT-SLUG-SYMLINK-RESOLUTION
title: Fix project_slug_for_path to stop resolving symlinks
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - project_slug_for_path() no longer calls pathlib.Path.resolve() or any other symlink-following normalization
  - A new regression test proves a path through a symlinked directory slugs to the symlink's own literal path, distinct from the slug of the resolved target
  - All 5 existing call sites (prompt_workflow_sessions.py:605; prompt_workflow_memory.py:65,687,826,984) reviewed and confirmed unaffected by the change, or fixed if one depended on the old symlink-resolving behavior
  - Full existing test suite for prompt_workflow_sessions.py and prompt_workflow_memory.py still passes
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_sessions.py
  - tests/assist_tests/prompt_workflow_sessions_test.py
---

## Summary

Fix `project_slug_for_path()` (`src/lrh/prompt_workflow_sessions.py:565-582`)
so it no longer resolves symlinks when computing a Claude Code
`~/.claude/projects/<slug>/` bucket name, matching Claude Code's real,
observed bucket-naming behavior.

## Problem / Context

`project_slug_for_path()` calls `.expanduser().resolve()` before slugifying
a path. `.resolve()` follows symlinks, but Claude Code's own bucket-naming
does not — it slugifies the literal, as-given working-directory path
string. This was flagged by both Copilot and Codex review bots on PR #599
(a documentation-only PR touching
`experimental/rescue_claude_sessions/tempspace-migration-status.md`), and
confirmed empirically against real `~/.claude/projects/` state on this
machine: this repository moved from a now-symlinked
`~/Workspace/LogicalRoboticsHarness/logical_robotics_harness` path to the
real `~/Tempspace/Projects/LogicalRoboticsHarness/logical_robotics_harness`
path, and two separate, independently-populated buckets exist under
`~/.claude/projects/` today — one keyed on the old symlinked path literally,
one keyed on the new real path — which is exactly why
`experimental/rescue_claude_sessions/` exists as a reconciliation tool.
Feeding `project_slug_for_path()` the old symlinked path incorrectly returns
the *new* bucket's slug, not the old bucket's real, distinct slug. Any
`lrh sessions`/`lrh memory` command that resolves a path argument through
this function (call sites: `prompt_workflow_sessions.py:605`;
`prompt_workflow_memory.py:65,687,826,984`) will silently target the wrong
bucket when given an old, symlinked path — e.g.
`lrh memory transfer --from <old-symlinked-path>` would silently operate on
the new bucket instead of the one actually holding the historical content.

Git history (`git log -p --follow` on `prompt_workflow_sessions.py`) shows
`.resolve()` was present in this function's original implementation, added
purely to get an absolute path for the character-substitution regex — the
only subsequent change (commit `70778f8e`) was about which characters to
replace (`.` vs `_`), never about symlink-following. The symlink-resolving
side effect was never deliberately chosen against Claude Code's real
behavior; it was never examined.

`experimental/rescue_claude_sessions/bucketlib.py:53-55`'s `slugify()`
already implements the correct approach in this same repo: plain regex
character substitution on the given string, with no `.resolve()` call, and
it matches observed real Claude Code behavior.

### Duplication search
- In-repo: No existing fix found. `WI-SESSION-ARCHIVE-SYNC-RECONCILER`
  (resolved) is the work item that originally introduced
  `project_slug_for_path()`, but did not examine symlink behavior.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found (`grep -r project_slug_for_path project/work_items/`
  found no prior fix request).
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Fix the symlink-following behavior in `project_slug_for_path()`
- Add regression test coverage for the symlink case
- Audit the 5 existing call sites for reliance on the old behavior

## Required Changes

1. In `src/lrh/prompt_workflow_sessions.py`, replace
   `pathlib.Path(path).expanduser().resolve()` with symlink-preserving
   absolute-path normalization (e.g. `os.path.abspath` after `expanduser`,
   or a pathlib equivalent) that still collapses `..`/`.` segments and makes
   relative paths absolute, but does not follow symlinks.
2. Update the function's docstring to state the symlink contract explicitly
   — it currently only describes the character-substitution behavior and
   says nothing about symlink handling.
3. Review each of the 5 call sites
   (`prompt_workflow_sessions.py:605`;
   `prompt_workflow_memory.py:65,687,826,984`) to confirm none relies on or
   accidentally compensates for the old symlink-resolving behavior.
4. Add a regression test in `tests/assist_tests/prompt_workflow_sessions_test.py`
   proving that a path through a symlinked directory slugs to the symlink's
   own literal path, not the resolved target's path.

## Non-Goals

- Do not change `experimental/rescue_claude_sessions/bucketlib.py`'s
  `slugify()` — it already has the correct behavior and is out of scope.
- Do not attempt to reconcile the two existing divergent
  `~/.claude/projects/` buckets on this machine — that is a local
  filesystem/session-archive concern, not a code change.
- Do not add symlink-resolution as a configurable option; the goal is to
  match Claude Code's actual behavior, not to support both behaviors.

## Acceptance Criteria

- `project_slug_for_path()` no longer calls `pathlib.Path.resolve()` or any
  other symlink-following normalization.
- A new test proves a symlinked-path input slugs to its own literal
  spelling, distinct from the slug of the resolved target.
- All 5 existing call sites reviewed and confirmed unaffected (or fixed if
  one depended on the old behavior), documented in the execution record.
- Full existing test suite for `prompt_workflow_sessions.py` and
  `prompt_workflow_memory.py` still passes.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- Removing `.resolve()` also removes `..`/`.` collapsing if not replaced
  with an equivalent normalization step — the fix must explicitly preserve
  that behavior via `os.path.abspath` (or equivalent), not just delete the
  call.
- A call site may be passing a relative path expecting `.resolve()` to
  anchor it against the current working directory; `os.path.abspath` has
  the same anchoring behavior, so this should carry over, but each call
  site should be checked rather than assumed.
