---
execution_id: 2026_05_16_07_56_03_IMPLEMENT_SERVE_PROMPT_WORKBENCH_MVP
prompt_id: PROMPT(WI-LRH-SERVE-SAFE-DEFAULT-MVP:IMPLEMENT_SERVE_PROMPT_WORKBENCH_MVP)[2026-05-15T16:03:00-04:00]
work_item: WI-LRH-SERVE-SAFE-DEFAULT-MVP
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-16T07:56:03+00:00
---

# Summary

Implemented the safe-default `lrh serve` prompt/run-packet/run-report workbench MVP for `WI-LRH-SERVE-SAFE-DEFAULT-MVP`.

# Dependency Checks

- Viewer dependency: satisfied by existing `lrh serve` read-only project viewer and `/api/project` route.
- Packet/report dependency: satisfied by existing `lrh.assist.run_packet.render_run_packet_from_work_item` and `lrh.assist.run_report.render_run_report` renderers.

# Result

- Added `/workbench` and `/api/workbench` index surfaces for deterministic work-item preview actions.
- Added `/workbench/prompt`, `/workbench/run-packet`, and `/workbench/run-report` copy/download pages.
- Added `/api/workbench/prompt`, `/api/workbench/run-packet`, and `/api/workbench/run-report` JSON preview routes.
- Reused package-owned prompt, run-packet, and run-report renderers.
- Kept routes read-only and in-memory; no agent dispatch, branch mutation, PR mutation, CI loop, merge, release, publish, arbitrary file serving, or repository write behavior was added.

# Validation

- `scripts/version tools` passed with expected Black/Ruff versions; pylint and conda remain unavailable in this environment report.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` passed: 528 tests.
- `lrh validate` passed with 0 errors and 3 pre-existing planning orphan warnings.
- `lrh snapshot` without a scope exited with CLI usage error because the command requires a scope.
- `lrh snapshot project --stdout` passed.
- `lrh serve --help` passed.
- Local workbench smoke via `serve.render_workbench_artifact(..., "run-packet", "WI-LRH-SERVE-SAFE-DEFAULT-MVP")` passed.

# Follow-up

Recommended next package: add a focused UX/documentation pass for richer workbench report inputs once the safe-default preview surface has been reviewed, while preserving the no-dispatch/no-mutation boundary.
