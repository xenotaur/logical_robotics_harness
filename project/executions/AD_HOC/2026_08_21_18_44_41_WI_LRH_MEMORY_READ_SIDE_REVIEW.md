---
execution_id: 2026_08_21_18_44_41_WI_LRH_MEMORY_READ_SIDE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_READ_SIDE_REVIEW)[2026-08-21T18:44:02+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_21_18_32_00_WI_LRH_MEMORY_READ_SIDE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/594
commit: 4acd447ecc1035574c58de440685ebe56d081c63
created_at: 2026-08-21T18:44:41+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/594
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Round 2 review-response for PR #594, addressing 4 `copilot-pull-request-reviewer`
findings surfaced on the initial push.

# Result

All four triaged as present, valid, and feasible:

1. `read_memory` didn't reject a symlinked corpus entry -- `_validate_name`
   blocks path traversal via the `name` argument, but a symlink placed
   directly in the corpus (`feedback-x.md -> /etc/passwd`) bypasses that
   entirely, since `Path.read_text()` follows symlinks by default. Fixed
   by rejecting `path.is_symlink()` explicitly.
2. `search_memories` had the same symlink-following gap in its glob loop
   -- fixed by skipping (not raising, to preserve "one bad entry doesn't
   abort the search") symlinked entries.
3. `search_memories`'s per-file read only caught `MemoryValidationError`,
   so an unreadable or non-UTF-8 `*.md` file aborted the whole search
   instead of being skipped like the existing execution-record search's
   own resilience. Fixed.
4. `lrh memory read --format json` could crash with `TypeError` on a
   memory whose frontmatter contains a YAML timestamp/date (parsed by
   `yaml.safe_load` into a `datetime` object, which `json.dumps` can't
   serialize by default). Fixed with `default=str`. Also fixed the
   adjacent gap of `_run_read` only catching `MemoryValidationError`, not
   `OSError`/`UnicodeDecodeError`.

All four independently re-verified against the actual code before
fixing (not accepted from the bot report alone).

Pushed directly: `git push` to the open PR branch.

# Validation

`scripts/format --check --diff`, `scripts/lint`, `lrh validate` (0
errors/warnings), full `scripts/test` suite (1266 tests, all pass).

# Follow-up

- Loop back to confirm-fixes for a fresh verdict against this new
  `HEAD`.
