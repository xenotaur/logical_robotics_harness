---
execution_id: 2026_10_11_04_31_38_LRH_MULTI_FOCUS_SUPPORT
prompt_id: PROMPT(AD_HOC:LRH_MULTI_FOCUS_SUPPORT)[2026-10-11T02:22:47+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/825
commit:
created_at: 2026-10-11T04:31:38+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md
session_transcript: pending
---

# Summary

Created design proposal PROP-LRH-MULTI-FOCUS-SUPPORT answering a handoff on whether LRH should support more than one simultaneous focus. Design note only; no code changed.

# Result

Wrote `project/design/proposals/proposed/lrh-multi-focus-support/00_proposal.md` (status: proposed, implementation_status: not_started). It documents seven current-state gaps in the single-focus model with `file:line` cites, evaluates options (a)-(d), checks `precedence_semantics.md`, and recommends fixing the baseline plus a read-only focus registry before considering multiple active foci. Corrected two points in the originating handoff (core_state.py path; `is_current_focus_related` drives no prioritization). Opened PR #825.

# Validation

- `lrh validate` (this worktree's source via PYTHONPATH=src): 0 errors, 0 warnings.
- Re-verified every cited line after fast-forwarding the worktree to origin/main (50f00813); cited source files unchanged since 979ac1e0.
- Reproduced paused-focus and missing-`current_focus.md` behavior on a scratch copy of `project/`. The single-error blanking effect is established from the code path, not isolated empirically (77 dangling `related_focus` errors accompanied it).

# Follow-up

- Recommended workstream (e.g. WS-LRH-FOCUS-MODEL) and work items per the proposal's Implementation Plan; not created here.
- Update `session_transcript` from `pending` to the durable session pointer.
- LCATS repository was not inspected; its interim guidance (umbrella focus) is unverified there.
