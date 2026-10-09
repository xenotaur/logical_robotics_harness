---
execution_id: 2026_10_08_16_17_22_SERVE_DETAIL_LOAD_PROJECT_404_SELFREVIEW
prompt_id: PROMPT(AD_HOC:SERVE_DETAIL_LOAD_PROJECT_404_SELFREVIEW)[2026-10-08T16:17:12+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-10-08T16:17:22+00:00
agent: claude_app
instruction_source: "ad-hoc: lrh-self-review diff-mode from lrh-implement Step 7.5 for PROMPT(AD_HOC:SERVE_DETAIL_LOAD_PROJECT_404)[2026-10-08T06:33:50+00:00]"
session_transcript: pending
---

# Summary

Report-only `/lrh-self-review` pass in diff mode, without `--apply`. It ran
before the first push of the ad-hoc fix that guards
`control_loader.load_project` in `src/lrh/serve.py`. That fix covers the
design and workstream detail renderers and the two dashboard summary helpers.
A cold-context `general-purpose` subagent reviewed `git diff origin/main` of
the working tree. `rerun_of` stays empty by design, because diff mode runs
before the primary execution record exists.

# Result

Findings: 0 blocking, 1 minor, 3 nits.

- Minor: when a project is malformed, the dashboard shows "None." under the
  design and workstream link lists, which reads like the project is empty.
  The project card on the same page still shows the validation error. The
  invoking session re-checked this directly: `_html_link_list` returns
  `<p>None.</p>` when the list is empty (`src/lrh/serve.py` around line 2751).
- Nit: a 404 status for a malformed project is debatable. It follows the
  requested spec and the existing work-item route pattern.
- Nit: the new 404 bodies leave out `indent=2`. The output is unchanged,
  because the handler re-serializes the body with `json.loads`.
- Nit: the tests cover only the missing-title `ValueError` path. The
  other error paths go through the same `except`.

The subagent confirmed that the exception set covers everything
`load_project` raises, that no unguarded `load_project(` call is left,
and that HEAD returns the same status as GET.

No fixes were applied. The PR proceeds as planned.

# Validation

- The subagent ran the 90 tests in `tests.cli_tests.serve_test`: all passed.
- The subagent swapped in `serve.py` from `origin/main`. Both new tests then
  failed with `ValueError: missing or invalid string field 'title'`.

# Follow-up

- Optional: when loading fails, show an "unavailable: <error>" note on the
  dashboard instead of "None.".
