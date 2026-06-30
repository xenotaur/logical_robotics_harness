---
execution_id: 2026_06_29_20_05_40_WI_WORKFLOW_DOCS_READINESS_AUDIT_PROMPTING
prompt_id: PROMPT(WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING:WI_WORKFLOW_DOCS_READINESS_AUDIT_PROMPTING)[2026-06-29T19:55:17-04:00]
work_item: WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/354
commit: 193a71867816bdb71d80f44fb9080e0269387472
created_at: 2026-06-29T20:05:40-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING.md
session_transcript: claude-app:aee573a9-b59f-4250-8516-ff21741d32e2
---

# Summary

Document the end-to-end readiness/audit/prompting/reporting workflow after the
readiness CLI and ready-work-item request were implemented. Add a concrete
before/after example of a valid-but-not-ready vs ready/promptable work item and
cross-link the authoritative design note.

# Result

- Added "What makes a work item ready: examples" section to
  `docs/how-to/manage-work-item-lifecycle.md` with a before/after showing a
  valid-but-not-ready WI (missing Scope, Required Changes, Acceptance Criteria,
  Validation) vs a ready/promptable one, plus a cross-link to the design note.
- Updated `docs/reference/cli/work-items.md` "Related request surfaces" section
  with matching links to the how-to example and the design note.
- PR [#354](https://github.com/xenotaur/logical_robotics_harness/pull/354) opened.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.15
- `scripts/format --check --diff` — 174 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 688 tests OK
- `lrh work-items validate` — 0 errors, 3 pre-existing warnings (unrelated)
- `lrh work-items audit --format md` — passed
- `lrh work-items readiness --status proposed --format md` — passed
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` when session ends.
