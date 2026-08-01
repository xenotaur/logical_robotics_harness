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

Attempted a full implementation of `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`
(`/lrh-closeout` auto-refreshing a skill-touching PR's global install).
The `/lrh-closeout` wiring went through 14 rounds of review, each
surfacing a further real gap in its checkout-verification logic; a
fresh-context go/no-go self-review then returned **NO-GO** on that part
of the design (disproportionate complexity, wrong foundational
approach — see the `_REVIEW` execution record and PR #456's body for the
full reasoning) and it was reverted. What ships from this PR is only the
standalone, independently-useful capability the reverted design was
built on: `install_named_skills()`. `/lrh-closeout` is unchanged; the
WI's stated acceptance criteria are **not** met by this PR.

# Result

- Added `install_named_skills()` / `RefreshStatus` /
  `TargetedRefreshResult` to `src/lrh/skills/installer.py`. Validates
  each name against the current package's `_skill_names()` before any
  destructive filesystem operation, returning an explicit `absent`
  result rather than `rmtree`-then-fail (the existing `_copy_skill`
  deletes the destination before reading the package source). Every
  other installed skill is left completely untouched. Guards against a
  bare `str` (would otherwise iterate character-by-character) and a
  one-shot iterable (would otherwise be silently consumed by double
  iteration inside the function).
- Added 7 tests to `tests/skills_installer_test.py` (`TestInstallNamedSkills`;
  see the `_REVIEW` execution record for the round-by-round additions):
  refresh of a differing-bytes skill, an unnamed sibling left alone, an
  absent name with a pre-existing stale directory (untouched, not
  deleted), an absent name with no existing directory (creates nothing),
  a bare string raising `TypeError`, a one-shot iterable not being
  silently consumed, and a non-`str` element raising `TypeError`.
- Initially extended `/lrh-closeout` (both SKILL.md trees) with a
  "skill refresh" step wiring `install_named_skills()` into closeout —
  **reverted** after the self-review's NO-GO verdict. Both trees are back
  to byte-identical with `origin/main` (verified: 0 diff).
- The originally-planned bootstrap step (WI item 5) is moot — there is
  no `/lrh-closeout` wiring left to bootstrap.

# Validation

- `python3 -m pytest tests/skills_installer_test.py`: 29/29 pass (final,
  post-revert)
- `scripts/format --check --diff`, `scripts/lint`: clean
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)
- `git diff origin/main -- .claude/skills/lrh-closeout/SKILL.md src/lrh/skills/lrh-closeout/SKILL.md`:
  empty — confirms the revert is clean, not a near-revert
- Manual smoke tests of `install_named_skills` (refresh, absent-name
  safety with and without a pre-existing directory, bare-string guard,
  one-shot-iterable guard) — all as documented in the tests above

# Follow-up

- `WI-CLOSEOUT-SKILLS-INSTALL-SYNC` itself needs a human decision on how
  to resolve: its acceptance criteria weren't met, but the underlying
  problem (global skill installs going stale) is still open. Handling
  that decision is out of scope for this execution record.
- If the underlying problem is picked up again later, the self-review's
  suggested alternative (a small tested CLI command reading from git's
  object database at a SHA pinned at confirm-gate time, rather than a
  live filesystem read) is recorded in PR #456's body and the `_REVIEW`
  execution record.
