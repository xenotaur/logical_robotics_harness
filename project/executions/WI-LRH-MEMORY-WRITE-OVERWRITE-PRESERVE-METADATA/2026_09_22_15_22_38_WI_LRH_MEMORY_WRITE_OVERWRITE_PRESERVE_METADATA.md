---
execution_id: 2026_09_22_15_22_38_WI_LRH_MEMORY_WRITE_OVERWRITE_PRESERVE_METADATA
prompt_id: PROMPT(WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA:WI_LRH_MEMORY_WRITE_OVERWRITE_PRESERVE_METADATA)[2026-09-22T14:57:46+00:00]
work_item: WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/714
commit: dedaa7d95ab74aee27a69146a8c83c8432f90125
created_at: 2026-09-22T15:22:38+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA.md
session_transcript: claude-app:239809db-0aff-4cae-b00b-76078ee01394
---

# Summary

Implemented WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA via /lrh-execute: write/import/transfer now preserve unknown frontmatter keys on overwrite and (for import/transfer) new-file writes; repair no longer writes to the wrong file; lrh memory validate gained a name_mismatch finding.

# Result

- src/lrh/prompt_workflow_memory.py: _write_memory_into_dir auto-derives preserved lines on overwrite (force-independent for preservation, force-gated only for the pre-existing cross-agent check); _export_records_from_dir/_import_records_into_dir carry preserved_top_level_lines/preserved_metadata_lines through the bundle; new _merge_preserved_lines() reconciles destination vs. incoming extras on overwrite; repair_memory always writes back to the file it opened (merged_name = slug, not frontmatter.get("name")); validate_corpus gained an independent name_mismatch field.
- Live-discovered and fixed in the same change: export_memories crashed outright on a memory whose metadata included a YAML timestamp (json.dumps can't serialize the datetime yaml.safe_load parses it into) -- the bundle's metadata field is now canonical-keys-only, always JSON-safe.
- One round of independent cold self-review during implementation: no defects found; its one coverage suggestion (write force + cross-agent reconciliation) was added as a test.
- Tests: one regression test per bug (8 new tests total), each verified to fail against the pre-fix source before the fix landed.

# Validation

scripts/format --check --diff, scripts/lint, scripts/test (1722 tests, OK), lrh validate (0 errors, 0 warnings) -- all pass.

# Follow-up

- Update session_transcript from pending at closeout.
