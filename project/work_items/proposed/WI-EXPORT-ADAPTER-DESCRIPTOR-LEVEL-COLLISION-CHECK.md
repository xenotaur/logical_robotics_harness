---
id: WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK
title: Add descriptor-level source/output identity check to Claude and Codex file exporters
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions:
  - edit_file
  - add_tests
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - change_antigravity_adapter
acceptance:
  - "`claude_export.convert_claude_session` opens the output without `O_TRUNC` and compares `fstat` to the source (`os.path.samestat`) before truncating; a link created after the path check raises `ClaudeExportError` and leaves the source untouched"
  - "`codex_file_export.convert_codex_file` does the same and raises `CodexFileExportError`"
  - "Each adapter has a race test (collision check patched to create a hardlink to the source) mirroring the antigravity test"
  - "Output files are still created 0600 from the first write; existing collision and force tests still pass"
  - "`scripts/test`, `scripts/lint`, `scripts/format --check --diff`, and `lrh validate` pass"
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/codex_file_export.py
  - tests/conversations_tests/claude_export_test.py
  - tests/conversations_tests/codex_file_export_test.py
---

# WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK: Add descriptor-level source/output identity check to Claude and Codex file exporters

## Summary

Close the check-then-write window in the Claude and Codex file-export adapters by verifying, on the opened output file descriptor, that the output is not the source transcript before truncating it.

## Problem / Context

Both adapters reject a source/output collision with a path-based check (`_reject_source_output_collision`: resolved-path comparison plus `samefile` when the output exists), which runs before the write. That check is not atomic with the write. If the output is absent at check time and a symlink or hardlink to the source is created before the write, `--force` follows it and truncates the source. PR #672 fixed this in `antigravity_export.py` after a Copilot review finding, by opening the output without `O_TRUNC`, comparing `fstat` of the descriptor to the source with `os.path.samestat`, and only then truncating.

- `claude_export.py`: `_write_private_text` opens with `O_WRONLY | O_CREAT | O_TRUNC`, so truncation happens at open, before any identity check is possible.
- `codex_file_export.py`: the output is written with `destination.write_bytes(...)`, which truncates by path.

### Prior Art Check
- **Duplication verdict**: none found. Searched `project/work_items/` and `src/lrh/conversations/`; the antigravity adapter carries the reference fix (PR #672), and no existing item covers the other two.
- **Demand verdict**: no existing work item, proposal, or backlog entry requests this. It originates from PR #672's recorded follow-up.

## Scope

### Included
- `src/lrh/conversations/claude_export.py` and `src/lrh/conversations/codex_file_export.py` write paths.
- Race tests for each adapter.

### Non-Goals
- The antigravity adapter, already fixed in PR #672.
- `codex_app_server_export.py` and `codex_archive.py`, which were not audited for this pattern; if they share it, file a separate item.
- Changing the existing path-based guards, which remain as the early, friendly check.

## Required Changes

- Claude: drop `O_TRUNC` from the `os.open` in `_write_private_text`; after opening, compare `os.fstat(fd)` to the source with `os.path.samestat`, raise `ClaudeExportError` (same message as the path guard) if they match, else `os.ftruncate(fd, 0)` and write. Thread the source path into the helper.
- Codex: replace `destination.write_bytes(...)` with the same open-compare-truncate-write sequence (mode `0o600` on creation), raising `CodexFileExportError` on a match.
- Tests: for each adapter, patch `_reject_source_output_collision` to hardlink the source to the output path, then assert the export raises and the source content is unchanged.

## Acceptance Criteria

1. `claude_export.convert_claude_session` opens the output without `O_TRUNC` and compares `fstat` to the source (`os.path.samestat`) before truncating; a link created after the path check raises `ClaudeExportError` and leaves the source untouched.
2. `codex_file_export.convert_codex_file` does the same and raises `CodexFileExportError`.
3. Each adapter has a race test mirroring the antigravity test.
4. Output files are still created 0600 from the first write; existing collision and force tests still pass.
5. `scripts/test`, `scripts/lint`, `scripts/format --check --diff`, and `lrh validate` pass.

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `PYTHONPATH=src lrh validate`

## Risk Notes

Low. Dropping `O_TRUNC` changes behavior only when the output already exists: the file is now truncated after the identity check rather than at open. Preserve the 0600-from-creation behavior in the Claude adapter.
