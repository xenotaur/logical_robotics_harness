---
execution_id: 2026_10_09_02_07_28_DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING_SELFREVIEW
prompt_id: PROMPT(AD_HOC:DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING_SELFREVIEW)[2026-10-09T02:07:24+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/802
commit:
created_at: 2026-10-09T02:07:28+00:00
agent: claude_app
instruction_source: "ad-hoc: lrh-self-review diff-mode from lrh-implement Step 7.5 for PROMPT(AD_HOC:DEPENDENCY_MAP_VIEW_ERRORS_NONBLOCKING)[2026-10-09T01:23:54+00:00]"
session_transcript: pending
---

# Summary

Diff-mode `/lrh-self-review` pass, run before the first push of the fix that
stops dependency-map view errors from blanking `core_state`. A cold-context
`general-purpose` subagent reviewed `git diff HEAD` against base `70750567`.
`origin/main` had advanced after branching, so the diff was taken against the
branch point, not `origin/main`. `rerun_of` stays empty by design, because
diff mode runs before the primary execution record exists.

# Result

Findings: 0 correctness bugs, 2 low, 2 nits.

- Low (applied): `DEPENDENCY_MAP_VIEW_ISSUE_CODES` duplicated the codes as
  string literals that the emit sites did not reference, so the set could
  drift from what is emitted. The invoking session re-checked this directly
  with `grep '"DEPENDENCY_MAP_VIEW_' src/lrh/control/validator.py`: literals
  at the emit sites, no use of the constant. Fixed with named code constants
  shared by the emit sites and the set.
- Low (not applied): `ux/dashboard.derive_operational_status` checks
  blockers before validation errors. A project with a bad view plus a
  blocked work item now reports BLOCKED instead of NEEDS_ATTENTION. Only
  tests call `project_summary_from_core_state`, and BLOCKED is arguably more
  accurate, so this was left as is.
- Nit (applied): without the fix, the new core_state test errored on
  `current_focus.id` instead of failing an assertion. Reordered so it fails
  an assertion.
- Nit (applied): renamed `_has_planning_errors` to
  `_has_state_blocking_errors`.

Mode: diff-mode. The fixes were applied by the `/lrh-implement` session after
direct verification, not through `--apply`. The subagent confirmed that no
planning loader reads `views/`, and that the new tests fail with the old
gate.

# Validation

After the fixes: `scripts/format --check --diff` clean, `scripts/lint` clean,
`scripts/test` 2130 tests OK, `lrh validate` 0 errors.

# Follow-up

None.
