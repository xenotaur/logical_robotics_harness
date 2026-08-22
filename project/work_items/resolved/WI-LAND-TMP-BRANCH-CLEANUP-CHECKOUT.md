---
resolution: "Implemented and merged in PR #580 (creation, commit 4f4244ec) and PR #581 (implementation, commit 3e0a5429)."
blocked_reason: null
blocked: false
id: WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT
title: Fix lrh-land main-worktree-lock workaround deleting the checked-out tmp branch
type: operation
status: resolved
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
  - merge_pr
acceptance:
  - src/lrh/skills/lrh-land/SKILL.md Step 7's main-worktree-lock workaround checks out a branch other than tmp-<slug> (the original PR branch, or a detached HEAD) before running git branch -D tmp-<slug>
  - src/lrh/skills/lrh-land/references/land-workflow.md's Main-worktree-lock rule row reflects the same corrected sequence
  - The push step in both files uses an explicit remote (git push origin tmp-<slug>:main), not the bare tmp-<slug>:main form, which git parses as a repository argument rather than a refspec
  - The corrected sequence, run end-to-end in a disposable scratch repository (not this project's own repo/branches), completes without error, including the final git branch -D on that scratch repo's own throwaway tmp-<slug> branch
  - .claude/skills/lrh-land/SKILL.md and .claude/skills/lrh-land/references/land-workflow.md are byte-for-byte identical to their src/lrh/skills/lrh-land counterparts
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-land/SKILL.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .agents/skills/lrh-land/SKILL.md
  - .agents/skills/lrh-land/references/land-workflow.md
  - .gemini/plugins/lrh/skills/lrh-land/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-land/references/land-workflow.md
---

## Summary

Fix `/lrh-land` Step 7's main-worktree-lock workaround
(`src/lrh/skills/lrh-land/SKILL.md:428-434`, mirrored in
`references/land-workflow.md`'s rule table), which runs
`git checkout -b tmp-<slug> origin/main`, performs the closeout work, pushes
`tmp-<slug>:main`, then runs `git branch -D tmp-<slug>` — all while `HEAD`
is still on `tmp-<slug>`. Git refuses to delete the currently checked-out
branch even with `-D`, so this sequence always errors immediately after the
closeout commit has already landed on `main`, leaving the session stuck on
a branch it cannot clean up and blocking the rest of the landing workflow.
The fix checks out a different branch (the original PR branch, or a
detached `HEAD`) before the delete.

## Problem / Context

Flagged during Taurcode PR #82 triage — a mechanical `lrh skills install
--local --force` resync of this project's own skill package into the
Taurcode repo. Three bots flagged real bugs in the *content* of the synced
skills (this project's canonical source), not anything the resync PR
introduced. Full triage detail is in the Taurcode repo at
`project/executions/AD_HOC/2026_08_20_01_06_17_RESYNC_LRH_SKILLS_REVIEW.md`.
This work item addresses one of the three findings; the other two
(`lrh-closeout` session-alias backend scoping, `lrh-self-review` diff-mode
missing untracked files) are tracked separately
(`WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE`,
`WI-SELF-REVIEW-UNTRACKED-FILE-DIFF`).

Read directly against this repo's current source
(`src/lrh/skills/lrh-land/SKILL.md:420-437`):

```bash
git fetch
git checkout -b tmp-<slug> origin/main
# ... execute the closeout edits and commits on this branch ...
git push tmp-<slug>:main
git branch -D tmp-<slug>
```

After `git checkout -b tmp-<slug> origin/main`, the session's `HEAD` points
at `tmp-<slug>` for the remainder of the sequence — the comment line does
not check out anything else, and neither does `git push tmp-<slug>:main`
(a push does not change the local `HEAD`). `git branch -D <branch>`
refuses to delete the branch `HEAD` currently points to, regardless of the
`-D` force flag — this is a hard Git invariant, not something `-D`
overrides (only `checkout`/`switch` to elsewhere, or a detached `HEAD`,
makes the branch deletable). So the very last line of this documented
sequence always fails, and it fails *after* `git push tmp-<slug>:main` has
already landed the closeout commit(s) on `main` — i.e., the important
state-changing work is done, but the workaround leaves the session on
`tmp-<slug>` with no clean way to proceed to whatever step comes after
Step 7, and repeated invocations would accumulate stray `tmp-<slug>`
branches locally since the delete never succeeds.

This directly matches the corresponding row in
`src/lrh/skills/lrh-land/references/land-workflow.md`'s "Five Glue-Logic
Rules" table (`Main-worktree-lock`), which states the same broken
sequence: "`git fetch → checkout -b tmp-<slug> origin/main → apply changes
→ push tmp-<slug>:main → delete tmp-<slug>`" — no checkout-away step
before the delete.

**Second, adjacent bug found while validating the fix:** the `git push
tmp-<slug>:main` line itself (already present before this WI; not
introduced by it) is also broken as documented. Verified directly: a bare
`<ref>:<ref>` argument with no space, with no remote named `tmp-<slug>`
configured, is parsed by `git push` as the *repository* argument, not a
refspec — the command does not do what the surrounding prose describes.
It needs an explicit remote: `git push origin tmp-<slug>:main`. This sits
directly upstream of the checkout-away fix (the sequence must actually
reach the delete step for that fix to matter), and this WI's own
acceptance criteria claim the corrected sequence "runs as documented"
successfully — which isn't true without also fixing this line. Folded
into this WI's scope rather than filed separately, since it's the same
code block and the same root cause category (an under-tested documented
git sequence).

**Prior art check:**
- *Duplication search:* grepped `project/work_items/` and
  `project/design/backlog.md` for "tmp-" and "main-worktree-lock" — no
  existing work item or backlog entry addresses this branch-delete bug.
- *Demand search:* grepped `project/workstreams/` and `project/design/`
  for the same terms — no existing request found. `WS-SKILLS-LRH-LAND` (the
  originating workstream for `/lrh-land`) is already `resolved`, so this is
  filed standalone per this project's convention for post-resolution
  fixes to a resolved workstream's skill.

## Scope

- `src/lrh/skills/lrh-land/SKILL.md` Step 7: add a checkout-away step
  before `git branch -D tmp-<slug>`; fix the push step to name an explicit
  remote.
- `src/lrh/skills/lrh-land/references/land-workflow.md`: update the
  `Main-worktree-lock` rule row to reflect the corrected sequence.
- Mirror both changes to every checked-in skill target this repo renders
  to for the target-aware installer (`.claude/skills/lrh-land/`,
  `.agents/skills/lrh-land/`, `.gemini/plugins/lrh/skills/lrh-land/`) via
  `lrh skills install --local --target all --source current-repo --force`
  — these are rendered outputs with per-target frontmatter differences,
  not byte-identical copies, so a raw `cp` to the non-Claude targets would
  be wrong.

## Non-Goals

- Does not change when the main-worktree-lock workaround is triggered (the
  "all worktrees have `main` checked out" condition) — only the cleanup
  step at the end of the workaround itself, plus the adjacent push-remote
  fix described above.
- Does not address worktree management more broadly — scoped strictly to
  this one documented command sequence.

## Required Changes

1. Edit `src/lrh/skills/lrh-land/SKILL.md` Step 7's workaround code block:
   change `git push tmp-<slug>:main` to `git push origin tmp-<slug>:main`;
   insert a checkout step after it and before `git branch -D tmp-<slug>`
   that returns `HEAD` to the original PR branch this Step 7 session
   started from (or `git checkout --detach` if that branch name isn't
   available in scope at this point). Add short notes explaining both
   fixes (bare `<ref>:<ref>` is parsed as a repository argument without an
   explicit remote; Git refuses to delete the currently checked-out
   branch).
2. Edit `src/lrh/skills/lrh-land/references/land-workflow.md`'s
   `Main-worktree-lock` rule row to include both fixes in its documented
   sequence.
3. Render both edited files to every checked-in skill target via
   `lrh skills install --local --target all --source current-repo
   --force`, then verify with `lrh skills check --target claude --local
   --source current-repo` and `lrh skills status --target {codex,
   antigravity} --local --source current-repo`.

## Acceptance Criteria

- Step 7's workaround sequence checks out a branch other than `tmp-<slug>`
  (or detaches `HEAD`) before `git branch -D tmp-<slug>`.
- The push step in both files uses `git push origin tmp-<slug>:main`, not
  the bare `tmp-<slug>:main` form.
- `references/land-workflow.md`'s rule table row reflects the same
  corrected sequence, not the old one.
- Running the corrected sequence end-to-end in a disposable scratch
  repository (not this project's own repo/branches) completes without
  error, including the final `git branch -D` on that scratch repo's own
  throwaway branch.
- `.claude/skills/lrh-land/`, `.agents/skills/lrh-land/`, and
  `.gemini/plugins/lrh/skills/lrh-land/` all report up to date against
  `src/lrh/skills/lrh-land/` via `lrh skills check`/`status`.
- `lrh validate` reports 0 errors.

## Validation

- lrh validate
- lrh skills check --target claude --local --source current-repo
- lrh skills status --target codex --local --source current-repo
- lrh skills status --target antigravity --local --source current-repo
- Manual repro: in a disposable scratch repository, run the corrected sequence end-to-end and confirm git push origin tmp-<slug>:main and the final git branch -D both succeed

## Risk Notes

Low risk — documentation/instruction-wording fix to an agent-facing skill
file plus reference doc; no code or CLI behavior changes. The main risk is
naming a checkout target that isn't actually knowable at that point in the
skill's control flow (e.g. if the original PR branch name wasn't retained
in a variable/context by the agent executing the skill); mitigate by
offering `git checkout --detach` as the always-safe fallback alongside the
preferred "return to the original PR branch" option.

`delete_branch` is intentionally absent from `forbidden_actions`: the only
branch delete this WI's validation performs is on a disposable scratch
repository created solely for reproduction, never on this project's own
repository or branches. Listing it would have blocked an implementing
agent from running the WI's own required manual-repro validation step.

Multi-target rendering (`.claude/`, `.agents/`, `.gemini/`) via
`lrh skills install` is a slightly wider surface than a single `cp`, but
is the correct, existing mechanism for this repo (verified: `.agents/` and
`.gemini/` outputs use different YAML frontmatter formatting per target,
so they cannot be produced by copying `src/lrh/skills/` bytes directly) —
using it is lower risk than a manual copy that would silently desync from
what those targets actually need.
