---
execution_id: 2026_10_26_07_47_49_SKILLS_INSTALL_DANGLING_SYMLINK_SELFREVIEW
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DANGLING_SYMLINK_SELFREVIEW)[2026-10-26T07:47:48+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_26_07_48_32_SKILLS_INSTALL_DANGLING_SYMLINK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/856
commit:
created_at: 2026-10-26T07:47:49+00:00
agent: claude_app
instruction_source: lrh-self-review diff-mode from /lrh-implement Step 7.5 for PROMPT(AD_HOC:SKILLS_INSTALL_DANGLING_SYMLINK)[2026-10-22T18:03:35+00:00]
session_transcript: pending
---

# Summary

Diff-mode `/lrh-self-review` pass over the uncommitted change that makes a
dangling symlinked skill directory count as a local modification in
`install_skills` and `inspect_skills` (`src/lrh/skills/installer.py`), with
unit and CLI regression tests and a reference-doc sentence. Diff-mode runs
before `/lrh-implement` Step 9 creates the primary record, so `rerun_of` and
`pr:` start empty and are backfilled at Step 9.

# Result

- Mode: diff-mode, report-only (no `--apply`).
- Findings: 0 blocking. Verified: no other skill-destination `exists()`
  check mishandles a dangling link (`install_named_skills` always
  force-copies; `plugin.json` paths already guard `is_symlink()`;
  `exporter.py` checks are on source/output paths); `--force` unlinks the
  link itself and never writes into its target; nothing reads through the
  link; the `_snapshot_tree` change does not alter existing tests; Python
  3.11 compatible; the doc sentence is accurate. The subagent reproduced
  the CLI bug by hand on the old code and confirmed the fix.
- Minor notes, both on test code added by this change, fixed before the
  first push by the invoking session (independently verified, in scope):
  1. `test_dangling_symlinked_skill_root_replaced_only_with_force`
     overstated what it checks — renamed to
     `test_dangling_symlinked_skill_root_replaced_with_force`.
  2. The dangling-root install tests sat in `TestDiffSkill` — moved to
     `TestInstallSkills`; only the diff test stays in `TestDiffSkill`.
- Theoretical, pre-existing, not acted on: a skill rendering zero source
  files would compare a symlinked root as up to date (empty == empty); real
  skills always ship `SKILL.md`.
- Re-verification by the invoking session: with `installer.py` reverted to
  `HEAD`, 5 of the 6 new dangling tests fail (the `diff_skill` coverage test
  passes either way, as that path already handled symlinked roots).

# Validation

- Subagent: `python -m unittest tests.skills_installer_test
  tests.cli_tests.skills_test` (142 OK); manual old-vs-new CLI reproduction.
- After the fixes: `scripts/format --check --diff` clean, `scripts/lint`
  exit 0, `scripts/test` 2377 OK, `lrh validate` 0 errors.

# Follow-up

None.
