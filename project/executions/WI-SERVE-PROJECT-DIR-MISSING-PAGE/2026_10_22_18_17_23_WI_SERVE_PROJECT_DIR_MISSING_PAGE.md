---
execution_id: 2026_10_22_18_17_23_WI_SERVE_PROJECT_DIR_MISSING_PAGE
prompt_id: PROMPT(WI-SERVE-PROJECT-DIR-MISSING-PAGE:WI_SERVE_PROJECT_DIR_MISSING_PAGE)[2026-10-22T17:55:04+00:00]
work_item: WI-SERVE-PROJECT-DIR-MISSING-PAGE
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/850
commit:
created_at: 2026-10-22T18:17:23+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-DIR-MISSING-PAGE.md
session_transcript: pending
---
# Summary

Implement `WI-SERVE-PROJECT-DIR-MISSING-PAGE` through `/lrh-execute`, with
`/lrh-implement` inlined. The work makes `lrh serve` project routes explain a
registered checkout that has no LRH project directory, as Narramorph does
today. Before this change, those routes showed "No dependency-map views" or a
bare 404.

# Result

PR https://github.com/xenotaur/logical_robotics_harness/pull/850, fix commit
`e650acd6ead3c58ca2506f1617ac8f2f00d1436b`.

- **`src/lrh/serve.py`**
  - `_config_for_project_selector` raises a 409 `no_project_directory` when
    the bound repo exists but the resolved project directory is not a
    directory. It uses `is_dir`, as `/meta` does. The check runs after the
    missing-checkout 409 and the `main` fallback.
  - The new `_no_project_directory_error` builds next actions that depend
    on the directory, comparing normalized paths:
    - default `<repo>/project`: init, or a repoint;
    - custom `project_dir`: a repoint, or init followed by a repoint to
      `project`, never init alone.
  - `ProjectSelectorError` gains `next_actions`. `next_action` is now the
    first entry, so the `no_local_checkout` payload is unchanged.
  - `render_project_selector_error_page` adds a "No LRH project directory"
    branch, keyed on the error code.
  - Docstrings were updated.
- **`tests/cli_tests/serve_test.py`**: two new tests.
  - Unset, `project`, and custom `control` directories, checked on all four
    HTML routes, HEAD, and the JSON API.
  - A regression guard that `project/` with no views still returns 200.
- **`docs/reference/cli/serve.md`**: the "Project selectors" section
  documents the new case.
- **Self-review**: the diff-mode pass found no blocking issues. Two low
  findings were fixed before push: stale docstrings, and `exists()` replaced
  with `is_dir()`. See record `2026_10_22_18_17_23_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_SELFREVIEW`.

# Validation

Runs used the `LrhLocalAgent` env with `PYTHONPATH=src`, on branch
`xenotaur/feat/wi-serve-project-dir-missing-page-impl` from `fda95ebb`.
Black 26.3.1, Ruff 0.15.12.

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2368 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land the PR through `/lrh-land`, which `/lrh-execute` Step 4 runs inline.
  Closeout resolves the work item.
