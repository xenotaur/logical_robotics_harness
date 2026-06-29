---
execution_id: 2026_05_18_19_25_08_IMPLEMENT_READINESS_CLI
prompt_id: PROMPT(WI-WORK-ITEMS-READINESS-CLI-MVP:IMPLEMENT_READINESS_CLI)[2026-05-17T02:06:00-04:00]
work_item: WI-WORK-ITEMS-READINESS-CLI-MVP
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/268
commit: 8e2e00ee54d661d881bce9114758b86ff539b9e8
session_transcript: pending
created_at: 2026-05-18T19:25:08+00:00
---

# Summary

Implemented an MVP `lrh work-items readiness` CLI command with deterministic markdown/json reporting and shared prompt-readiness diagnostics.

# Result

Added a new work-item readiness module, wired CLI parsing/dispatch, added unit/CLI tests, and updated work-item documentation to describe readiness as advisory and distinct from validation.

# Validation

- scripts/version tools
- scripts/test
- scripts/lint
- scripts/format --check
- lrh work-items validate
- lrh work-items audit --format md
- lrh work-items readiness WI-ASSIST-INSTALLABILITY-HARDENING
- lrh work-items readiness --status proposed --format md
- lrh work-items readiness --status proposed --format json
- lrh validate

# Follow-up

Populate `pr` and `commit` after merge workflow finalization.
