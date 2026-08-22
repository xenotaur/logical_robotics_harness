---
execution_id: 2026_08_22_05_28_12_PROJECT_SLUG_SYMLINK_RESOLUTION
prompt_id: PROMPT(AD_HOC:PROJECT_SLUG_SYMLINK_RESOLUTION)[2026-08-22T05:26:30+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/603
commit: 9a7f49c6283cae918a632e18be32f7583400d7f6
created_at: 2026-08-22T05:28:12+00:00
agent: claude_code
instruction_source: project/work_items/proposed/WI-PROJECT-SLUG-SYMLINK-RESOLUTION.md
session_transcript: claude-app:local_02330303-d423-49f8-9864-aeac6023c0b9
---

# Summary

Filed `WI-PROJECT-SLUG-SYMLINK-RESOLUTION`: fix `project_slug_for_path()`
(`src/lrh/prompt_workflow_sessions.py:565-582`) to stop resolving symlinks
when computing a Claude Code project slug, following up on a Copilot/Codex
review finding from PR #599 that was verified to hold against Claude Code's
real, observed bucket-naming behavior.

# Result

Confirmed empirically that `.expanduser().resolve()` in
`project_slug_for_path()` follows symlinks while Claude Code's actual
bucket-naming does not, using this repo's own two independently-populated
`~/.claude/projects/` buckets (old symlinked path vs. new real path) as a
live example. Reviewed git history to confirm the symlink-following was an
unexamined side effect of `.resolve()`, not a deliberate design choice, and
that no existing test or work item covers the symlink case. Wrote work item
`WI-PROJECT-SLUG-SYMLINK-RESOLUTION` (`project/work_items/proposed/`) with
full frontmatter, prior-art check, and body sections, and opened
[PR #603](https://github.com/xenotaur/logical_robotics_harness/pull/603).

# Validation

- `lrh validate` — 0 errors, 0 warnings.

# Follow-up

- Implementation is a separate follow-up (`/lrh-implement` or
  `/lrh-execute` against `WI-PROJECT-SLUG-SYMLINK-RESOLUTION`).
- `session_transcript` above is `pending` and should be updated to the
  durable session pointer once available.
