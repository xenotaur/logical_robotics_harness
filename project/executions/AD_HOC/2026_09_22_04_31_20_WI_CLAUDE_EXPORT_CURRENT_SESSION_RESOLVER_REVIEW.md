---
execution_id: 2026_09_22_04_31_20_WI_CLAUDE_EXPORT_CURRENT_SESSION_RESOLVER_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CLAUDE_EXPORT_CURRENT_SESSION_RESOLVER_REVIEW)[2026-09-22T04:24:51+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_22_04_18_58_WI_CLAUDE_EXPORT_CURRENT_SESSION_RESOLVER
pr: https://github.com/xenotaur/logical_robotics_harness/pull/698
commit: 
created_at: 2026-09-22T04:31:20+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/698
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Review-response round 1 for PR #698 (`WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`),
entered from `/lrh-land` Step 4. Four open review threads on `22841420`, from
both chatgpt-codex-connector and copilot-pull-request-reviewer.

# Result

All four comments were present and valid, and all were fixed:

- **chatgpt-codex-connector — fixed.** `--latest` scoping used
  `os.getcwd()`, which resolves symlinks away, while `project_slug_for_path`
  intentionally preserves the literal path (matching Claude Code's own
  bucket naming). Under a symlinked checkout this searches the wrong project
  bucket or reports it missing — the same issue this session hit firsthand
  while testing under macOS's `/tmp`. Added `_logical_cwd()` in
  `claude_export.py`: prefers `$PWD` when `os.path.samefile()` confirms it
  names the same directory as the physical cwd, else falls back to
  `os.getcwd()`.
- **copilot (isolated `CLAUDE_CONFIG_DIR`) — fixed.**
  `resolve_current_claude_session_identity`'s `environ=` covered the session
  IDs but not the app-data-dir default, which still read the real
  `os.environ`. Now resolves `CLAUDE_CONFIG_DIR` from the already-resolved
  `env` mapping.
- **copilot (`Path.expanduser()` RuntimeError) — fixed.** An unresolved
  named-user path (e.g. `~missing-user/.claude`) let a raw `RuntimeError`
  escape. Now caught in `resolve_transcript_path_by_session_id` and
  re-raised as `ClaudeSessionIdentityError`, matching the established
  `_expand_user_path` pattern in `claude_export.py`.
- **copilot (`Path.glob` matches directories) — fixed.** A directory named
  `<session_id>.jsonl` was silently accepted as the transcript. Matches are
  now filtered to `is_file()`. Noted, not fixed: `claude_export.py`'s own
  pre-existing `--session-id` glob branch has the same gap; it is untouched
  by this diff and the comment targeted only the new code, so it was left
  as an observation rather than expanded scope.

# Validation

- `scripts/format --check --diff` and `scripts/lint` — clean.
- `PYTHONPATH=src scripts/test` — 1682 tests OK (anaconda Python, Homebrew
  bash 5).
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Re-run `/lrh-confirm-fixes` for PR #698.
- Consider a follow-up to apply the same `is_file()` filter to
  `claude_export.py`'s pre-existing `--session-id` glob branch.
