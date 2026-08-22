---
resolution: null
blocked_reason: null
blocked: false
id: WI-PROJECT-SLUG-SYMLINK-RESOLUTION
title: Fix project_slug_for_path to match Claude Code's real bucket naming (symlinks and underscores)
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
related_design:
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
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
  - project_slug_for_path()'s character-substitution regex replaces underscores in addition to `/` and `.`, matching Claude Code's real hyphenated bucket naming
  - A new regression test proves a path through a symlinked directory slugs to the symlink's own literal path, distinct from the slug of the resolved target
  - A new regression test proves a path containing an underscore (e.g. this repo's own `logical_robotics_harness` directory name) slugs with the underscore replaced by a hyphen, matching the real observed `~/.claude/projects/` bucket name
  - All 5 existing call sites (prompt_workflow_sessions.py:605; prompt_workflow_memory.py:65,687,826,984) reviewed and confirmed unaffected by both changes, or fixed if one depended on the old behavior
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
so it matches Claude Code's real, observed
`~/.claude/projects/<slug>/` bucket-naming behavior in two confirmed ways:
it must stop resolving symlinks, and its character-substitution regex must
also replace underscores.

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

A second, independent discrepancy in the same helper was found and verified
during this WI's own review cycle: `project_slug_for_path()`'s regex
(`_PROJECT_SLUG_UNSAFE = re.compile(r"[/.]")`,
`src/lrh/prompt_workflow_sessions.py:562`) replaces only `/` and `.` —
deliberately, per its own docstring, to avoid breaking `.claude/worktrees/`
resolution — but does **not** replace `_`. Claude Code's own real bucket
for this exact repo is
`-Users-centaur-Tempspace-Projects-LogicalRoboticsHarness-logical-robotics-harness`
— hyphens throughout — even though the real directory name on disk is
literally `logical_robotics_harness` (underscore). Calling
`project_slug_for_path('.')` from inside this repo returns
`...-logical_robotics_harness...` (underscore preserved): a different,
wrong, orphaned slug from the real one. This was confirmed by direct
accident in a separate session: `lrh memory write --project-root .`
(which resolves its target bucket via this same helper) silently created a
third, never-to-be-read bucket
(`-Users-centaur-Tempspace-Projects-LogicalRoboticsHarness-logical_robotics_harness--claude-worktrees-git-access-check-b75cd6`)
instead of writing into the real, established canonical bucket. Both
discrepancies share the same root cause — `project_slug_for_path()` was
never verified against Claude Code's actual bucket-naming behavior — and
touch the same function and the same regression-test file, so they are
scoped as one combined fix rather than two dependent work items.

`experimental/rescue_claude_sessions/bucketlib.py:53-55`'s `slugify()`
already implements an approach that avoids both issues in this same repo:
plain `re.sub(r"[^A-Za-z0-9]", "-", str(path))`, with no `.resolve()` call
and replacing underscore too. Note this sibling implementation itself
hasn't been directly verified against Claude Code's real underscore-
normalizing behavior either — only the *evidence* (the real hyphenated
bucket) is confirmed, not that `bucketlib.slugify` is necessarily the exact
right approach to copy; character-class choice should be verified against
observed reality during implementation, not assumed from this one sibling.

### Duplication search
- In-repo: No existing fix found. `WI-SESSION-ARCHIVE-SYNC-RECONCILER`
  (resolved) is the work item that originally introduced
  `project_slug_for_path()`, but did not examine symlink or underscore
  behavior.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found (`git grep -n project_slug_for_path -- project/work_items/`
  found no prior fix request; the only hits are this WI itself and
  `WI-LRH-MEMORY-WRITE-SIDE`'s incidental mention of reusing the helper).
- Proposals: Found context, not a fix request —
  `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
  Decision 8 (line 120) already documents that `project_slug_for_path()`
  calls `.resolve()` and therefore "follows symlinks anyway," in the course
  of disqualifying a symlink-based memory-propagation design. That proposal
  treats the symlink behavior as a known constraint to design around, not
  as a bug to fix — it does not request or implement the fix this WI scopes.
  No proposal requests a fix to the underscore-preservation behavior.
- Backlog: No matching entries (`git grep -n project_slug_for_path --
  project/design/backlog.md` returns nothing).
- Recommendation: Proceed. Cite
  `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
  Decision 8 as related context in Problem/Context (done above) since it
  independently corroborates the symlink-following behavior from a design
  discussion that predates this WI, but it does not satisfy or duplicate
  this WI's scope.

## Scope

- Fix the symlink-following behavior in `project_slug_for_path()`
- Fix the underscore-preservation behavior in `project_slug_for_path()`'s
  character-substitution regex
- Add regression test coverage for both the symlink case and the underscore
  case
- Audit the 5 existing call sites for reliance on either old behavior

## Required Changes

1. In `src/lrh/prompt_workflow_sessions.py`, replace
   `pathlib.Path(path).expanduser().resolve()` with symlink-preserving
   absolute-path normalization (e.g. `os.path.abspath` after `expanduser`,
   or a pathlib equivalent) that still collapses `..`/`.` segments and makes
   relative paths absolute, but does not follow symlinks.
2. In the same file, update `_PROJECT_SLUG_UNSAFE` (or its substitution
   logic) so `_` is also replaced, matching Claude Code's real hyphenated
   bucket naming — verify the exact right character class against observed
   real bucket names (not just copied from `bucketlib.slugify`) before
   finalizing, per the note in Problem/Context above.
3. Update the function's docstring to state both the symlink and underscore
   contracts explicitly — it currently describes neither correctly.
4. Review each of the 5 call sites
   (`prompt_workflow_sessions.py:605`;
   `prompt_workflow_memory.py:65,687,826,984`) to confirm none relies on or
   accidentally compensates for either old behavior.
5. Add regression tests in `tests/assist_tests/prompt_workflow_sessions_test.py`
   proving (a) a path through a symlinked directory slugs to the symlink's
   own literal path, not the resolved target's path, and (b) a path
   containing an underscore slugs with the underscore replaced, matching a
   real observed bucket name.

## Non-Goals

- Do not change `experimental/rescue_claude_sessions/bucketlib.py`'s
  `slugify()` — it is a reference point, not necessarily the exact
  character-class implementation to copy; out of scope regardless.
- Do not attempt to reconcile the divergent `~/.claude/projects/` buckets
  already on disk (symlink-derived or underscore-derived) — that is a local
  filesystem/session-archive concern, not a code change.
- Do not add symlink-resolution or underscore-preservation as configurable
  options; the goal is to match Claude Code's actual behavior, not to
  support both behaviors.

## Acceptance Criteria

- `project_slug_for_path()` no longer calls `pathlib.Path.resolve()` or any
  other symlink-following normalization.
- `project_slug_for_path()`'s character substitution also replaces
  underscores.
- A new test proves a symlinked-path input slugs to its own literal
  spelling, distinct from the slug of the resolved target.
- A new test proves an underscore-containing path slugs with the
  underscore replaced by a hyphen.
- All 5 existing call sites reviewed and confirmed unaffected (or fixed if
  one depended on either old behavior), documented in the execution record.
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
- Widening the character substitution to replace `_` changes the slug for
  every path containing an underscore anywhere in its segments (directory
  names, not just this repo's own). Any code or test that hardcodes an
  underscore-preserving slug as an expected value will need updating —
  audit `git grep -n "logical_robotics_harness" -- tests/` and similar for
  slug-shaped string literals, not just the 5 call sites already listed.
