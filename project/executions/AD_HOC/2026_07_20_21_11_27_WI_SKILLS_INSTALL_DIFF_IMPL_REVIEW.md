---
execution_id: 2026_07_20_21_11_27_WI_SKILLS_INSTALL_DIFF_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_INSTALL_DIFF_IMPL_REVIEW)[2026-07-20T20:40:57-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_20_17_47_32_WI_SKILLS_INSTALL_DIFF
pr: https://github.com/xenotaur/logical_robotics_harness/pull/404
commit: 0435c75
created_at: 2026-07-20T21:11:27-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/404
session_transcript: claude-app:f5f46f77-c48c-4f3e-81e3-80cae1c6f5d9
---

# Summary

Address 5 open review comments on PR #404 (`WI-SKILLS-INSTALL-DIFF`
implementation) from `chatgpt-codex-connector` and
`copilot-pull-request-reviewer`, all converging on one real gap: a
symlinked skill *root* (not just a nested symlinked file) was not guarded
against.

# Result

All 5 comments passed triage (present, valid, feasible) and reduce to two
distinct fixes in `src/lrh/skills/installer.py`:

1. **Root-symlink not checked** (`chatgpt-codex-connector` P1;
   `copilot-pull-request-reviewer` x2; the shipped code only checked
   `path.is_symlink()` on *entries* returned by `directory.rglob("*")` —
   if `directory` itself (the installed skill root) was a symlink,
   `rglob()` still traversed into its target, and both
   `_skill_differs_from_package()` and `diff_skill()` would read/diff
   files from outside the skills directory. Fixed by checking
   `directory.is_symlink()` up front in `_collect_fs_files()` and
   `_collect_fs_symlinks()` (return empty rather than traverse), and by
   adding an explicit early-return message in `diff_skill()`
   ("installed skill directory is a symlink — skipped").
2. **Added nested symlink not counted as a modification**
   (`chatgpt-codex-connector` P2): since symlinks are excluded from both
   `pkg_files` and `fs_files`, a skill that otherwise matches the package
   but has one added symlink compared byte-dicts as equal, misclassifying
   as `UP_TO_DATE` — meaning `--diff` never even ran for it. Fixed by
   having `_skill_differs_from_package()` also treat a non-empty
   `_collect_fs_symlinks()` result as a modification.
3. **Missing regression test coverage**
   (`copilot-pull-request-reviewer`): added 3 tests —
   `test_symlinked_skill_root_detected_as_user_modified`,
   `test_diff_symlinked_skill_root_not_dereferenced`, and
   `test_diff_nested_added_symlink_counts_as_modified` — each asserting
   correct classification/messaging and that no secret target content
   ever appears in output.

Also manually smoke-tested live via the CLI (not just unit tests): replaced
an installed skill directory with a symlink to an external directory
containing a `SKILL.md` with marker text `TOP-SECRET-ROOT-CONTENTS`;
confirmed `lrh skills install --local` reports it as user-modified (not
up to date) and `--diff` reports the symlink-root message with the marker
text never appearing in output.

# Validation

- `scripts/lint` — Ruff: all checks passed
- `black --check --diff --required-version 25.11.0 src/lrh/skills/installer.py
  tests/skills_installer_test.py` — both files unchanged (canonical
  `scripts/format`/`scripts/lint` still can't pass this environment's
  pre-existing Black version-pin gate: 25.11.0 installed vs. 26.3.1
  required, unrelated to this change)
- `scripts/test` — Ran 794 tests (791 + 3 new) — OK
- `lrh validate` — 0 errors, 0 warnings
- `python -c "import lrh.skills.installer"` — ok
- Manual live CLI smoke test (symlinked skill root) — see Result above

# Follow-up

- Update `session_transcript` if this record is ever migrated to a
  different session (currently carries this session's real ID already).
- Once PR #404 merges, closeout should move
  `project/work_items/proposed/WI-SKILLS-INSTALL-DIFF.md` to `resolved/`.
