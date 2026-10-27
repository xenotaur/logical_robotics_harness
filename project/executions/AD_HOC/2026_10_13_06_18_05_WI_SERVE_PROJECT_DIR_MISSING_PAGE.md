---
execution_id: 2026_10_13_06_18_05_WI_SERVE_PROJECT_DIR_MISSING_PAGE
prompt_id: PROMPT(AD_HOC:WI_SERVE_PROJECT_DIR_MISSING_PAGE)[2026-10-13T02:22:07+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/841
commit: a94f15d4e783d52c7e95e79105c74b47e31a8ba6
created_at: 2026-10-13T06:18:05+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SERVE-PROJECT-DIR-MISSING-PAGE.md
session_transcript: claude-app:c94e499e-da6e-4e3f-a979-5876278e9f67
---
# Summary

Created the work item `WI-SERVE-PROJECT-DIR-MISSING-PAGE` with
`/lrh-work-item`. The owner noticed that Narramorph has a local checkout but
no LRH `project/` directory, and that `lrh serve` showed it the misleading
"No dependency-map views" page. PR #829 had left this case out of scope as a
Non-Goal.

# Result

- File: `project/work_items/proposed/WI-SERVE-PROJECT-DIR-MISSING-PAGE.md`.
  It is a `deliverable` under `WS-LRH-CONSOLE-LOCAL-DOGFOOD`, with no
  dependencies.
- PR: https://github.com/xenotaur/logical_robotics_harness/pull/841
- Research confirmed the following:
  - The current behavior is 200 "No dependency-map views" on the index and
    JSON 404s elsewhere.
  - The statusboard already classifies the state as `missing_project` with
    `PROJECT_CONTROL_DIR_NOT_FOUND`.
  - Both fix commands exist: `lrh project init --project-root` and
    `lrh meta set --project-dir`.
- Prior-art check: no duplicate. The only demand is the owner's request plus
  PR #829's Non-Goal.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SERVE-PROJECT-DIR-MISSING-PAGE`: prompt-ready,
  with no blocking items or warnings.

# Follow-up

- Offered: add the work item to `WS-LRH-CONSOLE-LOCAL-DOGFOOD`'s
  `work_items:` list.
- After merge, run `/lrh-closeout`, then
  `/lrh-execute WI-SERVE-PROJECT-DIR-MISSING-PAGE`.
