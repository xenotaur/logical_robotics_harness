---
execution_id: 2026_10_11_15_23_47_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES
prompt_id: PROMPT(WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES)[2026-10-11T04:27:21+00:00]
work_item: WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/829
commit: 273c92d4bee792f06d7131472c5893fe65c70a56
created_at: 2026-10-11T15:23:47+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES.md
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Implement `WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES` through `/lrh-execute`
(`/lrh-implement` inlined). The work closes the project-scoping gaps that
PR #813 left on the `lrh serve` work-item routes.

# Result

PR https://github.com/xenotaur/logical_robotics_harness/pull/829 (fix commit
`b7cb4d8208761a25a121e0b23e1b60e1c90589ea`).

- **`src/lrh/serve.py`:**
  - `render_workbench_artifact_page` takes `project_selector`. With it, the
    Back, context, and download links stay under `/project/<id>/`. Without
    it, the `/workbench` links are unchanged.
  - The detail page's download link now uses
    `/project/<id>/work-items/<wi>/prompt?download=1`.
  - New `_write_project_work_item` and `_write_project_prompt` handler
    helpers serve both GET and HEAD. The prompt helper handles
    `?download=1` through the existing download writers.
  - `_config_for_project_selector` raises 409 `no_local_checkout`, naming
    the missing path, when `repo_path_exists is False`.
  - `render_project_selector_error_page` shows `error.message`.
- **`tests/cli_tests/serve_test.py`:** three new tests (scoped links and
  download, missing bound checkout, HEAD parity with GET). The
  served-selectors assertion is now route-specific.
- **`docs/reference/cli/serve.md`:** a new "Work-item routes" section, and
  the 409 bullet covers a missing checkout.
- **Self-review:** the diff-mode pass found no blocking issues. One nit was
  fixed before push: the 409 message used `repr` quoting on the path.
  Record: `2026_10_11_15_23_21_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_SELFREVIEW`.

# Validation

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src` on branch
`xenotaur/feat/wi-serve-project-scoped-work-item-routes-impl`, cut from
`3f7aa723`. Versions: Black 26.3.1, Ruff 0.15.12.

- `scripts/format --check --diff`: 296 files unchanged.
- `scripts/lint`: passed.
- `scripts/test`: 2259 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`, inlined by `/lrh-execute` Step 4. Closeout
  resolves the work item.
