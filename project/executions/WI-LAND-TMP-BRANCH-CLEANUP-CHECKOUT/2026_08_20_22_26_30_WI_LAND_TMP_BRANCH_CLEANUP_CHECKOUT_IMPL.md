---
execution_id: 2026_08_20_22_26_30_WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT_IMPL
prompt_id: PROMPT(WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT:WI_LAND_TMP_BRANCH_CLEANUP_CHECKOUT_IMPL)[2026-08-20T22:22:59+00:00]
work_item: WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/581
commit: 3e0a54298d1e68678ac10904b34ef5fc6349888a
created_at: 2026-08-20T22:26:30+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT.md
session_transcript: claude-app:c02da21d-4a23-4315-857f-0829e0483667
---

# Summary

Implemented `WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT`: fixed `/lrh-land`
Step 7's main-worktree-lock workaround, which ran `git branch -D
tmp-<slug>` while `HEAD` was still checked out on `tmp-<slug>`, so the
delete always failed right after the closeout commit had already landed
on `main`.

# Result

Edited `src/lrh/skills/lrh-land/SKILL.md` Step 7: inserted
`git checkout <pr-branch>` (with `--detach` as a documented fallback)
between `git push tmp-<slug>:main` and `git branch -D tmp-<slug>`, plus a
note explaining Git's invariant and that `<pr-branch>` is already known
from Step 1's `headRefName`. Updated
`references/land-workflow.md`'s `Main-worktree-lock` rule row to match.
Manually reproduced the bug in a scratch repo first (delete failed while
checked out on `tmp-slug`) and confirmed the fix resolves it (delete
succeeded after checking out the other branch). Mirrored both files to
`.claude/skills/lrh-land/` (byte-identical). Ran a diff-mode
`/lrh-self-review` pass before pushing: the subagent independently
reproduced the same git behavior with its own experiment and confirmed
`<pr-branch>` is genuinely available (not a stale/pruned reference) at
that point in Step 7's documented control flow — zero findings, LGTM (see
the paired `_SELFREVIEW` execution record). Opened PR #581 from branch
`xenotaur/chore/wi-land-tmp-branch-cleanup-checkout-impl`, targeting
`main` (does not depend on WI PR #580 having merged first for the code
change itself, only for the WI's eventual `resolved` status).

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `diff -q` on both mirrored file pairs (`SKILL.md`,
  `references/land-workflow.md`) between `src/lrh/skills/lrh-land/` and
  `.claude/skills/lrh-land/` — identical.
- Manual repro in a scratch git repo: `git branch -D tmp-slug` fails
  while checked out on it (bug reproduced) → succeeds after checking out
  elsewhere first (fix confirmed).
- `scripts/lint` / `scripts/format --check` fail repo-wide on a
  pre-existing tool-version pin mismatch (`ruff`/`black` pins in
  `pyproject.toml` don't match locally installed versions) — same failure
  reproduces on `main`, confirmed unrelated to this change.
- Diff-mode `/lrh-self-review`: cold subagent independently reproduced the
  core git claim, confirmed `<pr-branch>` availability and mirror
  byte-identity, confirmed scope matched the WI exactly — zero findings,
  verdict LGTM.

# Follow-up

- Merge WI PR #580 before or alongside this PR so `/lrh-closeout` can
  later resolve `WI-LAND-TMP-BRANCH-CLEANUP-CHECKOUT` to
  `status: resolved`.
- Update `session_transcript` from `pending` to the durable session
  pointer once available.

## Review-response round 1

Two real bot findings on the paired WI PR (#580) applied here, since they
implicated this PR's actual fix, not just the WI text:

1. **`chatgpt-codex-connector` P1 — missing Codex/Antigravity mirror
   targets.** The original push only synced `.claude/skills/lrh-land/`.
   This repo also renders to `.agents/skills/lrh-land/` (Codex) and
   `.gemini/plugins/lrh/skills/lrh-land/` (Antigravity/Gemini) via
   `lrh skills install --local --target all --source current-repo
   --force` — verified these are *rendered* outputs (different YAML
   frontmatter formatting per target), not byte-identical copies, so a
   raw `cp` would have been wrong even if attempted. Re-ran the installer
   for all three targets and confirmed with `lrh skills check --target
   claude --local --source current-repo` and `lrh skills status --target
   {codex,antigravity} --local --source current-repo` that all three are
   now up to date against this branch's `src/lrh/skills/lrh-land/`.
2. **`chatgpt-codex-connector` P1 — broken `git push tmp-<slug>:main`.**
   Independently verified in a scratch repo: `git push tmp-<slug>:main`
   (no explicit remote) fails — a bare `<ref>:<ref>` argument with no
   space is parsed as the repository, not a refspec. This line predates
   this WI's own change (I only added the checkout-away step after it),
   but it sits directly upstream of my fix and the WI's acceptance
   criteria implicitly claim the full documented sequence runs correctly
   end-to-end, so fixed it here too: `git push tmp-<slug>:main` →
   `git push origin tmp-<slug>:main` in both `SKILL.md` Step 7 and
   `references/land-workflow.md`'s rule row.

Re-ran `lrh validate` after both fixes — 0 errors, 0 warnings.
