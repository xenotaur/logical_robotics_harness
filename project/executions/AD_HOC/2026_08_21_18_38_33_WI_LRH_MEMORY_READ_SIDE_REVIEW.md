---
execution_id: 2026_08_21_18_38_33_WI_LRH_MEMORY_READ_SIDE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_READ_SIDE_REVIEW)[2026-08-21T18:37:56+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_21_18_32_00_WI_LRH_MEMORY_READ_SIDE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/594
commit: 4acd447ecc1035574c58de440685ebe56d081c63
created_at: 2026-08-21T18:38:33+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/594
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Round 1 review-response for PR #594, addressing 1 P2 finding from
`chatgpt-codex-connector` on the initial push.

# Result

Triaged as present, valid, and feasible: `search_memories` silently
skipped any memory file that failed `read_frontmatter_and_body`,
excluding exactly the legacy/malformed population `lrh memory search`
exists to help inspect and repair -- a query matching only that file's
raw content reported zero matches even though the text was really there.
Fixed by falling back to searching the raw file content as a single
opaque blob when frontmatter parsing fails, but only when no
`--agent`/`--type` filter was requested (unanswerable without valid
metadata, so such files remain excluded when a filter is set). Added two
regression tests (found-via-raw-content, correctly-excluded-under-filter).

Independently re-verified against the actual code before fixing (not
accepted from the bot report alone).

Pushed directly: `git push` to the open PR branch.

# Validation

`scripts/format --check --diff`, `scripts/lint`, `lrh validate` (0
errors/warnings), full `scripts/test` suite (1261 tests, all pass).

# Follow-up

- Loop back to confirm-fixes for a fresh verdict against this new
  `HEAD`.
