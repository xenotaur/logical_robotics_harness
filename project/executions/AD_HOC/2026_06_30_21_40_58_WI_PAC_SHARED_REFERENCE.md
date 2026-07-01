---
execution_id: 2026_06_30_21_40_58_WI_PAC_SHARED_REFERENCE
prompt_id: PROMPT(AD_HOC:WI_PAC_SHARED_REFERENCE)[2026-06-30T21:38:28-04:00]
work_item: WI-PAC-SHARED-REFERENCE
status: landed
rerun_of: null
pr: https://github.com/xenotaur/logical_robotics_harness/pull/358
commit: b08b8d90
created_at: 2026-06-30T21:40:58-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-PAC-SHARED-REFERENCE.md
session_transcript: claude-app:cf151d13-af10-4a8c-9aac-9686b4c23234
---

# Summary

Implement `WI-PAC-SHARED-REFERENCE`: create the canonical prior-art-check
procedure at `src/lrh/skills/_shared/prior-art-check.md` (covering both
duplication search and demand search) and initialize
`project/design/backlog.md` with the deferred validator drift-check entry.
Also updated the WI itself to reflect the expanded scope (demand search added
during design-session refinement immediately before implementation).

# Result

- `src/lrh/skills/_shared/__init__.py` — created (Python package marker for the new `_shared/` directory)
- `src/lrh/skills/_shared/prior-art-check.md` — created; canonical procedure with two sub-searches:
  - **Duplication search** (in-repo / sibling-repo / external library) → verdict: proceed or block
  - **Demand search** (work items / proposals / backlog) → verdict: no action or offer to close/link
  - Recording instructions for each of the five skills
  - Escalation rules (duplication = stop; demand match = offer at report time)
- `project/design/backlog.md` — created; deferred validator drift-check entry
- `project/work_items/proposed/WI-PAC-SHARED-REFERENCE.md` — updated scope, summary, and acceptance criteria to include demand search

# Validation

- `lrh validate` — 0 errors, 0 warnings
- `scripts/*` not run — toolchain unavailable; all changes are markdown/text

# Follow-up

- `session_transcript: pending` — update to `claude-app:<uuid>` after session ends
- Per-skill copies of `prior-art-check.md` not yet created — that is `WI-PAC-DESIGN-SKILLS` and `WI-PAC-IMPL-SKILLS`
