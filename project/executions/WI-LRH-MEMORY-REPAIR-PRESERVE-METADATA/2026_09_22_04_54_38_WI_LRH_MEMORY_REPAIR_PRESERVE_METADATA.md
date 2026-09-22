---
execution_id: 2026_09_22_04_54_38_WI_LRH_MEMORY_REPAIR_PRESERVE_METADATA
prompt_id: PROMPT(WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA:WI_LRH_MEMORY_REPAIR_PRESERVE_METADATA)[2026-09-22T03:51:33+00:00]
work_item: WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/702
commit: 
created_at: 2026-09-22T04:54:38+00:00
agent: claude_app
instruction_source: project/work_items/resolved/WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA.md
session_transcript: pending
---

# Summary

Implemented WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA via /lrh-execute: `lrh memory repair` now preserves frontmatter keys outside its own schema, byte-for-byte, instead of silently dropping them.

# Result

- src/lrh/prompt_workflow_memory.py: `_extract_preserved_frontmatter_lines()` (with helper `_consume_frontmatter_block()`) splits a memory's raw frontmatter into canonical vs. preserved lines, split by nesting depth (top-level vs. metadata-nested) so they can be re-spliced at the correct position; `_render_memory_file()` renders the top-level and metadata dicts separately and splices preserved lines into each at the right depth; `repair_memory()` computes and threads them through. `write_memory`/`_write_memory_into_dir` accept (but default to empty) the same parameters, so ordinary write/import/transfer callers are unaffected.
- Confirmed by inspection (per Scope): `write`, `import`, and `transfer` all funnel through the same `_render_memory_file`, so an overwrite via any of them has the same latent key-loss as `repair` had; not fixed here (out of scope), noted for a possible follow-up.
- Conservative by design: a value that spans multiple lines (block sequence/scalar), a `metadata:` line with inline flow-mapping content, or a duplicate key in the source raises `MemoryValidationError` rather than guessing and risking a second, subtler data-loss bug.
- Five rounds of independent cold self-review during implementation each found and fixed one real, verified defect (mixed-position line ordering producing unparseable output; a same-indent block sequence silently dropped; a blank line inside a sequence or after a null scalar mishandled; a comment line reproducing the same failure mode; a duplicate key silently collapsing to its last value) — all before this was ever pushed.
- Tests: reproduction of the original bug (fails without the fix), byte-for-byte timestamp preservation, canonical-only byte-identical output, and one test per edge case found during self-review.
- docs/reference/cli/memory.md and Decision 9 of the adopted proposal updated.

# Validation

scripts/format --check --diff, scripts/lint, scripts/test (1668 tests, OK), lrh validate (0 errors, 0 warnings) — all pass.

# Follow-up

- Consider fixing the same key-loss in write/import/transfer's overwrite path (out of scope for this WI).
- Back up the real memory corpus (lrh memory sync + tar) and backfill authored_by on the 14 legacy Claude-Code-auto-memory files using this fixed repair.
