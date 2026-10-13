---
execution_id: 2026_10_12_23_28_28_SKILLS_INSTALL_DIFF_HELP_WORDING_REVIEW
prompt_id: PROMPT(AD_HOC:SKILLS_INSTALL_DIFF_HELP_WORDING_REVIEW)[2026-10-12T22:56:29+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_12_06_06_28_SKILLS_INSTALL_DIFF_HELP_WORDING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/832
commit: 4658c53da901bc3e840b101dad7be10bdfce203e
created_at: 2026-10-12T23:28:28+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/832
session_transcript: claude-app:12a73f73-ccc5-4308-abe1-4ceb4827d712
---

# Summary

Review-response round (inline from `/lrh-land`) for PR #832, which rewords
the `lrh skills install --diff` help. Three open comments (one Codex, two
Copilot), all on the same point: `--diff` does not always emit a unified
diff.

# Result

- Fixed — chatgpt-codex-connector (discussion_r4245105480, P2): Antigravity
  `plugin.json` symlink/non-file/non-UTF-8 cases emit one-line notes, not a
  unified diff. Help now says `--diff` reports how each installed item
  differs from source, with a unified diff for changed text files.
- Fixed — copilot-pull-request-reviewer (discussion_r4245105561): same
  point for `diff_skill`'s added/removed/binary/symlink notes; help
  reworded and `docs/reference/cli/skills.md` `--diff` row updated to
  describe both output forms.
- Fixed — copilot-pull-request-reviewer (discussion_r4245105584): the
  primary record's Result claimed the docs were already accurate; corrected
  (pre-merge, record still `in_progress`) to say the reference doc was
  updated, and its quoted help text refreshed.
- Skipped: none. All three re-verified against
  `src/lrh/skills/installer.py` (`diff_skill`,
  `_diff_antigravity_plugin_manifest`). The diff-mode self-review had
  flagged this looseness as a low-severity note that was wrongly treated
  as pre-existing scope.
- Commit `461c54be`.

# Validation

Per-worktree conda env `IntelligentHopper`:

- `scripts/version tools`: Python 3.11.17, ruff 0.15.12, black 26.3.1
- `scripts/format --check --diff`: 298 files unchanged
- `scripts/lint`: exit 0
- `scripts/test`: 2288 tests, OK
- `lrh validate`: 0 errors, 0 warnings
- `lrh skills install --help`: shows the revised wording

# Follow-up

None.
