---
execution_id: 2026_10_08_16_18_28_SERVE_DETAIL_LOAD_PROJECT_404
prompt_id: PROMPT(AD_HOC:SERVE_DETAIL_LOAD_PROJECT_404)[2026-10-08T06:33:50+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/798
commit:
created_at: 2026-10-08T16:18:28+00:00
agent: claude_app
instruction_source: "ad-hoc: guard control_loader.load_project in serve.render_design_detail_page / render_workstream_detail_page (and the dashboard summary helpers) so a malformed registered project returns 404 JSON instead of dropping the connection; follow-up to PR #793"
session_transcript: pending
---

# Summary

Ad-hoc fix and follow-up to PR #793. After a Meta workspace resolved to a
malformed registered project, `src/lrh/serve.py` called
`control_loader.load_project` unguarded in the design and workstream detail
renderers. The exception escaped the request handler, and the server dropped
the connection without a response.

# Result

- `src/lrh/serve.py`:
  - `render_design_detail_page` and `render_workstream_detail_page` now catch
    `(FileNotFoundError, OSError, ValueError)` and return 404
    `{"error": "not_found", "message": str(error)}`. This matches
    `render_project_work_item_page`. HEAD goes through the same renderers.
  - At the user's request at the plan gate, `_project_design_summaries` and
    `_project_workstream_summaries` now return `[]` on the same errors, so the
    `/project/<p>` dashboard still renders with a 200 response.
- `tests/cli_tests/serve_test.py`: added two tests.
  - `test_detail_routes_return_not_found_for_malformed_project` checks GET
    404 JSON and HEAD 404 on both detail routes.
  - `test_project_dashboard_omits_links_for_malformed_project` checks the
    dashboard route.
  - Both use a registered project, set up with `_write_local_meta_workspace`
    and `_write_project_record`, that contains a workstream with no title.
  - Without the fix, all three cases fail with `RemoteDisconnected`.
- Prior-art check: no duplicate found. The demand match is the follow-up
  listed in PR #793's execution records. #793 is still open and edits
  `_project_from_meta_selector` in the same file, which is a different hunk.
- Self-review: `2026_10_08_16_17_22_SERVE_DETAIL_LOAD_PROJECT_404_SELFREVIEW.md`
  found nothing blocking. It raised 1 minor finding and 3 nits; none were
  fixed.

# Validation

Ran in the `LrhMain` conda env with `PYTHONPATH=src`, which imports this
worktree's `lrh`. Tool versions: Python 3.11.17, Black 26.3.1, Ruff 0.15.12.

- `scripts/format --check --diff`: clean
- `scripts/lint`: clean
- `scripts/test`: 2055 tests, OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Optional: when loading fails, show an "unavailable: <error>" note on the
  dashboard instead of "None.".
