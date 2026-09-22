---
execution_id: 2026_09_22_04_18_58_WI_CLAUDE_EXPORT_CURRENT_SESSION_RESOLVER
prompt_id: PROMPT(WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER:WI_CLAUDE_EXPORT_CURRENT_SESSION_RESOLVER)[2026-09-22T02:09:56+00:00]
work_item: WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/698
commit: 
created_at: 2026-09-22T04:18:58+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Implement `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER` through `/lrh-execute`:
give the Claude exporter a metadata-only current-session resolver, a
non-guessing `--current` discovery flag, a project-scoped `--latest`, and a
`Source transcript:` output line.

# Result

- New `src/lrh/conversations/claude_session.py`, modelled on `codex_session.py`:
  `resolve_current_claude_session_identity` reads `CLAUDE_CODE_SESSION_ID`
  (required) and `CLAUDE_CODE_HOST_SESSION_ID` (optional, `local_` stripped,
  `claude-app:<uuid>`), and globs `<app-data-dir>/projects/*/<id>.jsonl` for
  the transcript path. Never reads transcript content. Fails clearly, never
  guesses, on an unset id or a zero/multi-match glob. New
  `lrh conversation current-claude-session-id` CLI, `--format text|json`,
  `--field`.
- `export-claude-session` gained `--current` as a fourth member of the
  required discovery group, resolved through the same function; on failure it
  raises, it never falls back to `--latest`.
- `_resolve_transcript_path`'s `latest` branch is now scoped by default to
  `<app-data-dir>/projects/<project_slug_for_path(cwd)>/`; `--all-projects`
  restores the old `projects/*/*.jsonl` glob and is rejected when passed
  without `--latest`. The silent tie-break is unchanged.
- `Source transcript: <path>` is printed on every successful export.
- `docs/reference/cli/conversation.md`: a new `current-claude-session-id`
  section, and updates to `export-claude-session`'s discovery, options, and
  exit-behavior sections.
- Registered in `src/lrh/cli/main.py` and exported from
  `src/lrh/conversations/__init__.py`.

Verified during implementation: no existing code read either environment
variable before this change (confirmed by grep). Both variables are set in
this Claude desktop app session (`CLAUDE_CODE_ENTRYPOINT=claude-desktop`),
used as a live smoke test. Their availability under a plain CLI invocation or
an IDE integration could not be tested from this environment — documented as
unverified in the CLI reference rather than assumed; the resolver's
fail-clearly behavior does not depend on the answer. The only existing caller
of `export-claude-session --latest` is the `/lrh-export-claude` skill's own
Step 1, which always forwards `--transcript-path` it derived itself, never
`--latest` — so the scoping change has no effect on current skill behavior
(`WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` replaces that step).

Pre-push diff-mode self-review (`_SELFREVIEW` record) found two minor gaps,
both fixed before this push: `CLAUDE_HOST_SESSION_ID_ENV` was not re-exported
from `lrh.conversations.__init__` alongside its sibling constant; and
`--all-projects` silently no-opped when passed without `--latest` (now
rejected with a clear error).

# Validation

- `PYTHONPATH=src scripts/test` — 1676 tests OK. Anaconda Python, Homebrew
  bash 5 (stock macOS bash 3.2 breaks two unrelated scripts on an empty-array
  `set -u`, unrelated to this change).
- `scripts/lint` and `scripts/format --check --diff` — clean.
- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Proceed to `/lrh-land` for PR #698.
- `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT` can now proceed; it
  depends on both this item and `WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY`.
- Whether `CLAUDE_CODE_SESSION_ID`/`CLAUDE_CODE_HOST_SESSION_ID` are available
  outside the desktop app remains genuinely open.
