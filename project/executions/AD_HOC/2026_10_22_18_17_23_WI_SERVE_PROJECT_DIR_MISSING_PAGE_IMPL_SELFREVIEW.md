---
execution_id: 2026_10_22_18_17_23_WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE_IMPL_SELFREVIEW)[2026-10-22T18:17:23+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_22_18_17_23_WI_SERVE_PROJECT_DIR_MISSING_PAGE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/850
commit:
created_at: 2026-10-22T18:17:23+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-DIR-MISSING-PAGE.md
session_transcript: pending
---
# Summary

Diff-mode `/lrh-self-review` of the `WI-SERVE-PROJECT-DIR-MISSING-PAGE`
implementation, run once before the first push. It reviewed `git diff HEAD`
on `fda95ebb`, covering `src/lrh/serve.py`, `tests/cli_tests/serve_test.py`,
and `docs/reference/cli/serve.md`. The pass was report-only, without
`--apply`. `pr` and `rerun_of` were set after the PR opened.

# Result

The cold-context subagent found **no blocking or correctness issues** and
judged that all five acceptance criteria are plausibly met.
`tests.cli_tests.serve_test` passed 132 tests. It verified:

- **Check placement.** The check runs after both `no_local_checkout`
  raises and after the `main` fallback, and before any `ServeConfig` is
  built.
- **Route coverage.** Every route goes through `_config_for_project_selector`.
- **Default vs custom classification.** Both paths come from `expanduser`
  plus `resolve`, so the comparison classifies correctly. `project_dir="."`
  never reaches the new error.
- **Advertised commands.** Every command shown would clear the 409:
  `build_plan` writes `<repo>/project`, and `meta set --project-dir` exists.
- **Quoting and escaping.** Both are correct.
- **`no_local_checkout` payload and pages.** Unchanged.
- **Tests.** The new tests would fail without the change.
- **Docs.** They match the code.

It made three low findings:

1. **Stale docstrings** in `dependency_map_payload`,
   `render_dependency_map_page`, and `_config_for_project_selector`.
   **Fixed before push.**
2. **`exists()` vs `/meta`'s `is_dir()`.** **Fixed before push:** the check
   now uses `is_dir()`, so a `project_dir` that names a file counts as
   missing.
3. **Pre-existing, out of scope.** An absolute or escaping `project_dir`
   resolves to None and gets the `no_local_checkout` 409. The registry
   already rejects such values (`workspace.py` project-dir validation).
   Not changed.

# Validation

- After the fixes: `scripts/format --check --diff` exit 0, `scripts/lint`
  exit 0, `scripts/test` 2368 tests OK, `lrh validate` 0 errors.
- The invoking session re-verified the top finding (the stale docstrings)
  by reading `serve.py`.

# Follow-up

- `/lrh-implement` Step 8 (commit and PR) proceeded.
