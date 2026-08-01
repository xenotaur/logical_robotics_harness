---
execution_id: 2026_08_01_12_42_29_WI_CLOSEOUT_SKILLS_INSTALL_SYNC_IMPL
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SKILLS_INSTALL_SYNC_IMPL)[2026-08-01T12:33:03-04:00]
work_item: WI-CLOSEOUT-SKILLS-INSTALL-SYNC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/456
commit: 
created_at: 2026-08-01T12:42:29-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLOSEOUT-SKILLS-INSTALL-SYNC.md
session_transcript: claude-app:20d16dd9-a465-4d31-b39f-280db14488ef
---

# Summary

Implemented `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`: `/lrh-closeout` now
detects when a closed-out PR's diff touches `.claude/skills/` or
`src/lrh/skills/`, and refreshes exactly those skill names via a new
targeted install capability, bypassing the coarse-grained
`USER_MODIFIED` check for those names only.

# Result

- Added `install_named_skills()` / `RefreshStatus` /
  `TargetedRefreshResult` to `src/lrh/skills/installer.py`. Validates
  each name against the current package's `_skill_names()` before any
  destructive filesystem operation, returning an explicit `absent`
  result rather than `rmtree`-then-fail (the existing `_copy_skill`
  deletes the destination before reading the package source). Every
  other installed skill is left completely untouched.
- Added 6 new tests to `tests/skills_installer_test.py` (in
  `TestInstallNamedSkills`, updated across this PR's review rounds):
  refresh of a differing-bytes skill, an unnamed sibling left alone, an
  absent name with a pre-existing stale directory (untouched, not
  deleted), an absent name with no existing directory (creates nothing),
  a bare string raising `TypeError` instead of being iterated
  character-by-character, and a one-shot iterable (generator) not being
  silently consumed by double iteration.
- Extended `.claude/skills/lrh-closeout/SKILL.md` (and its
  `src/lrh/skills/lrh-closeout/SKILL.md` mirror, kept byte-identical)
  with a 6th Step 2 assessment item ("Skill refresh"): REST PR Files
  endpoint fetch (paginated, 3,000-file ceiling and fetch-failure
  handling), structural candidate-name filtering, both-revision
  `_skill_names()` partitioning (base revision via the `git ls-tree`
  colon form, not the pathspec form, which doesn't list a directory's
  children), Step 4 confirm-gate disclosure before any file is written,
  Step 5 execution with `PYTHONPATH` explicitly pinned to the merged
  checkout, and a Step 8 report line. Updated the Quality Checklist and
  "What This Skill Does Not Do" to match.
- Documented the bootstrap requirement (WI item 5 — this PR's own
  closeout cannot auto-trigger the new step, since the closing session
  runs the pre-fix `lrh-closeout`) explicitly in the PR body's "Bootstrap
  note" section, with the exact command to run by hand.

# Validation

- `python3 -m pytest tests/skills_installer_test.py`: 28/28 pass (final
  count after review-round fixes; see the `_REVIEW` execution record for
  the incremental counts as tests were added)
- `scripts/format --check --diff`, `scripts/lint`: clean
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)
- `scripts/test`: OK
- Manual smoke test of the exact `install_named_skills` invocation
  documented in the SKILL.md (refreshed a real skill name, returned
  `absent` for a fake one, created no directory for the fake one)
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout`:
  identical

# Follow-up

- The WI's manual smoke-test items (full end-to-end `/lrh-closeout` run
  against a real skill-touching PR, multi-commit/rebase-merge file-list
  completeness, 3,000-file ceiling, fetch-failure simulation) are not
  exercised in this session — they require a future skill-touching PR to
  close out through this path, or a dedicated test harness this WI's
  scope didn't include.
- Bootstrap: this PR's own closeout must manually refresh
  `~/.claude/skills/lrh-closeout` per the PR body's bootstrap note —
  flagged for the closing session, not yet executed.
