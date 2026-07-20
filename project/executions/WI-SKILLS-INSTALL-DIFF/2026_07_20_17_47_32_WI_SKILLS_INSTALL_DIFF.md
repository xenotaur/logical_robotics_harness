---
execution_id: 2026_07_20_17_47_32_WI_SKILLS_INSTALL_DIFF
prompt_id: PROMPT(WI-SKILLS-INSTALL-DIFF:WI_SKILLS_INSTALL_DIFF)[2026-07-20T17:37:22-04:00]
work_item: WI-SKILLS-INSTALL-DIFF
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/404
commit: 8d4c3c3
created_at: 2026-07-20T17:47:32-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-INSTALL-DIFF.md
session_transcript: claude-app:f5f46f77-c48c-4f3e-81e3-80cae1c6f5d9
---

# Summary

Implement `WI-SKILLS-INSTALL-DIFF`: add a `--diff` flag to `lrh skills
install` that prints a unified diff of what changed, per file, for every
skill flagged as user-modified.

# Result

- `src/lrh/skills/installer.py`: added `diff_skill()` computing per-file
  diffs (added / removed / changed) between the package and installed skill
  trees via stdlib `difflib.unified_diff`. Added `_collect_fs_symlinks()`
  and updated `_collect_fs_files()` to skip symlinks entirely — symlinked
  paths are detected via `path.is_symlink()` and reported as
  `<path>: symlink — skipped`, never dereferenced. UTF-8 decode failures
  are reported as `<path>: binary files differ`.
- `src/lrh/cli/main.py`: added `--diff` to `skills_install_parser`; wired
  to print `diff_skill()` output for each `USER_MODIFIED` result after
  `format_report`'s existing warning line.
- `tests/skills_installer_test.py`: added `TestDiffSkill` with 6 tests
  (no-change, modified text, added file, removed file, binary file,
  symlinked file — the last asserting the symlink target's contents never
  appear in the diff output).

All acceptance criteria from the work item are met.

# Validation

- `scripts/version tools` — Python 3.11.8, Ruff 0.15.12; Black 25.11.0
  installed (project pins `26.3.1` — pre-existing environment version-pin
  mismatch, confirmed unrelated to this change: see below)
- `scripts/lint` — Ruff: all checks passed (one real line-length violation
  in `installer.py` was caught and fixed during implementation)
- `black --check --diff --required-version 25.11.0 src/lrh/skills/installer.py
  src/lrh/cli/main.py tests/skills_installer_test.py` — all 3 files
  unchanged (diagnostic follow-up confirming the changed files are
  Black-clean at the installed version, since the canonical
  `scripts/format`/`scripts/lint` commands can't pass the version-pin gate
  in this environment)
- `scripts/test` — Ran 791 tests (785 + 6 new) — OK
- `lrh validate` — 0 errors, 0 warnings
- `python -c "import lrh.skills.installer"` — ok
- Manual smoke test: `lrh skills install --diff --local` in a scratch
  `.claude/skills/` directory with a modified, added, removed, and
  symlinked file — confirmed correct output for all four cases, and
  confirmed the symlink target's secret contents never appeared anywhere
  in the output.

# Follow-up

- Update `session_transcript` if this record is ever migrated to a
  different session.
- Once PR #404 merges, closeout should move
  `project/work_items/proposed/WI-SKILLS-INSTALL-DIFF.md` to `resolved/`
  with `resolution:` noting implementation and the merge commit.
