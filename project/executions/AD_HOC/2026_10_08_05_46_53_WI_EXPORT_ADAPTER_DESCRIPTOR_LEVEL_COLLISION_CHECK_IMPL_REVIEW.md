---
execution_id: 2026_10_08_05_46_53_WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_IMPL_REVIEW)[2026-10-08T04:54:41+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_08_02_09_07_WI_EXPORT_ADAPTER_DESCRIPTOR_LEVEL_COLLISION_CHECK_IMPL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/787
commit:
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/787
session_transcript: pending
created_at: 2026-10-08T05:46:53+00:00
---

# Summary

Address two review threads on PR #787 (Codex P1 `r4213912591`, Copilot
`r4213922974`): the writers compared the output descriptor against
`source.stat()` taken by pathname at write time, so a source renamed, replaced,
or removed after it was read could defeat the guard and the original file be
truncated through a pre-existing hardlink. Per the user's direction, the same
weakness in the antigravity adapter (merged in PR #672) was fixed in this PR,
and the work item was revised to allow it.

# Result

Both findings were valid and reproduced (the new rename and replacement tests
fail against the previous implementation). Fix:

- New `src/lrh/conversations/source_identity.py` with
  `read_bytes_with_identity(path)`: opens the source with `os.open`, takes
  `os.fstat` on that descriptor, reads the bytes from it, closes it, returns
  `(bytes, stat_result)`.
- Claude, Codex, and antigravity adapters read the source through the helper
  and pass the captured `source_stat` to their writers, which compare
  `os.path.samestat(os.fstat(output_fd), source_stat)` before truncating or
  chmod-ing. The three per-adapter `_is_same_file` helpers were removed.
- Antigravity's writer also `chmod`ed the output by pathname after the write;
  it now `fchmod`s the checked descriptor, matching the Claude adapter.
- Work item `WI-EXPORT-ADAPTER-DESCRIPTOR-LEVEL-COLLISION-CHECK` revised:
  title, acceptance, scope, required changes and artifacts now cover all three
  adapters and the stable-identity requirement, and `change_antigravity_adapter`
  was removed from `forbidden_actions`. This widens the plan the user approved
  at the `/lrh-execute` Step 2 gate; the user directed the change in chat.
- Docs: the three "identity is re-checked" bullets in
  `docs/reference/cli/conversation.md` now say "against the file that was read".
- Tests: rename and replacement regressions for each adapter, plus helper tests.
  The Codex tests hook `render_codex_markdown` because Codex runs its path-based
  collision check before reading the source.

# Validation

- New rename and replacement tests against the previous implementation (HEAD
  `ea51f3cb`, extracted with `git archive`): exactly the six new tests fail, the
  other 89 pass.
- With `os.path.samestat` patched to return False on the new code, all nine
  race tests (link, rename, replacement for each adapter) fail.
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test` (1992 tests
  OK), `lrh validate` (0 errors, 0 warnings), using the LRH conda env.

# Follow-up

- Not applied: `O_EXCL` for the no-`--force` create race (pre-existing, does not
  endanger the source).
- `codex_app_server_export.py` and `codex_archive.py` were not audited for this
  pattern.
