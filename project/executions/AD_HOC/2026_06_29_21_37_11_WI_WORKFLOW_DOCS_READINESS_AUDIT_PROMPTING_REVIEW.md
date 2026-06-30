---
execution_id: 2026_06_29_21_37_11_WI_WORKFLOW_DOCS_READINESS_AUDIT_PROMPTING_REVIEW
prompt_id: PROMPT(AD_HOC:WI_WORKFLOW_DOCS_READINESS_AUDIT_PROMPTING_REVIEW)[2026-06-29T20:17:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_06_29_20_05_40_WI_WORKFLOW_DOCS_READINESS_AUDIT_PROMPTING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/354
commit: 193a71867816bdb71d80f44fb9080e0269387472
created_at: 2026-06-29T21:37:11-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/354
session_transcript: claude-app:aee573a9-b59f-4250-8516-ff21741d32e2
---

# Summary

Address one open review comment on PR #354: the "valid but not ready" readiness
output example did not match actual `lrh work-items readiness` CLI output.
Also diagnosed and fixed an unrelated CI failure: PR #353 (merged after our
earlier closeout) reintroduced stale `proposed/` copies of three already-resolved
work items, causing a duplicate-work-item-id test failure.

# Result

- Fixed: corrected the example readiness output in
  `docs/how-to/manage-work-item-lifecycle.md` to match the literal strings from
  `src/lrh/assist/work_item_prompt_core.py` (`missing Scope section`, `missing
  Required Changes section`, `missing Acceptance Criteria`, `missing Validation
  commands`) and backtick-wrapped `prompt_ready`. One comment addressed; none
  skipped.
- Out-of-band fix (reported separately, not a review comment): removed stale
  `project/work_items/proposed/` copies of `WI-REQUEST-READY-WORK-ITEM-MVP`,
  `WI-WORK-ITEM-READINESS-DESIGN`, and `WI-WORK-ITEMS-READINESS-CLI-MVP` from
  `main` (commit `fcb294a`) that PR #353 had reintroduced after our earlier
  closeout. Rebased this PR branch onto the fixed main and force-pushed
  (force-with-lease) to restore green CI.

# Validation

- `scripts/format --check --diff` — 174 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 688 tests OK
- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` when session ends.
