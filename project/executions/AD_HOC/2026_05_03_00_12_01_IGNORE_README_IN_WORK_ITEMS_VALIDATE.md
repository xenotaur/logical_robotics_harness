---
execution_id: 2026_05_03_00_12_01_IGNORE_README_IN_WORK_ITEMS_VALIDATE
prompt_id: PROMPT(AD_HOC:IGNORE_README_IN_WORK_ITEMS_VALIDATE)[2026-05-02T20:10:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: ca926c3
created_at: 2026-05-03T00:12:01+00:00
---

# Summary

Exclude `README.md` (case-insensitive basename match) from work-item discovery used by `lrh work-items validate` so documentation files are not treated as malformed work items.

# Result

Implemented a narrow filter in work-item path discovery (`path.name.lower() == "readme.md"` is skipped) and added regression tests proving README files are ignored at root and bucket levels while non-README markdown diagnostics and valid WI behavior remain intact.

# Validation

- `scripts/test` (pass)
- `scripts/format` (pass)
- `scripts/lint` (pass)
- `lrh work-items validate --project-root .` (pass)

# Follow-up

None.
