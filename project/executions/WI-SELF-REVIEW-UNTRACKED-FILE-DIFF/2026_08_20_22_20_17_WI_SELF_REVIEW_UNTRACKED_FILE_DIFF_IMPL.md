---
execution_id: 2026_08_20_22_20_17_WI_SELF_REVIEW_UNTRACKED_FILE_DIFF_IMPL
prompt_id: PROMPT(WI-SELF-REVIEW-UNTRACKED-FILE-DIFF:WI_SELF_REVIEW_UNTRACKED_FILE_DIFF_IMPL)[2026-08-20T04:48:14+00:00]
work_item: WI-SELF-REVIEW-UNTRACKED-FILE-DIFF
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/576
commit: ae710248c0f407f2e672cdf0d2a45232ba507ffd
created_at: 2026-08-20T22:20:17+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SELF-REVIEW-UNTRACKED-FILE-DIFF.md
session_transcript: claude-app:c02da21d-4a23-4315-857f-0829e0483667
---

# Summary

Implemented `WI-SELF-REVIEW-UNTRACKED-FILE-DIFF`: fixed `/lrh-self-review`
Step 1's diff-mode `git diff main` command, which never includes untracked
files, so a diff of only brand-new files (no tracked-file modifications)
was silently reported as "nothing to review."

# Result

Edited `src/lrh/skills/lrh-self-review/SKILL.md` Step 1: added
`git add -N .` (intent-to-add) immediately before `git diff main`, plus a
note explaining why (untracked files are invisible to `git diff` in any
form) and clarifying the interaction with Step 8's staging. Manually
reproduced the bug in a scratch repo first (empty diff without the fix)
and confirmed the fix resolves it (populated diff with `git add -N .`).
Mirrored the change to `.claude/skills/lrh-self-review/SKILL.md`
(byte-identical). Ran a diff-mode `/lrh-self-review` pass before pushing:
the subagent independently reproduced the core git behavior and flagged
one real wording overstatement (the original "no effect on a later
`git commit`" claim didn't account for `git commit -a`, which does include
intent-to-add file content) — I independently re-verified this with my own
git experiment and tightened the wording before pushing (see the paired
`_SELFREVIEW` execution record for full detail). Opened PR #576 from
branch `xenotaur/chore/wi-self-review-untracked-file-diff-impl`, targeting
`main` (does not depend on WI PR #575 having merged first for the code
change itself, only for the WI's eventual `resolved` status).

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `diff -q src/lrh/skills/lrh-self-review/SKILL.md .claude/skills/lrh-self-review/SKILL.md` — identical.
- Manual repro in a scratch git repo: new untracked file → `git diff main` empty (bug reproduced) → `git add -N .` → `git diff main` shows the new file (fix confirmed).
- `scripts/lint` / `scripts/format --check` fail repo-wide on a
  pre-existing tool-version pin mismatch (`ruff`/`black` pins in
  `pyproject.toml` don't match locally installed versions) — same failure
  reproduces on `main`, confirmed unrelated to this change.
- Diff-mode `/lrh-self-review`: cold subagent independently reproduced the
  git behavior, confirmed `.gitignore` handling and mirror byte-identity,
  flagged one real wording overstatement (fixed) and one non-blocking
  backlog note (cwd-scoping of `git add -N .`, consistent with existing
  behavior elsewhere in this skill).

# Follow-up

- Merge WI PR #575 before or alongside this PR so `/lrh-closeout` can
  later resolve `WI-SELF-REVIEW-UNTRACKED-FILE-DIFF` to `status: resolved`.
- Backlog note (not in scope): `git add -N .` is cwd-scoped; if this skill
  is ever invoked from a subdirectory instead of repo root, new files
  elsewhere in the repo would remain invisible — consistent with existing
  assumptions elsewhere in this skill and `/lrh-implement`, not a new gap.
- Update `session_transcript` from `pending` to the durable session
  pointer once available.

## Review-response round 1

Two real `chatgpt-codex-connector` findings applied here (one on this PR,
one on the paired PR #581's equivalent gap, replicated here since the same
bug existed in this PR too):

1. **P2 (this PR) — `git add -N .` pollutes the index for unrelated
   untracked files.** Independently verified: with unrelated,
   non-`.gitignore`d untracked files present, `git add -N .` intent-adds
   *all* of them, not just the diff's own new files, and — since Step 8
   doesn't prohibit `git commit -a` — those entries could leak into a
   later commit. Fixed by adding `git reset` (no path) immediately after
   `git diff main` in Step 1's diff-mode block, restoring the index to
   its pre-diff state; verified in a scratch repo that this fully resolves
   it (`git commit -a` afterward includes nothing from the untracked
   files). Rewrote the accompanying prose accordingly — the previous
   "`git commit -a` is the one exception" caveat no longer applies since
   the intent-to-add entries don't survive past this step anymore.
2. **P1 (found on paired PR #581 for `lrh-land`; same gap here) — missing
   Codex/Antigravity mirror sync.** Re-ran `lrh skills install --local
   --target all --source current-repo --force` and verified with
   `lrh skills check --target claude --local --source current-repo` /
   `lrh skills status --target {codex,antigravity} --local --source
   current-repo` that all three targets are up to date.

Re-ran `lrh validate` after both fixes — 0 errors, 0 warnings. Rebased
onto latest `main` and force-pushed (`--force-with-lease`) to keep the
branch history linear and the diff clean of unrelated upstream drift —
this is a solo feature branch on an open, not-yet-reviewed-by-a-human PR,
not shared history.
