---
execution_id: 2026_10_08_02_09_07_WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_IMPL
prompt_id: PROMPT(WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK:WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_IMPL)[2026-10-07T23:05:34+00:00]
work_item: WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/787
commit:
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK.md
session_transcript: pending
created_at: 2026-10-08T02:09:07+00:00
---

# Summary

Implement WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK: add a
descriptor-level source/output identity check to the Claude and Codex file
exporters, mirroring the antigravity fix from PR #672.

# Result

Opened PR #787. `claude_export._write_private_text` and a new
`codex_file_export._write_private_bytes` open the output without `O_TRUNC`,
compare `fstat` to the source with `os.path.samestat`, and only then
`ftruncate` and write (Claude's `fchmod` also follows the check). A link to the
source created after the path check now raises `ClaudeExportError` /
`CodexFileExportError` and leaves the source untouched. Newly created Codex
file exports are now `0600` (behavior change, documented). Added a race test
per adapter, force-overwrite-truncates tests, and a Codex 0600 test; with the
identity check disabled both race tests fail. Docs updated in
`docs/reference/cli/conversation.md`. Diff-mode self-review: 0 defects, 3 nits
(see the `_IMPL_SELFREVIEW` record).

# Validation

`scripts/format --check --diff`, `scripts/lint`, `scripts/test` (1957 tests OK)
with the LRH conda env (ruff 0.15.12, black 26.3.1, Python 3.11); `lrh validate`
0 errors. Touched-module tests, lint and validate re-run after merging
origin/main.

# Follow-up

Shared descriptor-level write helper across the three export adapters; audit
`codex_app_server_export.py` and `codex_archive.py` for the same pattern;
`O_EXCL` for the no-`--force` create race.
