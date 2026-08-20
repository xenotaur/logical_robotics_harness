---
execution_id: 2026_08_20_22_20_17_WI_SELF_REVIEW_UNTRACKED_FILE_DIFF_IMPL
prompt_id: PROMPT(WI-SELF-REVIEW-UNTRACKED-FILE-DIFF:WI_SELF_REVIEW_UNTRACKED_FILE_DIFF_IMPL)[2026-08-20T04:48:14+00:00]
work_item: WI-SELF-REVIEW-UNTRACKED-FILE-DIFF
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/576
commit: 
created_at: 2026-08-20T22:20:17+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SELF-REVIEW-UNTRACKED-FILE-DIFF.md
session_transcript: pending
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
