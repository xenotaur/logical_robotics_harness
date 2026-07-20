---
execution_id: 2026_07_20_01_05_08_WI_SKILLS_INSTALL_DIFF_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_INSTALL_DIFF_REVIEW)[2026-07-20T00:59:18-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/402
commit: c797783
created_at: 2026-07-20T01:05:08-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/402
session_transcript: pending
---

# Summary

Address open review comments on PR #402 (`WI-SKILLS-INSTALL-DIFF`
work-item filing) from `chatgpt-codex-connector` and
`copilot-pull-request-reviewer`.

# Result

Both comments passed triage (present, valid, feasible) and were fixed by
editing `project/work_items/proposed/WI-SKILLS-INSTALL-DIFF.md` — this PR
only contains a planning artifact, so both fixes are document edits rather
than code changes:

1. **Symlink-following risk** (`chatgpt-codex-connector`, P2): the WI's
   Required Changes didn't account for `_collect_fs_files` following
   symlinks via `path.is_file()` / `read_bytes()` (`installer.py:60-62`),
   which a future `--diff` implementation would expose by printing a
   symlink target's contents in diff output under an untrusted `--local`
   checkout. Added an explicit symlink-detection requirement to Required
   Changes item 1, a matching bullet to Acceptance Criteria (body +
   frontmatter), a symlink test case to the planned test list, and a new
   Risk Notes bullet documenting the concern for the future implementer.
2. **Non-durable phrasing** (`copilot-pull-request-reviewer`): the
   Problem/Context paragraph referenced "(this session)" and claimed the
   PATH fragility of external binaries was "documented" without a citable
   source. Reworded to drop the session-relative phrase and to justify the
   `difflib` choice on its own portability merits (no external-binary
   dependency) instead of an uncited claim.

# Validation

- `git rev-parse HEAD` — c797783
- `scripts/version tools` — Python 3.11.8, Ruff 0.15.12, Black 25.11.0
  installed (project pins Black 26.3.1; version mismatch is a pre-existing
  environment issue, not a regression — no Python files are touched by this
  change)
- `scripts/format --check --diff` — fails only on the Black version-pin
  mismatch above; not applicable to this change (Markdown-only diff)
- `scripts/lint` — Ruff: all checks passed; Black check fails for the same
  pre-existing version-pin reason
- `scripts/test` — Ran 785 tests in 46.330s — OK
- `lrh validate` — 0 errors, 0 warnings
- `lrh work-items validate` — 0 errors; 6 pre-existing warnings on unrelated
  resolved WIs, none referencing WI-SKILLS-INSTALL-DIFF

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  this session ends.
- Once PR #402 merges, closeout should move
  `project/work_items/proposed/WI-SKILLS-INSTALL-DIFF.md` — but note it
  stays in `proposed/` (the PR only files the planning artifact; the WI
  itself resolves only once the `--diff` feature is implemented).
