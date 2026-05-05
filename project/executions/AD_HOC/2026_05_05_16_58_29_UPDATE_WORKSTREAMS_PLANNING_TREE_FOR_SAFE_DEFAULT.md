---
execution_id: 2026_05_05_16_58_29_UPDATE_WORKSTREAMS_PLANNING_TREE_FOR_SAFE_DEFAULT
prompt_id: PROMPT(AD_HOC:UPDATE_WORKSTREAMS_PLANNING_TREE_FOR_SAFE_DEFAULT)[2026-05-05T12:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: pending
commit: pending
created_at: 2026-05-05T16:58:29+00:00
---

# Summary

Update the accepted workstreams/planning-tree proposal so it reflects
safe-default non-agentic core semantics, explicitly separates
human-assisted preparation from agentic execution, and aligns with the
companion safe-default packaging proposal.

# Result

Completed. The existing
`workstreams-and-recursive-planning-tree/00_proposal.md` umbrella
document was revised in place to:

- add a capability-boundary and safe-default-packaging alignment section
- clarify execution-ready terminology for work items/leaves
- replace default `lrh run` assumptions with core-vs-agentic execution
  boundary language
- extend non-goals with explicit no-autonomy/no-agent-adapter/no-sandbox
  guarantee statements for default core LRH
- split recommended follow-up into core and agentic tracks
- cross-reference
  `project/design/proposals/safe-default-agentic-extra-packaging/`
  as the companion capability-boundary proposal

# Validation

- `scripts/version tools`
- `lrh validate` (0 errors, 0 warnings)

# Follow-up

- Review and merge the proposal update.
- If accepted, propagate accepted wording into canonical design docs
  (`design.md`, `architecture.md`, `repository_spec.md`) in a follow-on
  change.
