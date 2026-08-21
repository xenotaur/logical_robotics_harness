---
execution_id: 2026_08_21_17_21_02_WI_LRH_MEMORY_PORTABILITY
prompt_id: PROMPT(WI-LRH-MEMORY-PORTABILITY:WI_LRH_MEMORY_PORTABILITY)[2026-08-21T16:20:35+00:00]
work_item: WI-LRH-MEMORY-PORTABILITY
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/589
commit: c2672f22a3ed2465d9e81b14b97db09dac978959
created_at: 2026-08-21T17:21:02+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-PORTABILITY.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Implemented `lrh memory export`/`import`/`transfer` (`WI-LRH-MEMORY-PORTABILITY`),
the portability surface for moving curated memories between corpora
(`PROP-LRH-MEMORY-COMMAND` Decision 8). Run via `/lrh-execute
WI-LRH-MEMORY-PORTABILITY`, inlining `/lrh-implement`.

# Result

- Both of the WI's own Open Questions were resolved at the chain
  authorization gate before implementation started: export/transfer
  require an explicit `--name`/`--agent` filter (no unfiltered "all"
  default); bundle format is JSONL.
- `export_memories()`, `import_memories()`, `transfer_memories()`
  implemented in `prompt_workflow_memory.py`; CLI wiring in
  `memory_workflow.py`.
- `write_memory`/`list_memories` refactored into
  `_write_memory_into_dir`/`_list_memories_in_dir` cores + thin
  `project_root`-based public wrappers, enabling `import`/`transfer` to
  reuse the exact validated write/read path without any behavior change
  to the existing `write`/`list`/`sync`/`repair` commands.
- Pre-push `/lrh-self-review` diff-mode pass (see
  `project/executions/AD_HOC/2026_08_21_17_19_35_WI_LRH_MEMORY_PORTABILITY_SELFREVIEW.md`):
  found and fixed a real HIGH-severity path-escape bug in
  `_resolve_memory_dir` (pathlib's `/` operator silently discards its left
  operand for an absolute right operand, letting `transfer` write outside
  `claude_projects_root`), plus a missing exception-handling gap in
  `import`'s CLI wiring. Both independently re-verified.
- Opened PR #589.

# Validation

`scripts/version tools`, `lrh validate` (0 errors/warnings),
`scripts/format --check --diff`, `scripts/lint`, `scripts/test` (1240
tests, all pass), `lrh memory transfer --help`. New unit tests
(`ExportMemoriesTest`, `ImportMemoriesTest`, `TransferMemoriesTest`, 15
cases total including a direct regression test for the path-escape fix)
and CLI tests (5 cases) cover export/import/transfer end-to-end.

# Follow-up

- Awaiting reviewer response / merge via `/lrh-land`.
- `WI-LRH-MEMORY-READ-SIDE` remains proposed, no dependency on this item.
- This completes 3 of 4 `WS-LRH-MEMORY-COMMAND` work items on merge.
