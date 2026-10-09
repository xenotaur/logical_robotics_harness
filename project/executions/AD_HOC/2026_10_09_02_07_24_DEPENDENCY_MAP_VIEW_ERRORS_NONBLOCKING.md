---
execution_id: 2026_10_09_02_07_24_DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING
prompt_id: PROMPT(AD_HOC:DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING)[2026-10-09T01:23:54+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/802
commit: 5e67c2b1fb6bc4898784d1e2e3c854fb12e034f7
created_at: 2026-10-09T02:07:24+00:00
agent: claude_app
instruction_source: "ad-hoc: stop invalid dependency-map view declarations (DEPENDENCY_MAP_VIEW_INVALID / DEPENDENCY_MAP_VIEW_UNKNOWN_REFERENCE) from blanking core_state, keeping lrh validate strict"
session_transcript: claude-app:f057ed51-1b95-47ea-9e12-14b2d6271846
---

# Summary

`_validate_dependency_map_views` reports view errors with severity `error`,
and `core_state.load_core_project_state` returned its empty state on any
validation error. So one bad `project/views/dependency_maps/*.md` made every
work item 404 on Serve's work-item and workbench artifact pages.

# Result

- `src/lrh/control/validator.py`: added named `DEPENDENCY_MAP_VIEW_INVALID`
  and `DEPENDENCY_MAP_VIEW_UNKNOWN_REFERENCE` constants plus the
  `DEPENDENCY_MAP_VIEW_ISSUE_CODES` set, and the emit sites now use them.
  Severity is unchanged, so `lrh validate` still exits non-zero.
- `src/lrh/core_state.py`: the empty-state gate now uses
  `_has_state_blocking_errors`, which ignores view-scoped codes.
  `ValidationSummary` still counts them.
- Tests: two new core_state tests and the
  `TestDependencyMapViewErrorsStayScoped` serve tests, covering the work-item
  page, the workbench prompt, the 422 map page, and `lrh validate`.
- Prior art: no duplicate and no existing work item. Related resolved items
  are WI-LRH-CONSOLE-MAP-SNAPSHOT and WI-LRH-CONSOLE-MAP-STATIC.
- Self-review: see
  `2026_10_09_02_07_28_DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING_SELFREVIEW`.

# Validation

Tools: conda env `LrhMain` with `PYTHONPATH=src`, so `lrh` resolves to this
worktree. Versions: black 26.3.1, ruff 0.15.12, Python 3.11.17.

- `scripts/format --check --diff`: clean
- `scripts/lint`: clean
- `scripts/test`: 2130 tests OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

None.
