---
execution_id: 2026_08_22_19_44_09_WI_LRH_MEMORY_TRANSFER_SAFETY_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_TRANSFER_SAFETY_IMPL_REVIEW)[2026-08-22T19:30:15+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_22_18_05_32_LRH_MEMORY_TRANSFER_SAFETY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/606
commit: 9ebce5029ddeeaf2aa018cd099a034d9f1272d9d
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/606
session_transcript: claude-app:937464f4-d02a-4285-9bbf-f8411ebb09fe
created_at: 2026-08-22T19:44:09+00:00
---

# Summary

Address 4 review comments on PR #606 (Codex x3, Copilot x1), all
converging on the same overwrite-guard code added for
WI-LRH-MEMORY-TRANSFER-SAFETY's Bug 2 fix.

# Result

- **Codex** (`#discussion_r3836676679`) / **Copilot**
  (`#discussion_r3836676895`) -- fixed. A destination with malformed or
  unreadable frontmatter (or non-UTF-8 bytes) previously blocked a
  forced overwrite entirely -- a regression against
  `_write_memory_into_dir`'s own pre-existing behavior, which skips
  parsing the destination when `force=True`. `_guard_import_overwrite`
  now catches the parse/decode failure, treats the destination the same
  as a legacy record (requires `--force`, no different), and snapshots
  its raw bytes (not a parsed re-render) before permitting the
  overwrite.
- **Codex** (`#discussion_r3836676683`) -- fixed. Added
  `_locked_memory_path`, a per-destination-path `fcntl.flock` (mirroring
  `_locked_index`'s and `prompt_workflow_sessions._locked_dest`'s own
  pattern), and moved the guard call and the subsequent
  `_write_memory_into_dir` call inside it as one atomic
  read-snapshot-write unit. Verified with a new concurrency test
  (`test_transfer_concurrent_forced_overwrites_never_drop_a_version`) --
  two threads racing a forced transfer into the same destination now
  always preserve both the original and the losing thread's version in
  `history/`.
- **Codex** (`#discussion_r3836676686`) -- fixed. Snapshot filenames are
  now keyed by content hash only (dropped the timestamp component,
  which defeated the guard's own stated dedup intent), and the guard
  pre-renders the exact bytes the incoming write would produce,
  comparing them against the destination's current content -- a
  genuine no-op now skips the snapshot (and the whole guard) entirely,
  rather than creating a new identical-content file on every repeated
  `--force` run.

All four converge on the same three code changes in
`_guard_import_overwrite` and its call site in
`_import_records_into_dir` (`src/lrh/prompt_workflow_memory.py`).

# Validation

- `scripts/test` / targeted modules: 1292 (full) / 99 (targeted) tests,
  all pass, including 3 new regression tests for these findings plus
  the existing concurrency-test pattern already established for `sync`.
- `black --check --config /dev/null` / `ruff check --isolated` against
  changed files: clean (bypassing this environment's known,
  pre-existing black/ruff version-pin mismatch, confirmed unrelated to
  this change).
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Suggest running `/lrh-confirm-fixes` against this PR before merge.
