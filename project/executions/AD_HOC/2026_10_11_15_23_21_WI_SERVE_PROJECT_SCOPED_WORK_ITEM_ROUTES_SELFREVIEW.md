---
execution_id: 2026_10_11_15_23_21_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES_SELFREVIEW)[2026-10-11T15:23:21+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_11_15_23_47_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES
pr: https://github.com/xenotaur/logical_robotics_harness/pull/829
commit: 273c92d4bee792f06d7131472c5893fe65c70a56
created_at: 2026-10-11T15:23:21+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES.md
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Diff-mode `/lrh-self-review` of the `WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`
implementation, run once before the first push. It reviewed `git diff HEAD`
on top of `3f7aa723`, covering `src/lrh/serve.py`,
`tests/cli_tests/serve_test.py`, and `docs/reference/cli/serve.md`. This was
a report-only pass, without `--apply`. `rerun_of` and `pr`
were backfilled after the PR opened.

# Result

The cold-context subagent found **no blocking issues**. It judged that the
diff plausibly satisfies all six acceptance criteria. `tests.cli_tests.serve_test`
ran 126 tests, OK. It verified:

- **Escaping and quoting.** URLs are quoted with `_url_quote(safe="")`, then
  HTML-escaped. The `/workbench` markup is byte-for-byte unchanged.
- **Missing-checkout check.** It reads `repo_path_exists`, not the
  `project/` directory. It cannot affect the `main` fallback or the
  never-bound case.
- **GET/HEAD agreement.** GET and HEAD share helpers, and the download HEAD
  reuses `_write_download_head`.
- **Tests.** Each new test would fail without the change.
- **Docs.** They match the code.

It raised two nits:

1. The missing-checkout test doesn't assert the frame wrapper. It uses the
   same rendering path as the remote-only test, which does assert it.
   Accepted as is.
2. The 409 message quoted the path with Python `repr`, which would double
   backslashes on Windows. **Fixed before push:** the message now uses plain
   double quotes. I verified the fix by reading `serve.py`, and
   `serve_test` still passes.

# Validation

All runs used the `LrhLocalAgent` env with `PYTHONPATH=src`. Versions:
Black 26.3.1, Ruff 0.15.12.

- After the fix, `scripts/format --check --diff` and `scripts/lint` passed.
- `scripts/test`: 2259 tests, OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `/lrh-implement` Step 8 (commit and PR) proceeds next.
