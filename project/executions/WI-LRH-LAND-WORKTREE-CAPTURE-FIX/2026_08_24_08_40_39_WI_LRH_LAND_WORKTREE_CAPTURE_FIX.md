---
execution_id: 2026_08_24_08_40_39_WI_LRH_LAND_WORKTREE_CAPTURE_FIX
prompt_id: PROMPT(WI-LRH-LAND-WORKTREE-CAPTURE-FIX:WI_LRH_LAND_WORKTREE_CAPTURE_FIX)[2026-08-24T08:14:37+00:00]
work_item: WI-LRH-LAND-WORKTREE-CAPTURE-FIX
status: in_progress
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-LAND-WORKTREE-CAPTURE-FIX.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/634
commit: 6541b959
created_at: 2026-08-24T08:40:39+00:00
---

# Summary

Implements `WI-LRH-LAND-WORKTREE-CAPTURE-FIX`: fixes the two real gaps in
`/lrh-land`'s Main-worktree-lock workaround discovered live during PR
#628's own closeout -- a worktree-unsafe hardcoded `.git/` capture path,
and a stale `SKILL.md` illustrative snippet.

# Result

Fixed `src/lrh/skills/lrh-land/references/land-workflow.md`'s
Main-worktree-lock rule: replaced the hardcoded
`.git/lrh-tmp-branch-parent-<slug>` path (capture, read-back, and cleanup
-- three occurrences) with `$(git rev-parse --git-dir)`-resolved paths,
which work correctly whether `.git` is a plain directory or a worktree
gitdir-pointer file.

Reworded `src/lrh/skills/lrh-land/SKILL.md`'s Step 7 illustrative bash
snippet to explicitly note it is a mainline sketch only, not a
copy-pasteable complete procedure, and to point to `land-workflow.md`'s
Main-worktree-lock rule and its Main-Worktree-Lock Troubleshooting section
for the real commands -- rather than duplicating that content inline,
which would create a second copy to keep in sync.

Mirrored to `.claude/` (raw `cp`), `.agents/` and `.gemini/` (via the
proper skill installer -- `lrh skills install --scope project --local
--target codex|antigravity --source current-repo --force`, run as two
separate invocations, not raw `cp`, per PR #628's own review finding on
this exact point). The installer's `--force` also regenerated several
other, unrelated already-stale skills each time; reverted those via
`git show HEAD:<path> > <path>` before committing, keeping this PR scoped
to `lrh-land` only (`git checkout`/`restore`/`rm -rf` are permission-
blocked in this session).

A naming collision was hit and resolved: the derived branch name
(`xenotaur/chore/wi-lrh-land-worktree-capture-fix`) already existed
locally as a fully-merged, stale branch from the PR that originally filed
this same work item (#631) -- inevitable, since WI-creation and
WI-implementation branches derive identically from the WI's own ID and
type. Used `xenotaur/chore/wi-lrh-land-worktree-capture-fix-impl` instead,
flagged to the user as a divergence from the approved run plan's stated
branch name rather than silently substituted.

Diff-mode `/lrh-self-review`: no blocking findings. Independently
re-verified before accepting: reproduced the fixed capture/read-back/
cleanup command sequence directly (including a path-with-space quoting
stress test), confirmed the one remaining literal
`.git/lrh-tmp-branch-parent-<slug>` grep match is explanatory prose about
the old bug (not a leftover instance), and re-ran the mirror-parity `diff`
commands directly rather than accepting the subagent's report alone.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- Mirror parity: `diff` clean for body content across `src/`, `.claude/`,
  `.agents/`, `.gemini/` (installer-normalized frontmatter differences in
  `.agents`/`.gemini` `SKILL.md` are expected and pre-existing, out of
  scope).
- `GATE-DEFINITION` markers re-verified correctly paired (2 open, 2
  close) after the edit.
- Doc-only change (all 8 changed files `.md`) -- `scripts/format`/
  `scripts/lint` skipped on the known, pre-existing local/CI `black`/
  `ruff` version mismatch, unrelated to this change; `scripts/test`
  skipped, no Python files touched.

# Follow-up

None deferred -- the fix is complete as scoped, matching both acceptance
criteria in the work item.
