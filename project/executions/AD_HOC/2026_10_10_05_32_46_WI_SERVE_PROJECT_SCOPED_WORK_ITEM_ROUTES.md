---
execution_id: 2026_10_10_05_32_46_WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_SCOPED_WORK_ITEM_ROUTES)[2026-10-10T02:49:04+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/818
commit:
created_at: 2026-10-10T05:32:46+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES.md
session_transcript: pending
---
# Summary

Created the work item `WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES` with
`/lrh-work-item`. It captures the follow-ups deferred in PR #813's closeout
note. The two work-item download links render from the served project (the
same bug class as #813). A missing bound checkout gets a misleading page
instead of the framed 409. The work-item routes have no HEAD handler. One
served-selectors test assertion is loose.

# Result

- File: `project/work_items/proposed/WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES.md`.
  It is a `deliverable` under `WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with no
  dependencies.
- PR: https://github.com/xenotaur/logical_robotics_harness/pull/818
- Research added one finding to the scope. The `/project/<id>/work-items/<wi>/prompt`
  preview page's "Download Markdown" link (`src/lrh/serve.py:2217`) also
  targets the served project's `/workbench/prompt`.
- Prior-art check: no duplicate. The only demand is PR #813's closeout note,
  which the work item cites.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`:
  prompt-ready, no blocking items or warnings.

# Follow-up

- Offered: add the work item to `WS-LRH-CONSOLE-LOCAL-DOGFOOD`'s
  `work_items:` list.
- After this PR merges, run `/lrh-closeout`. Then implement the work item
  with `/lrh-execute WI-SERVE-PROJECT-SCOPED-WORK-ITEM-ROUTES`.
