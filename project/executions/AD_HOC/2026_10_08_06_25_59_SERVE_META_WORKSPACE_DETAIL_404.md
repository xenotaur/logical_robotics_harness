---
execution_id: 2026_10_08_06_25_59_SERVE_META_WORKSPACE_DETAIL_404
prompt_id: PROMPT(AD_HOC:SERVE_META_WORKSPACE_DETAIL_404)[2026-10-08T06:04:24+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/793
commit: a15e878c1a162fb1dc9ef37a40a269900687c12e
created_at: 2026-10-08T06:25:59+00:00
agent: claude-app
instruction_source: "ad-hoc: catch Meta workspace resolution/registry errors in serve._project_from_meta_selector so design/workstream detail routes return 404 JSON instead of dropping the connection"
session_transcript: claude-app:5a942286-523d-4024-a56b-96e1f2a712b6
---

# Summary

Ad-hoc fix. `_project_from_meta_selector` in `src/lrh/serve.py` did not catch
`MetaWorkspaceResolutionError` or `MetaRegistryError`. With no resolvable Meta
workspace, `GET /project/<p>/designs/<id>` and `/workstreams/<id>` raised
inside the request handler, and the server dropped the connection without a
response.

# Result

- `src/lrh/serve.py`: wrapped `resolve_meta_workspace` and
  `list_registered_project_loads_in_workspace` in
  `except (MetaWorkspaceResolutionError, MetaRegistryError)`, returning
  `(None, None)`. The existing callers already map that to 404
  `{"error": "not_found", "project": <selector>}`.
- `tests/cli_tests/serve_test.py`: added
  `test_detail_routes_return_not_found_without_meta_workspace`, covering the
  design and workstream detail routes. It fails with `RemoteDisconnected`
  without the fix.
- Prior-art check: no existing work item, proposal or PR covered this. Open
  PR #792 also edits `serve.py`, but not this function.
- Self-review: `2026_10_08_06_24_55_SERVE_META_WORKSPACE_DETAIL_404_SELFREVIEW.md`
  found nothing blocking.

# Validation

Run in the `LrhMain` conda env with `PYTHONPATH=src`. Python 3.11.17,
Black 26.3.1, Ruff 0.15.12; pyright is not installed.

- `scripts/format --check --diff`: clean
- `scripts/lint`: clean
- `scripts/test`: 2000 tests, OK
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Optional: wrap `control_loader.load_project` in the design and workstream
  detail renderers so a malformed project returns 404. The work-item routes
  already do this.
