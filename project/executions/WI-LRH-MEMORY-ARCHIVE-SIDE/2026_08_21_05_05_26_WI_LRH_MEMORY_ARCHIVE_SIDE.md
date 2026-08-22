---
execution_id: 2026_08_21_05_05_26_WI_LRH_MEMORY_ARCHIVE_SIDE
prompt_id: PROMPT(WI-LRH-MEMORY-ARCHIVE-SIDE:WI_LRH_MEMORY_ARCHIVE_SIDE)[2026-08-21T04:45:00+00:00]
work_item: WI-LRH-MEMORY-ARCHIVE-SIDE
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/583
commit: f37672d4363842bd0b574076d3343e6926f5afc5
created_at: 2026-08-21T05:05:26+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-ARCHIVE-SIDE.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Implemented `lrh memory sync` (`WI-LRH-MEMORY-ARCHIVE-SIDE`), closing the
archive-side gap: `lrh sessions sync` mirrors transcripts but never touches
`memory/`. Run via `/lrh-execute WI-LRH-MEMORY-ARCHIVE-SIDE`, inlining
`/lrh-implement`.

# Result

- Generalized `mirror_transcript` into a shared `mirror_file_with_snapshot`
  primitive (`prompt_workflow_sessions.py`), implementing content-hash
  comparison and snapshot-before-overwrite (Decision 6), purely additive --
  `mirror_transcript`/`lrh sessions sync` behavior untouched, confirmed by
  re-running the full sessions test suite unchanged.
- Implemented `lrh memory sync` (`prompt_workflow_memory.py`,
  `memory_workflow.py`) as an independent subcommand (Decision 5), mirroring
  `<slug>/memory/**/*.md` into `<archive_root>/raw/<slug>/memory/**`,
  matching `sessions sync`'s flag shape.
- Pre-push `/lrh-self-review` diff-mode pass (see
  `project/executions/AD_HOC/2026_08_21_05_04_07_WI_LRH_MEMORY_ARCHIVE_SIDE_SELFREVIEW.md`):
  no findings, independently re-verified.
- Opened PR #583.

# Validation

`scripts/version tools`, `lrh validate` (0 errors/warnings),
`scripts/format --check --diff`, `scripts/lint`, `scripts/test` (1182 tests,
all pass), `lrh memory sync --dry-run` (manual scratch-corpus verification).
New unit tests (`SyncMemoryTest`, 6 cases) and CLI tests (2 cases) cover
mirror/no-op/snapshot/shrink/dry-run/empty-corpus behavior.

# Follow-up

- Awaiting reviewer response / merge via `/lrh-land`.
- `WI-LRH-MEMORY-READ-SIDE` and `WI-LRH-MEMORY-PORTABILITY` remain proposed;
  `PORTABILITY` depends on this item and will unblock on merge.
