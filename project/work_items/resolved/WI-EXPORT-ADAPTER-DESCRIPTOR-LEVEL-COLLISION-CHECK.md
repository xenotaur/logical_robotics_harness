---
id: WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK
title: Add descriptor-level, stable-source-identity collision check to Claude, Codex, and antigravity file exporters
type: deliverable
status: resolved
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
resolution: 'Landed descriptor-level, stable-source-identity collision checks in the Claude, Codex, and antigravity file exporters in PR #787 (2b8c61f9585f7d97e6a490fa5087768bffdbda5d)'
expected_actions:
  - edit_file
  - add_tests
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "`claude_export.convert_claude_session` opens the output without `O_TRUNC` and compares `fstat` of the open output to the identity of the source file that was read (`os.path.samestat`) before truncating or chmod-ing; a link created after the path check raises `ClaudeExportError` and leaves the source untouched"
  - "`codex_file_export.convert_codex_file` does the same and raises `CodexFileExportError`"
  - "`antigravity_export.convert_antigravity_session` is changed to capture the source identity at read time and compare against it, with unchanged error type (`AntigravityExportError`)"
  - "Source identity is taken from the descriptor the source bytes are read through, not from a pathname at write time, so a source that is renamed, replaced, or removed after the read cannot defeat the check"
  - "Each adapter has a race test for a link created after the path check, plus rename and replacement regression tests (output hardlinked to the original, source path then renamed or replaced after the read), each verified to fail when the identity comparison is disabled"
  - "Output files are still created 0600 from the first write; existing collision and force tests still pass"
  - "`scripts/test`, `scripts/lint`, `scripts/format --check --diff`, and `lrh validate` pass"
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - src/lrh/conversations/source_identity.py
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/codex_file_export.py
  - src/lrh/conversations/antigravity_export.py
  - tests/conversations_tests/source_identity_test.py
  - tests/conversations_tests/claude_export_test.py
  - tests/conversations_tests/codex_file_export_test.py
  - tests/conversations_tests/antigravity_export_test.py
  - docs/reference/cli/conversation.md
---

# WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK: Add descriptor-level, stable-source-identity collision check to Claude, Codex, and antigravity file exporters

## Summary

Close the check-then-write window in the Claude, Codex, and antigravity file-export adapters by verifying, on the opened output file descriptor, that the output is not the source transcript that was read, before truncating or chmod-ing it. The source is identified by the descriptor it was read through, not by its pathname at write time.

## Problem / Context

All three adapters reject a source/output collision with a path-based check (`_reject_source_output_collision`: resolved-path comparison plus `samefile` when the output exists), which runs before the write. That check is not atomic with the write. If the output is absent at check time and a symlink or hardlink to the source is created before the write, `--force` follows it and truncates the source. PR #672 fixed this in `antigravity_export.py` after a Copilot review finding, by opening the output without `O_TRUNC`, comparing `fstat` of the descriptor to the source with `os.path.samestat`, and only then truncating.

- `claude_export.py`: `_write_private_text` opened with `O_WRONLY | O_CREAT | O_TRUNC`, so truncation happened at open, before any identity check was possible.
- `codex_file_export.py`: the output was written with `destination.write_bytes(...)`, which truncates by path.

The first version of this fix (and PR #672's antigravity version) compared the output descriptor against `source.stat()`, taken by pathname at write time. Review of PR #787 (Codex P1 `r4213912591`, Copilot `r4213922974`) showed that is a second-order gap: if the source path is renamed or replaced after the source bytes are read, with the output already hardlinked to the original file, `source.stat()` describes the replacement (or fails, and the helper returned `False`), so the comparison reports "different" and the original transcript is truncated. The antigravity adapter shares exactly this weakness, so it is in scope here.

### Prior Art Check
- **Duplication verdict**: none found. Searched `project/work_items/` and `src/lrh/conversations/`; the antigravity adapter carries the first-generation fix (PR #672), and no existing item covers the stable-identity gap or the other two adapters.
- **Demand verdict**: no existing work item, proposal, or backlog entry requests this. It originates from PR #672's recorded follow-up and PR #787's review findings.

## Scope

### Included
- `src/lrh/conversations/claude_export.py`, `src/lrh/conversations/codex_file_export.py`, and `src/lrh/conversations/antigravity_export.py` read and write paths.
- A small shared helper, `src/lrh/conversations/source_identity.py`, that reads a source file through one descriptor and returns its bytes together with the `os.stat_result` of that descriptor.
- Race, rename, and replacement tests for each adapter, plus tests for the helper.
- The matching bullets in `docs/reference/cli/conversation.md`.

### Non-Goals
- `codex_app_server_export.py` and `codex_archive.py`, which were not audited for this pattern; if they share it, file a separate item.
- Changing the existing path-based guards, which remain as the early, friendly check.
- Closing the no-`--force` create race (no `O_EXCL`); it does not endanger the source and is pre-existing.

## Required Changes

- Shared helper: `read_bytes_with_identity(path)` opens the source with `os.open(..., O_RDONLY)`, takes `os.fstat` on that descriptor, reads the bytes from it, closes it, and returns `(bytes, stat_result)`. `OSError` propagates so each adapter keeps its existing error mapping.
- Each adapter: read the source via the helper instead of `path.read_bytes()`, keep the returned stat result, and pass it to the writer in place of the source path. The writer opens the output without `O_TRUNC`, compares `os.fstat(fd)` to the captured source stat with `os.path.samestat`, raises the adapter's error (same message as the path guard) on a match, else `os.ftruncate(fd, 0)`, then (Claude only) `fchmod`, then writes. Remove the per-adapter `_is_same_file` helpers.
- Codex: replace `destination.write_bytes(...)` with the open-compare-truncate-write sequence (mode `0o600` on creation).
- Tests: for each adapter, (a) patch the collision check to hardlink the source to the output path, (b) hardlink the output to the original and then rename the source path away after the read, (c) same but replace the source path with a new file; assert the export raises and the original file content is unchanged. The Codex adapter runs `_reject_source_output_collision` before its read, so its tests hook `render_codex_markdown`, which runs between read and write. Verify by mutation that disabling the identity comparison makes these tests fail.

## Acceptance Criteria

1. Each of `claude_export.convert_claude_session`, `codex_file_export.convert_codex_file`, and `antigravity_export.convert_antigravity_session` opens the output without `O_TRUNC` and compares `fstat` of the open output to the identity of the source file that was read (`os.path.samestat`) before truncating or chmod-ing; a collision raises that adapter's error and leaves the source untouched.
2. The source identity comes from the descriptor the source bytes were read through, so a source renamed, replaced, or removed after the read cannot defeat the check.
3. Each adapter has link-after-check, rename, and replacement regression tests, each failing when the identity comparison is disabled.
4. Output files are still created 0600 from the first write; existing collision and force tests still pass.
5. `scripts/test`, `scripts/lint`, `scripts/format --check --diff`, and `lrh validate` pass.

## Validation

- `scripts/version tools`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `PYTHONPATH=src lrh validate`

## Risk Notes

Low. Dropping `O_TRUNC` changes behavior only when the output already exists: the file is now truncated after the identity check rather than at open. Preserve the 0600-from-creation behavior in the Claude adapter, and keep the identity check ahead of `fchmod` so a raced hardlink cannot get the source chmod-ed. Reading the source through a descriptor instead of `Path.read_bytes()` must keep each adapter's existing `OSError` handling.
