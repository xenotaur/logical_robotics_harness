---
execution_id: 2026_08_30_08_43_17_DOC_WORK_WI_LRH_MEMORY_TRANSFER_SAFETY_REVIEW
prompt_id: PROMPT(AD_HOC:DOC_WORK_WI_LRH_MEMORY_TRANSFER_SAFETY_REVIEW)[2026-08-30T08:42:50+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_29_17_00_22_DOC_WORK_WI_LRH_MEMORY_TRANSFER_SAFETY
pr: https://github.com/xenotaur/logical_robotics_harness/pull/653
commit: 1eea39c0
created_at: 2026-08-30T08:43:17+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/653
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Addressed 2 open review comments on PR #653 (`lrh memory` reference
page's `import`/`transfer` overwrite-safety documentation) — both by
`chatgpt-codex-connector`.

# Result

1. **Byte-identical overwrite exception not documented (Codex P2).**
   The new "required to overwrite any existing destination" wording
   incorrectly implied `--force` was needed even for a no-op
   re-import. Independently re-verified against
   `_guard_import_overwrite`'s source: its byte-identical no-op check
   (`existing_bytes == new_content.encode("utf-8")`) returns *before*
   its own `if not force:` raise — so an idempotent re-import genuinely
   requires no `--force`. Fixed both the `import` flag bullet and the
   "Overwrite safety" paragraph to state this explicitly.
2. **Snapshot filename used the kebab-case name, not the on-disk stem
   (Codex P2).** `<name>.<short-hash>.md` implied `feedback-x.<hash>.md`;
   the actual stem comes from `filename_for()`'s underscore
   substitution (`feedback_x.md`), confirmed by re-reading
   `_guard_import_overwrite`'s own `stem = pathlib.Path(filename).stem`
   line. Fixed to `<filename-stem>`, matching the already-correct
   wording in `docs/how-to/move-memories-between-projects.md`.

Publication outcome: **Pushed directly** — commit `1eea39c0` on the
existing open PR branch
`xenotaur/chore/doc-work-wi-lrh-memory-transfer-safety`.

# Validation

- `lrh validate` — 0 errors; 2 pre-existing warnings, unrelated.
- `gh pr diff 653 --name-only` — confirmed docs-only diff (local
  branch was behind `main`, so a raw `git diff origin/main..HEAD`
  comparison was unreliable here; used the actual PR diff instead).
- Both fixed claims independently re-verified against
  `_guard_import_overwrite`'s source before applying, not merely
  accepted from the review comments.

# Follow-up

- None from this round.
