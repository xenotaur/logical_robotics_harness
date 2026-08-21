---
execution_id: 2026_08_20_22_22_31_WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT
prompt_id: PROMPT(AD_HOC:WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT)[2026-08-20T22:21:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/580
commit: 
created_at: 2026-08-20T22:22:31+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT.md
session_transcript: pending
---

# Summary

Created work item `WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT`, the third of
three skill-content bugs surfaced while triaging Taurcode PR #82 (a
mechanical `lrh skills install --local --force` resync of this project's
own skill package). `/lrh-land` Step 7's main-worktree-lock workaround
deletes `tmp-<slug>` with `git branch -D` while `HEAD` is still checked
out on it — Git always refuses this, right after the closeout commit has
already landed on `main`.

# Result

Wrote
`project/work_items/proposed/WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT.md`
scoping the fix: check out a branch other than `tmp-<slug>` (the original
PR branch, or a detached `HEAD`) before the delete, in both
`SKILL.md` Step 7 and `references/land-workflow.md`'s `Main-worktree-lock`
rule row. Opened PR #580 from branch
`xenotaur/chore/wi-land-tmp-branch-cleanup-checkout`. This record covers
the planning phase only (work item creation); implementation is a separate
execution record, to be created when the fix is implemented.

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Implement the fix described in the work item (edit
  `src/lrh/skills/lrh-land/SKILL.md` Step 7 and
  `references/land-workflow.md`, mirror to `.claude/skills/lrh-land/`).
- Update `session_transcript` from `pending` to the durable session pointer
  once available.

## Review-response round 1

Three `chatgpt-codex-connector` findings on this PR applied to the WI text:

1. **P1 — missing remote in `git push tmp-<slug>:main`.** Independently
   verified in a scratch repo: a bare `<ref>:<ref>` argument (no space, no
   configured remote named `tmp-<slug>`) is parsed by `git push` as the
   repository argument, not a refspec, so the documented sequence fails
   before ever reaching the checkout-away step this WI adds. Folded the
   fix (`git push origin tmp-<slug>:main`) into this WI's scope, required
   changes, and acceptance criteria — it's the same code block and the
   same root-cause category, and the original acceptance criterion's
   claim that the sequence "runs as documented" wasn't true without it.
2. **P1 — missing Codex/Antigravity mirror targets.** Confirmed this repo
   renders skills to `.agents/skills/` (Codex) and
   `.gemini/plugins/lrh/skills/` (Antigravity), not just
   `.claude/skills/`, via `lrh skills install --local --target all
   --source current-repo --force` — verified these are rendered outputs
   (different frontmatter formatting per target), not byte copies. Added
   both targets to `artifacts_expected`, `Scope`, `Required Changes`, and
   `Acceptance Criteria`, and switched the required-evidence commands from
   a bare `diff -q` to `lrh skills check`/`status --source current-repo`.
3. **P2 — `forbidden_actions` contradicts required validation.**
   `delete_branch` was listed while the WI's own manual-repro validation
   requires running `git branch -D` on a scratch branch. Removed it from
   `forbidden_actions` and added a Risk Notes paragraph clarifying the
   delete only ever targets a disposable scratch repository, never this
   project's own branches.

Re-ran `lrh validate` after all changes — 0 errors, 0 warnings.
