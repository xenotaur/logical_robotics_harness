---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-LAND-WORKTREE-CAPTURE-FIX
title: Fix worktree-unsafe .git/ capture path and stale SKILL.md snippet in /lrh-land
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - "The Main-worktree-lock rule's tmp_branch_parent capture works correctly when .git is a worktree gitdir-pointer file, not just a normal repo directory"
  - "SKILL.md Step 7's illustrative bash snippet either matches land-workflow.md's documented capture/cleanup procedure, or explicitly defers to it instead of standing as an incomplete literal example"
  - "Both fixes present, correct, and consistent across src/, .claude/, .agents/, .gemini/ -- byte-identical for .claude/ (raw cp mirror), and for the changed procedural content specifically in .agents/.gemini/ (their SKILL.md frontmatter is installer-normalized and never byte-identical to src/, per the existing, out-of-scope divergence this WI's Non-Goals section already excludes); verified via lrh skills status --scope project --target codex|antigravity --source current-repo reporting up to date, not via a whole-file diff"
---

## Summary

PR #628 (`/lrh-land` friction-doc fixes) added a `tmp_branch_parent` capture
step writing to `.git/lrh-tmp-branch-parent-<slug>`. Discovered live during
that same PR's own closeout: this fails in a worktree checkout, where
`.git` is a file (a gitdir pointer), not a directory — reproduced directly
(`bash: .git/lrh-tmp-branch-parent-...: Not a directory`). Separately,
`SKILL.md`'s Step 7 illustrative bash snippet still shows the old
main-worktree-lock workaround without the capture or cleanup steps
`land-workflow.md`'s Main-worktree-lock rule now documents, so an agent
that copy-pastes the `SKILL.md` snippet literally, rather than deriving the
full procedure from the loaded `land-workflow.md` prose, would silently
skip the capture step and lose the non-fast-forward troubleshooting
recovery path entirely.

## Problem / Context

`/lrh-land`'s whole main-worktree-lock mechanism exists specifically to
handle the multi-worktree case — this repository's own primary mode of
operation in practice. A capture path that breaks inside a worktree
directly contradicts that: the fix has to work precisely in the case it
exists to handle.

**Duplication search:** `git grep -nE "git-dir|lrh-tmp-branch-parent|worktree.*capture" -- project/work_items project/design/backlog.md`
(tracked-only, worktree-safe — not the filesystem `grep -rl` this repo's
own convention flags as non-reproducible for repo-wide survey evidence)
returns matches only within this work item's own file, self-referential
from its own title and body text. No prior, independent work item or
backlog entry covers this.

**Demand search:** No existing work item, proposal, or backlog entry
requests this fix. Freshly discovered during PR #628's own closeout
(2026-08-24), not previously reported.

## Scope

Two small, contained doc-only fixes to the `/lrh-land` skill's own
worktree-workaround procedure, mirrored across all four skill-install
targets.

## Required Changes

- `src/lrh/skills/lrh-land/references/land-workflow.md`: replace the
  hardcoded `.git/lrh-tmp-branch-parent-<slug>` path with a path resolved
  via `$(git rev-parse --git-dir)`, which correctly returns the real git
  directory whether `.git` is an ordinary directory or a worktree's
  gitdir-pointer file.
- `src/lrh/skills/lrh-land/SKILL.md` Step 7 ("Switch to main before
  closeout"): update the illustrative bash snippet to match the capture/
  cleanup procedure `land-workflow.md` documents, or reword it to
  explicitly defer to `land-workflow.md`'s Main-worktree-lock rule rather
  than standing as a literal, copy-pasteable but incomplete example.
- Mirror both changes to `.claude/skills/lrh-land/`, `.agents/skills/lrh-land/`
  (via the proper skill installer, not raw `cp` — see PR #628's own
  review findings on this exact point), `.gemini/plugins/lrh/skills/lrh-land/`
  (same).

## Non-Goals

- No other `/lrh-land` behavior change.
- No new troubleshooting rows beyond fixing the two identified gaps.
- Does not address the pre-existing, unrelated `.agents`/`.gemini`
  frontmatter cosmetic-style divergence (block-style vs. flow-style YAML)
  — established as out-of-scope, installer-driven, and harmless in prior
  sessions.

## Acceptance Criteria

- The `tmp_branch_parent` capture works correctly when run inside a git
  worktree checkout (`.git` is a file, not a directory) — verified by
  direct reproduction, not just code review.
- `SKILL.md` Step 7's snippet no longer omits the capture/cleanup steps
  `land-workflow.md` documents, either by matching them or by explicitly
  deferring to that file.
- Both fixes present and correct in `src/`, `.claude/` (byte-identical
  `diff`), and `.agents/`/`.gemini/` (via `lrh skills status --scope
  project --target codex|antigravity --source current-repo` reporting up
  to date — not a whole-file `diff`, since installer-normalized frontmatter
  in those two targets is never byte-identical to `src/`, per this WI's
  own Non-Goals).
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- Manual repro: run the capture command in a worktree checkout and confirm
  it succeeds (this work item's own implementation session runs inside a
  worktree, so this is directly testable in place)
- `diff -r` for `.claude/`; `lrh skills status --scope project --target
  codex|antigravity --source current-repo` for `.agents/`/`.gemini/`

## Risk Notes

Low risk — doc-only change to an already-narrow procedural section, no
code or behavior change outside `/lrh-land`'s own worktree-workaround
text.
