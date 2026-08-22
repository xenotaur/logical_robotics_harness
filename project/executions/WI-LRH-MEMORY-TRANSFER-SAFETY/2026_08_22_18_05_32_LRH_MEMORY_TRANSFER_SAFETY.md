---
execution_id: 2026_08_22_18_05_32_LRH_MEMORY_TRANSFER_SAFETY
prompt_id: PROMPT(WI-LRH-MEMORY-TRANSFER-SAFETY:LRH_MEMORY_TRANSFER_SAFETY)[2026-08-22T17:05:59+00:00]
work_item: WI-LRH-MEMORY-TRANSFER-SAFETY
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/606
commit: f5a2028e
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-TRANSFER-SAFETY.md
session_transcript: pending
created_at: 2026-08-22T18:05:32+00:00
---

# Summary

Implemented WI-LRH-MEMORY-TRANSFER-SAFETY: fixed `lrh memory transfer`'s
silent no-op on a bare relative `--from` path, and added a `--force` +
history-snapshot guard to `transfer`/`import`'s overwrite of a same-agent
or legacy (no `authored_by`) destination memory.

# Result

- `_resolve_memory_dir` itself was left untouched (per Risk Notes --
  changing its public contract was flagged as risky); instead
  `transfer_memories` now raises a clear `MemoryValidationError` when
  `--from` resolves to a corpus directory that does not exist, before
  ever reaching export/import -- closing the silent `0 written, 0
  errors` no-op without touching `--to`'s legitimate fresh-corpus case.
- Added `_guard_import_overwrite`, called only from
  `_import_records_into_dir` (the shared call site for both
  `import_memories` and `transfer_memories`) -- `_write_memory_into_dir`
  itself, and therefore `write_memory`'s own same-agent overwrite
  behavior, is unchanged. The guard requires `--force` before
  overwriting a destination whose `authored_by` matches the incoming
  agent or is absent (legacy), and snapshots the destination's prior
  content into `<memory_dir>/history/` (content-hash-keyed, mirroring
  `sync`'s own snapshot convention) before the overwrite proceeds.
  Genuine cross-agent conflicts are left to `_write_memory_into_dir`'s
  own pre-existing check, unchanged.
- Updated `import --force`'s and `transfer --force`'s CLI help text in
  `memory_workflow.py` to describe the new semantics.
- A diff-mode `/lrh-self-review` pass (dispatched before this PR was
  opened) found one real HIGH-severity finding: the new guard built a
  filesystem path from a bundle record's `name` field and read whatever
  it found there *before* that name was validated as a safe kebab-case
  slug -- a crafted `import` bundle with `name:
  "../../../secret_area/evil_target"` could read an arbitrary file
  outside the destination corpus and copy its content into
  `memory/history/` as a side effect, even though the record was
  ultimately rejected with an innocuous-looking "not a valid slug"
  error. I independently reproduced this directly (confirmed the leak,
  then confirmed the fix closes it) before applying the fix: `name` is
  now validated via `_validate_name` before the guard runs, so no
  filesystem access happens on an unvalidated name.

# Validation

- `scripts/version tools`: Black/Ruff report a version-pin mismatch
  (running 25.11.0/0.15.0 vs. required 26.3.1/0.15.12) -- confirmed
  identical, pre-existing environment drift on `origin/main` tip, not
  introduced by this change. Actual formatting/lint compliance verified
  directly (`black --check --config /dev/null`, `ruff check --isolated`
  against the 4 changed files) -- both clean.
- `scripts/test`: 1289 tests, all pass (`PYTHONPATH=src` required in
  this checkout -- its editable pip install points at an unrelated
  checkout elsewhere on disk).
- `lrh validate`: 0 errors, 0 warnings.
- `lrh memory transfer --help` / `lrh memory import --help`: confirmed
  updated help text.
- Diff-mode self-review: 1 HIGH finding (path traversal, above), fixed
  and re-verified clean; re-ran full validation after the fix.

# Follow-up

- `session_transcript: pending` -- update to the durable Claude.app
  session pointer once available.
- Wait for reviewer comments and run `/lrh-review-response` /
  `/lrh-confirm-fixes` before merge, then `/lrh-closeout` to land the
  execution record and resolve WI-LRH-MEMORY-TRANSFER-SAFETY.
