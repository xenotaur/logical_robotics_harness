---
execution_id: 2026_10_26_07_48_32_SKILLS_INSTALL_DANGLING_SYMLINK
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DANGLING_SYMLINK)[2026-10-22T18:03:35+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/856
commit:
created_at: 2026-10-26T07:48:32+00:00
agent: claude_app
instruction_source: ad_hoc conversation — follow-up to PR 832, protect dangling symlinked skill directories in lrh skills install/status/check
session_transcript: pending
---

# Summary

`install_skills` and `inspect_skills` decided a skill was missing with
`not dest.exists()`, which follows symlinks, so a dangling symlinked skill
directory looked missing: `lrh skills install` silently replaced it without
`--force`, `--diff`/`--dry-run` said "would install", and `status`/`check`
said "missing". A resolving symlinked skill directory was already protected.
Surfaced as a pre-existing edge case by the self-review passes on PR #832.

# Result

- `src/lrh/skills/installer.py`: both checks now use
  `not dest.exists() and not dest.is_symlink()` (the guard
  `_install_antigravity_plugin_manifest` already uses). A dangling symlink
  falls through to the existing comparison: kept unless `--force` (which
  unlinks the link itself), reported modified, and reported by `--diff`
  via the existing symlink note.
- `tests/skills_installer_test.py`: dangling-root tests for install,
  forced dry run, `--force`, `inspect_skills`, and `diff_skill`.
- `tests/cli_tests/skills_test.py`: CLI `--diff` regression test;
  `_snapshot_tree` records symlinks by link target.
- `docs/reference/cli/skills.md`: one sentence on symlinked skill
  directories counting as local modifications.
- Prior-art check: no existing WI/backlog entry; the `plugin.json` guard is
  the reused pattern.
- Self-review (diff-mode): 0 blocking; two test-code nits fixed before the
  first push; see
  `2026_10_26_07_47_49_SKILLS_INSTALL_DANGLING_SYMLINK_SELFREVIEW.md`.

# Validation

Per-worktree conda env `IntelligentHopper` (rebound to this worktree with
`scripts/conda-worktree-env IntelligentHopper` first):

- `scripts/version tools`: Python 3.11.17, ruff 0.15.12, black 26.3.1
- `scripts/format --check --diff`: 298 files unchanged
- `scripts/lint`: exit 0
- `scripts/test`: 2377 tests, OK
- `lrh validate`: 0 errors, 0 warnings
- With `installer.py` reverted to the branch base, 5 of 6 new dangling
  tests fail (the `diff_skill` coverage test passes either way).

# Follow-up

None.
