---
execution_id: 2026_10_22_06_47_52_TAURSCRIPTS_HYBRID_LAYOUT
prompt_id: PROMPT(AD_HOC:TAURSCRIPTS_HYBRID_LAYOUT)[2026-10-22T01:03:20+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/848
commit: 6b01c284
agent: codex
instruction_source: project/design/proposals/proposed/taurscripts-hybrid-layout/00_proposal.md
session_transcript: pending
created_at: 2026-10-22T06:47:52+00:00
---

# Summary

Capture the durable Taurscripts hybrid source and installation layout decision
as an LRH design proposal, alongside the workstream that will implement it.

# Result

Created `PROP-TAURSCRIPTS-HYBRID-LAYOUT` in the proposed proposal bucket. The
proposal records the decision to preserve `bin/` as the stable installation
tree, add selective per-tool development areas, introduce a manifest-driven
installer, and defer generated staging until justified.

# Validation

- Prior-art duplication and demand searches completed with no blocking match.
- `lrh validate` completed with 0 errors and 0 warnings.
- `git diff --check` passed.

# Follow-up

Review and merge PR #848 with the companion workstream. Update the proposal's
implementation traceability as Taurscripts work items land.
