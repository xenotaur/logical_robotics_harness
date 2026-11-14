---
execution_id: 2026_11_14_01_43_14_WI_LRH_FOCUS_ACTIVE_LEAF_DECOUPLE
prompt_id: PROMPT(AD_HOC:WI_LRH_FOCUS_ACTIVE_LEAF_DECOUPLE)[2026-11-13T01:06:45+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/875
commit:
created_at: 2026-11-14T01:43:14+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE.md
session_transcript: claude-app:017c7be3-d288-4b60-becf-c31f8f62ebd6
---

# Summary

Created WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE: make is_active_leaf focus-independent (proposal Decision 2).

# Result

Wrote project/work_items/proposed/WI-LRH-FOCUS-ACTIVE-LEAF-DECOUPLE.md with problem context cited to core_state.py, planning_tree.py, serve.py and dashboard.py, four acceptance criteria and the expected test files.

# Validation

- `lrh validate`: 0 errors, 0 warnings. `scripts/lint`: pass.
- Cited `file:line` references and every `artifacts_expected` path were checked against the working tree before commit.
- Written and confirmed in the same combined PR (#875) as the other two planning artifacts.

# Follow-up

- Review-response, confirm-fixes and closeout for PR #875 land this record; `/lrh-closeout` updates its status.
- The deferred proposal decisions (focus registry and `lrh serve` focus views, resolver disposition, multi-active foci) are recorded in `WS-LRH-FOCUS-MODEL` and are not work items yet.
