---
execution_id: 2026_10_10_05_50_34_SKILLS_INSTALL_DIFF_READ_ONLY
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DIFF_READ_ONLY)[2026-10-10T05:35:27+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/820
commit: f4dd10e735c4eff5a5cf19290df1e0637d5c69a9
created_at: 2026-10-10T05:50:34+00:00
agent: claude_app
instruction_source: ad_hoc conversation — make `lrh skills install --diff` never write files after it installed lrh-antigravity-export on 2026-10-10
session_transcript: claude-app:12a73f73-ccc5-4308-abe1-4ceb4827d712
---

# Summary

Make `lrh skills install --diff` strictly read-only. The CLI passed only
`--dry-run` through as the preview flag, so `--diff` ran a real install —
writing missing skills (reported as `installed:`) and, with `--force`,
overwriting modified ones — while printing diffs only for skipped skills.

# Result

- `src/lrh/cli/main.py`: `--diff` now implies preview for both
  `install_skills_for_targets` and `format_report`; missing skills report
  `would install` and the newly-created restart note is suppressed. With
  `--diff --force` (user-approved extension), `would overwrite` entries
  are diffed too. Help text updated.
- `tests/cli_tests/skills_test.py`: three regression tests asserting the
  filesystem is unchanged after `--diff` on an empty antigravity target, an
  antigravity target missing one skill, and `--diff --force` on a modified
  codex skill. All three fail against the pre-change `main.py`.
- `docs/reference/cli/skills.md`, `docs/how-to/keep-skills-up-to-date.md`:
  document that `--diff` never writes.
- Prior-art check: no existing WI/backlog entry for this; the original
  `WI-SKILLS-INSTALL-DIFF` never specified read-only semantics.
- Self-review (diff-mode): 0 blocking findings, 3 cosmetic notes; see
  `2026_10_10_05_50_03_SKILLS_INSTALL_DIFF_READ_ONLY_SELFREVIEW.md`.

# Validation

Run in the per-worktree conda env `IntelligentHopper`
(`scripts/conda-worktree-env IntelligentHopper`):

- `scripts/version tools`: lrh 0.2.5.dev3412+g0876991b7, Python 3.11.17,
  ruff 0.15.12, black 26.3.1 (pyright not installed; not needed by lint)
- `scripts/format --check --diff`: clean
- `scripts/lint`: exit 0
- `scripts/test`: 2223 tests, OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

None.
