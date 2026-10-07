---
execution_id: 2026_10_07_16_21_20_LRH_CONSOLE_L1_WORK_ITEMS
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_L1_WORK_ITEMS)[2026-10-07T16:20:47+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/782
commit:
agent: "claude_app"
instruction_source: "user request in session: \"Approve the list; write them in one planning PR\""
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-07T16:21:20+00:00
---

# Summary

This record covers the planning PR for the eight LRH Console L1 work items. The owner approved
the list in this session ("Approve the list; write them in one planning PR"). The items
implement the Revision 2 decisions of `PROP-LRH-CONSOLE-VISUAL-LANGUAGE` (PR #781) and the L1
gate of the local-dogfood proposal.

# Result

- Added eight work items in `project/work_items/proposed/`, appended in execution order to
  `WS-LRH-CONSOLE-LOCAL-DOGFOOD`'s `work_items:` list. In order: TOKENS, THEME, FRAME,
  MAP-SNAPSHOT, MAP-STATIC, INTERACTIVE, STATUSBOARD, and L1-DOGFOOD (`operation`).
- The dependencies match the approved list. The excluded items stay out: the waived L0 checks,
  Back on the Delete key, `scripts/clean --desktop`, and effort estimates.

**Pre-push cold review.** A subagent compared the items with the approved list and the
proposals, and checked every citation. It found 3 must-fix items, 5 should-fix items and 6 nits.
All were applied except nit 14, which is flagged in the PR:

- INTERACTIVE is narrowed to tracing, filters, and the theme switch, matching Q8.
- THEME cites the sixth hard-coded theme (`serve.py:1500`) and adds `needs_restart`.
- The L1 gate quote is cited at `:307`, verbatim.
- *(recommended)* tags were added for the title bar and the line styles.
- The search slot in FRAME is left out of scope because of the CSP.
- The LCATS view is a separate, owner-authorized LCATS PR.
- L1-DOGFOOD matches its sibling's forbidden actions and evidence.

# Validation

- `lrh validate`, run from this worktree's `src`: 0 errors, 0 warnings. The
  `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` warning is cleared.
- `lrh work-items readiness` reports `prompt_ready: yes` for all eight.
- `git diff --check` is clean.

# Follow-up

- Land this PR with `/lrh-land`.
- Then execute the items with `/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD`, starting with TOKENS.
