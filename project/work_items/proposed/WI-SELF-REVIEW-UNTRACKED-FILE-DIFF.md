---
resolution: null
blocked_reason: null
blocked: false
id: WI-SELF-REVIEW-UNTRACKED-FILE-DIFF
title: Fix lrh-self-review diff-mode missing brand-new untracked files
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
  - merge_pr
acceptance:
  - src/lrh/skills/lrh-self-review/SKILL.md Step 1's diff-mode diff-building instruction stages new files with intent-to-add before running git diff main, so untracked new files appear in the diff
  - A working tree containing only new untracked files (no modified tracked files) produces a non-empty diff under the documented procedure, instead of a false "nothing to review" exit
  - The existing correct rationale for using git diff main (not the three-dot main...HEAD form) is preserved unchanged
  - .claude/skills/lrh-self-review/SKILL.md is byte-for-byte identical to src/lrh/skills/lrh-self-review/SKILL.md
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-self-review/SKILL.md
  - .claude/skills/lrh-self-review/SKILL.md
---

## Summary

Fix `/lrh-self-review` Step 1's diff-mode diff-building command
(`git diff main`), which never includes untracked files regardless of the
dot form used. At `/lrh-implement` Step 7.5's own call site — before Step 8
commits anything — if Step 6's implementation only created brand-new files
with no modifications to any existing tracked file, `git diff main` is
empty even though real new content exists, and the skill reports a false
"nothing to review" exit, silently skipping review of that content. The fix
stages new files with intent-to-add (`git add -N`) immediately before
computing the diff, so untracked new files are included without their
content actually being staged for commit.

## Problem / Context

Flagged during Taurcode PR #82 triage — a mechanical `lrh skills install
--local --force` resync of this project's own skill package into the
Taurcode repo. Three bots flagged real bugs in the *content* of the synced
skills (this project's canonical source), not anything the resync PR
introduced. Full triage detail is in the Taurcode repo at
`project/executions/AD_HOC/2026_08_20_01_06_17_RESYNC_LRH_SKILLS_REVIEW.md`.
This work item addresses one of the three findings; the other two
(`lrh-closeout` session-alias backend scoping, `lrh-land` tmp-branch
cleanup deleting the checked-out branch) are tracked separately
(`WI-CLOSEOUT-SESSION-ALIAS-BACKEND-SCOPE`,
`WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT`).

Read directly against this repo's current source
(`src/lrh/skills/lrh-self-review/SKILL.md:98-116`): diff-mode's documented
procedure is

```bash
git rev-parse HEAD
git diff main
```

with the accompanying rationale correctly explaining why the two-dot form
(`git diff main`, working tree vs. `main`'s tip) is used instead of the
three-dot `git diff main...HEAD` form — at `/lrh-implement` Step 7.5's call
site, Step 6's changes are still uncommitted, so a committed-only diff
would be empty. That rationale is sound and this work item does not change
it. What it misses: `git diff` — in *any* dot form — only ever reports
changes to files Git is already tracking (modified or staged); a file that
exists on disk but has never been `git add`-ed does not appear in `git
diff` output at all, only in `git status`'s "Untracked files" section. So
if Step 6 of `/lrh-implement` created only new files (e.g. a new skill's
`SKILL.md` and `references/*.md`, with no edits to any existing tracked
file), `git diff main` returns empty, Step 1 of `/lrh-self-review` hits its
own "If the diff is empty, stop and report — nothing to review" branch, and
the entire new-file content silently skips review. This is not a rare
edge case for this skill's own callers — several of this project's own
work items add brand-new skill directories or reference docs with no
modification to any existing file.

**Prior art check:**
- *Duplication search:* grepped `project/work_items/` and
  `project/design/backlog.md` for "self-review" and "untracked" — no
  existing work item or backlog entry addresses this diff-mode gap. The
  adopted proposal `PROP-LRH-SELF-REVIEW` documents the two-dot-vs-three-dot
  diff-command choice but does not address untracked files.
- *Demand search:* grepped `project/workstreams/` and `project/design/` for
  the same terms — no existing request found.

## Scope

- `src/lrh/skills/lrh-self-review/SKILL.md` Step 1, diff-mode command
  block: add an intent-to-add step before `git diff main`.
- Mirror the change to `.claude/skills/lrh-self-review/SKILL.md`.

## Non-Goals

- Does not change the two-dot-vs-three-dot diff-form rationale — that
  reasoning is correct and unrelated to this bug.
- Does not change PR-mode's diff procedure (`gh pr view`), which is
  unaffected — a PR's `HEAD` diff already reflects committed content.
- Does not change how `/lrh-implement` Step 6 stages or commits files
  outside of this self-review call site.

## Required Changes

1. Edit `src/lrh/skills/lrh-self-review/SKILL.md` Step 1's diff-mode block:
   before `git diff main`, add `git add -N .` (or an equivalent targeted
   intent-to-add invocation) so untracked new files are included in the
   diff without staging their content for commit. Add a short note
   explaining why this step is needed (untracked files are invisible to
   `git diff` in any form) so a cold agent executing this skill
   understands the purpose, not just the command.
2. Mirror the edited file to `.claude/skills/lrh-self-review/SKILL.md`.

## Acceptance Criteria

- SKILL.md Step 1's diff-mode procedure stages new files with
  intent-to-add before computing the diff.
- A working tree with only new untracked files (no tracked-file
  modifications) produces a non-empty `git diff main` result under the
  documented procedure.
- The existing two-dot-vs-three-dot rationale is preserved, not rewritten.
- `.claude/skills/lrh-self-review/SKILL.md` mirrors
  `src/lrh/skills/lrh-self-review/SKILL.md` byte-for-byte.
- `lrh validate` reports 0 errors.

## Validation

- lrh validate
- diff -q src/lrh/skills/lrh-self-review/SKILL.md .claude/skills/lrh-self-review/SKILL.md
- Manual repro: in a scratch worktree, create a new untracked file only, run `git add -N .` then `git diff main`, confirm the new file's content appears in the diff

## Risk Notes

Low risk — documentation/instruction-wording fix to an agent-facing skill
file plus a benign `git add -N` (intent-to-add only, does not stage file
content or affect what a subsequent commit would include). The main risk
is an agent mistaking intent-to-add for a real `git add` and accidentally
committing new files earlier than intended; mitigate by stating explicitly
in the added note that intent-to-add does not stage content.
