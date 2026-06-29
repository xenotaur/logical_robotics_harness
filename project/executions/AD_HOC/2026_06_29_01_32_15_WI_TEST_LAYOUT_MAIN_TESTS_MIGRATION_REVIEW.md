---
execution_id: 2026_06_29_01_32_15_WI_TEST_LAYOUT_MAIN_TESTS_MIGRATION_REVIEW
prompt_id: PROMPT(AD_HOC:WI_TEST_LAYOUT_MAIN_TESTS_MIGRATION_REVIEW)[2026-06-29T01:17:44-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/348
commit: 5d9c8a1
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/348
session_transcript: claude-app:56e26950-a2c7-4fe5-acae-55216781527b
created_at: 2026-06-29T01:32:15-04:00
---

# Summary

Addressed two review comments on PR #348 (WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION
planning artifact).

# Result

**Comment 1** (`#discussion_r3488444553`, Copilot) — `version_integration_test.py`
was listed under "True module mirrors" in the frontmatter `acceptance:` list,
but the body correctly described it as an integration test (broader than one
module). Fixed the acceptance criterion to label it as an integration test,
consistent with the body.

**Comment 2** (`#discussion_r3488445153`, Codex P2) — The migration was
described as "pure relocation — no content changes," but several files
(`conversation_test.py`, `match_test.py`, `project_doctor_test.py`,
`project_init_test.py`, `prompt_test.py`, `search_test.py`, `setup_test.py`,
`snapshot_test.py`) use `Path(__file__).resolve().parents[2]` to compute the
repo root. After moving one directory deeper, this resolves to `tests/`
instead of the repo root, breaking subprocess cwd arguments. Fixed by:
- Removing the "pure relocation" claim from Required Changes
- Adding an explicit step to update `parents[2]` → `parents[3]` in all
  moved files, with the list of known affected files
- Narrowing the Non-Goals to permit path-depth fixes
- Replacing the pytest Risk Note with a detailed path-depth breakage warning
  listing all known affected files

No primary execution record found for `rerun_of` — WI was created directly
in the design session, not via `/lrh-implement`.

# Validation

- `lrh validate` — 0 errors, 0 warnings (no Python changes; format/lint/test not required)

# Follow-up

- Once PR #348 merges, set `status: landed` and populate `commit:` with merge SHA.
