---
execution_id: 2026_05_18_02_11_56_DESIGN_ALIGNMENT
prompt_id: PROMPT(WI-WORK-ITEM-READINESS-DESIGN:DESIGN_ALIGNMENT)[2026-05-17T02:04:00-04:00]
work_item: WI-WORK-ITEM-READINESS-DESIGN
status: in_progress
rerun_of: null
pr: null
commit: null
created_at: 2026-05-18T02:11:56+00:00
---

# Summary

Design-alignment run for the work-item readiness workflow. The run adds a design note for the gap
between valid work items and prompt-ready work items, records `WI-ASSIST-INSTALLABILITY-HARDENING` as
the motivating dogfood case, and creates follow-up work items for the readiness CLI, ready-work-item
request, and workflow documentation.

# Result

- Added `project/design/work_item_readiness_workflow.md` as the design artifact for lifecycle
  vocabulary and command boundaries.
- Updated the main design document and work-item README with concise references to the readiness
  boundary.
- Added `WI-WORK-ITEM-READINESS-DESIGN`, `WI-WORK-ITEMS-READINESS-CLI-MVP`,
  `WI-REQUEST-READY-WORK-ITEM-MVP`, and `WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING`.
- Linked the readiness work items from `WS-EXECUTION-FRAMEWORK`.

# Validation

- `scripts/version tools` — passed; Black and Ruff are available in the task environment.
- `scripts/test` — passed, 529 tests.
- `scripts/lint` — passed.
- `scripts/format --check` — passed.
- `lrh work-items validate` — passed, 0 errors and 0 warnings.
- `lrh work-items audit --format md` — passed; it reports one informational lifecycle finding because
  this non-terminal work item now has the required execution record.
- `lrh validate` — passed, 0 errors and 0 warnings.

# Follow-up

After this PR lands, update this execution record to `landed` and fill in `pr` and `commit` metadata.
Implementation remains deferred to the follow-up work items listed above.
