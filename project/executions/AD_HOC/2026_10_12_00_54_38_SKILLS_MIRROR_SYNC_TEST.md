---
execution_id: 2026_10_12_00_54_38_SKILLS_MIRROR_SYNC_TEST
prompt_id: PROMPT(AD_HOC:SKILLS_MIRROR_SYNC_TEST)[2026-10-11T15:03:39+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/831
commit:
created_at: 2026-10-12T00:54:38+00:00
agent: claude_app
instruction_source: ad-hoc — pin .claude/.agents/.gemini skill install targets to src via a generalized mirror sync test, and update /lrh-create-skill and CONTRIBUTING to render new skills into all three targets
session_transcript: pending
---

# Summary

This change generalizes the `.gemini`-only sync test from PR #819 into
`tests/packaging_tests/skills_mirror_sync_test.py`. The new test pins all
three committed skill install targets to the installer's render of
`src/lrh/skills/`. It also updates `/lrh-create-skill` and `CONTRIBUTING.md`
so new skills reach every target.

# Result

**Context.** The PR #819 follow-up analysis (2026-10-11) found that
`.claude/skills` and `.agents/skills` were pinned only for specific skills and
files, by `skills_vcs_merge_wiring_test.py` and
`skills_execute_prereq_stop_test.py`. That is the same gap that let `.gemini`
drift.

**Test.** For each target, the test asserts four things:

- the committed skill set equals the `src` skill set;
- each skill equals `installer._renderer_for_target(target).render(...)`
  file by file;
- there are no symlinks, matching the installer;
- the Antigravity `plugin.json` equals the installer manifest.

The target-to-renderer mapping is:

| Target | Renderer |
|---|---|
| `.claude/skills` | CLAUDE |
| `.agents/skills` | CODEX |
| `.gemini/plugins/lrh/skills` | ANTIGRAVITY |

It passes on `main` as-is: all targets were already in sync. Mutation checks
in each target fail as expected.

**`/lrh-create-skill`.**

- *Why it changed:* Step 6 hand-copied new skills into `.claude` only, so
  every skill created with it would fail the new test (and has failed the
  `.gemini` pin since #819).
- *What changed:* Step 6 now renders into all three targets with
  `lrh skills install --local --target all --source current-repo`, with a
  dry-run preview first. It explains what to do on a "local modifications —
  skipped" warning and keeps a `diff -r` fallback for older checkouts.
- *Supporting updates:* the description, the Step 6 re-check, the
  `git add` line and the checklist were updated to match.
- *Regeneration:* the skill was regenerated into all three targets from a
  one-skill scratch source.

**Plan approval.** The user approved this scope at Step 4 ("Approve + fix
create-skill").

**Additions beyond the approved file list**, both flagged in the PR body:

- `CONTRIBUTING.md`'s skills section. It said "two locations",
  hand-copy, and "future CI enforcement"; `WS-SKILLS` is resolved with no
  such open item.
- `lrh-review-response` `references/canonical-validation.md`, which had a
  `.claude`-only `diff -r`. This was a self-review finding.

**Self-review.** Diff-mode `/lrh-self-review` found one medium docs issue
(BSD `cp` with a trailing slash in the one-skill tip), three low issues and
one nit. All were verified and fixed. See
`2026_10_12_00_53_45_SKILLS_MIRROR_SYNC_TEST_SELFREVIEW`.

**Prior art.** No existing work item or backlog entry requested this.

# Validation

All runs used the per-worktree conda env `LrhGeminiSkillsSync` (Python 3.11,
ruff 0.15.12, black 26.3.1), after rebasing onto `origin/main` `fac55e58`.

- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 2288 tests, OK.
- `lrh validate`: 0 errors.
- `lrh skills install --local --target all --source current-repo --dry-run`:
  all up to date.
- `lrh chain-defaults status`: not stale.

# Follow-up

- When rebased, open PRs #553 and #624 will fail the sync test until they
  regenerate their skill copies. This was already true for `.gemini` since
  #819.
