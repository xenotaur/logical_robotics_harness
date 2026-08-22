---
execution_id: 2026_08_21_05_13_49_WI_LRH_MEMORY_ARCHIVE_SIDE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_ARCHIVE_SIDE_REVIEW)[2026-08-21T05:13:21+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_21_05_05_26_WI_LRH_MEMORY_ARCHIVE_SIDE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/583
commit: f37672d4363842bd0b574076d3343e6926f5afc5
created_at: 2026-08-21T05:13:49+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/583
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Round 1 review-response for PR #583 (`WI-LRH-MEMORY-ARCHIVE-SIDE`),
addressing two `chatgpt-codex-connector` P2 findings on the initial push.

# Result

Both findings triaged as present, valid, and feasible:

1. **Serialize snapshot-before-overwrite operations** -- two overlapping
   `lrh memory sync` processes racing a fast-changing source could both
   snapshot the same prior content and race the final write, silently
   dropping an intermediate version. Fixed by wrapping
   `mirror_file_with_snapshot`'s read-compare-snapshot-write sequence in a
   new per-destination `fcntl.flock`-based lock (`_locked_dest`), the same
   pattern `prompt_workflow_memory._locked_index` already uses for the
   analogous `MEMORY.md` index race.
2. **Reject archive roots nested under the memory corpus** -- an
   `--archive-root` inside (or containing) the memory corpus would have its
   own mirrored output picked up by the next run's `rglob("*.md")`,
   re-mirroring it one level deeper every run without ever converging.
   Fixed by rejecting either nesting direction in `sync_memory` with a
   clear `MemoryValidationError` before any file is touched.

Both were independently re-verified against the actual code (not
accepted from the bot report alone) before fixing.

Pushed directly: `git push` to the open PR branch.

# Validation

`scripts/version tools`, `scripts/format --check --diff`, `scripts/lint`,
`scripts/test` (full suite, 1185 tests, all pass), `lrh validate` (0
errors/warnings). Added 3 regression tests: nested-archive-root-either-
direction (2 cases) and a concurrent-sync test asserting the final state
retains the latest content with the prior version snapshotted, not dropped.

# Follow-up

- Awaiting fresh automated review of this commit before the merge gate
  (REVIEW-LANDED re-check).
