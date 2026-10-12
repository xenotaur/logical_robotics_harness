---
execution_id: 2026_10_12_06_06_28_SKILLS_INSTALL_DIFF_HELP_WORDING
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DIFF_HELP_WORDING)[2026-10-12T00:40:09+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/832
commit: 
created_at: 2026-10-12T06:06:28+00:00
agent: claude_app
instruction_source: ad_hoc conversation — follow-up to PR 820, make the `lrh skills install --diff` help text match its behavior
session_transcript: pending
---

# Summary

Reword the `lrh skills install --diff` argparse help. It said the flag
prints a diff "for each locally modified skill", but the CLI diffs every
installed item whose status is `USER_MODIFIED` or `FORCED`, including the
Antigravity `plugin.json` manifest. Raised as a cosmetic note by both
self-review passes on PR #820.

# Result

- `src/lrh/cli/main.py`: help now reads "print a unified diff for each
  installed item that differs from source".
- Docs (`docs/reference/cli/skills.md`,
  `docs/how-to/keep-skills-up-to-date.md`) were already accurate; no test
  asserts on the help string.
- Prior-art check: no existing WI/backlog entry; the wording originated in
  the resolved `WI-SKILLS-INSTALL-DIFF` and was kept by PR #820.
- Self-review (diff-mode): 0 blocking, 3 low-severity notes; see
  `2026_10_12_06_05_57_SKILLS_INSTALL_DIFF_HELP_WORDING_SELFREVIEW.md`.

# Validation

Per-worktree conda env `IntelligentHopper`:

- `scripts/version tools`: Python 3.11.17, ruff 0.15.12, black 26.3.1
- `scripts/format --check --diff`: 298 files unchanged
- `scripts/lint`: exit 0
- `scripts/test`: 2288 tests, OK
- `lrh validate`: 0 errors, 0 warnings
- `lrh skills install --help`: shows the new wording

# Follow-up

Optional, not filed: a skill directory that is a dangling symlink is
reported `would install` and not diffed (`install_skills` checks only
`dest.exists()`), unlike `plugin.json`.
