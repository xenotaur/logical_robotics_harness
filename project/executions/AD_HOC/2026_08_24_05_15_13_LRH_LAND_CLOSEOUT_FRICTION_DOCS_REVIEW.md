---
execution_id: 2026_08_24_05_15_13_LRH_LAND_CLOSEOUT_FRICTION_DOCS_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_LAND_CLOSEOUT_FRICTION_DOCS_REVIEW)[2026-08-24T05:15:05+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/628
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/628
commit: 938aab78
created_at: 2026-08-24T05:15:13+00:00
---

# Summary

`/lrh-review-response` round for PR #628, inlined from `/lrh-land` Step 4.

# Result

`lrh request review_response` returned real thread data (not
`Nothing to resolve:`); GraphQL duplicate-node pattern (known from earlier
this session) meant the raw output listed each finding multiple times.
Deduplicated to 4 distinct findings, each independently re-verified
against the current diff/repo state before triage (none accepted on the
review comment's word alone):

1. **chatgpt-codex-connector (P2)** -- raw `cp` mirroring broke
   `CodexSkillRenderer`/`AntigravitySkillRenderer` frontmatter-stripping
   (`argument-hint`, `when_to_use`), leaving `lrh skills status` reporting
   `lrh-land` as locally modified for both targets. Verified directly via
   `lrh skills status --scope project --target codex|antigravity --source
   current-repo` before fixing. Fixed by regenerating through the proper
   installer (`lrh skills install --scope project --local --target
   <codex|antigravity> --source current-repo --force`) instead of `cp`.
2. **copilot** -- Step 7's material-divergence comparison always
   classified the no-primary backfill record as "newly appeared ... not in
   the preview," defeating the single-ask path for exactly the backfill
   case it exists to support. Verified via direct read + `git blame`
   (pre-existing text, not part of this PR's original diff, but in a file
   this PR touches). Fixed with an explicit exception for that one
   deterministic record.
3. **copilot** -- this PR's own new Step 7 anti-pattern callout was
   broader than intended, and as written could suppress the
   material-divergence rule's own required fresh ask. Verified by direct
   read of both sections. Qualified the callout to not override that rule.
4. **copilot** -- this PR's own new non-fast-forward troubleshooting row
   referenced an undefined `<tmp-branch-parent>` with no fail-closed path
   on a rebase conflict. Verified by direct read/grep (`tmp-branch-parent`
   defined nowhere in the file). Fixed: `tmp_branch_parent` now captured
   explicitly at branch-creation time in the Main-worktree-lock rule; the
   troubleshooting row adds an explicit abort-and-report path for a
   conflicting rebase and for a failed ancestry check.

**Side effect caught and reverted:** the `--force` install run initially
also regenerated several other already-stale, unrelated skills
(`lrh-closeout`, `lrh-confirm-fixes`, `lrh-execute`, `lrh-implement`,
`lrh-review-response`, `lrh-antigravity-export`) across `.agents`/`.gemini`
-- broader than what was previously scoped for this PR. Reverted those via
`git show HEAD:<path> > <path>` (`git checkout`/`restore` are
permission-blocked destructive ops in this session) before committing, so
this PR stays scoped to `lrh-land` only. One stray untracked directory
(`.gemini/plugins/lrh/skills/lrh-antigravity-export/`) from the same side
effect could not be removed (`rm -rf` also permission-blocked) but is
harmless and was left unstaged.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning.
- `lrh skills status --scope project --target codex|antigravity --source
  current-repo`: `lrh-land` reports up to date for both, post-fix.
- `git status --short` re-checked after staging to confirm only the 8
  intended `lrh-land` files were committed.

# Follow-up

- None deferred -- all 4 findings fixed and pushed in commit `938aab78`.
