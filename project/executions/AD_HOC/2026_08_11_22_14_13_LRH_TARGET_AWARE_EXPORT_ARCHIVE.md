---
execution_id: 2026_08_11_22_14_13_LRH_TARGET_AWARE_EXPORT_ARCHIVE
prompt_id: PROMPT(AD_HOC:LRH_TARGET_AWARE_EXPORT_ARCHIVE)[2026-08-11T22:13:55+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/542
commit: c31e1086804fdaef2a1655d1a4cf20d449b492a7
created_at: 2026-08-11T22:14:13+00:00
agent: codex_app
instruction_source: project/design/proposals/proposed/lrh-target-aware-export-archive/00_proposal.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Create a proposed LRH design artifact for a target-aware `/lrh-export` skill and
private conversation archive infrastructure. The proposal captures the
date-first Promptspace-style "B-plus" archive layout, target-aware export
dispatch, archive sorting CLI shape, machine-readable indexes, and private
non-authoritative safety boundary.

# Result

Added
`project/design/proposals/proposed/lrh-target-aware-export-archive/00_proposal.md`
with frontmatter for `PROP-LRH-TARGET-AWARE-EXPORT-ARCHIVE` and body sections
covering summary, motivation, prior-art check, design decisions, non-goals,
implementation plan, cross-references, and open questions.

The proposal was first drafted locally for iteration, then revised after
inspecting the actual Promptspace directory shape and confirming that
`~/.local/share/lrh` had no populated session archive to preserve. The final
draft chooses a date-first human-facing archive under a configurable private
root, backed by root-level indexes, rather than preserving the unused
machine-first `raw/` / `exports/` archive-root layout as canonical.

# Validation

- `lrh validate` — passed with 0 errors and the pre-existing
  `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` warning for
  `WS-SESSION-ARCHIVE-SYNC`.
- `lrh prompt check-execution --slug lrh-target-aware-export-archive --work-item AD_HOC --project-root .`
  — reported no prior execution record for this slug.

# Follow-up

- Review the proposal and decide whether to adopt it as the governing design.
- If adopted, create/update a workstream and work items for archive contract and
  configuration, archive sorter CLI, archive list/inspect commands,
  target-aware `/lrh-export`, and Promptspace dogfood.
- Resolve the remaining naming/configuration questions for the private archive
  root and whether Claude `/export` zips are copied by default or only with an
  explicit option.
