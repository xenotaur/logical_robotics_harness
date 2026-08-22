---
execution_id: 2026_08_22_03_37_47_WI_LRH_MEMORY_TRANSFER_SAFETY
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_TRANSFER_SAFETY)[2026-08-22T03:35:57+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/597
commit: 8f40e33a6ba747029631e786c5cc264ef929222c
created_at: 2026-08-22T03:37:47+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-TRANSFER-SAFETY.md
session_transcript: claude-app:937464f4-d02a-4285-9bbf-f8411ebb09fe
---

# Summary

Created work item `WI-LRH-MEMORY-TRANSFER-SAFETY`, capturing two
correctness bugs in `lrh memory transfer`/`import` found live while
evaluating a hub-and-spoke memory-consolidation workflow: a bare relative
path silently misresolves as a corpus slug (silent no-op), and a
same-agent overwrite is unconditional with no snapshot (unlike `sync`'s
snapshot-before-overwrite invariant).

# Result

Ran the prior-art check (no duplicate in-repo, no matching proposal or
backlog entry); proposed the complete work item to the user for
confirmation before writing. Wrote
`project/work_items/proposed/WI-LRH-MEMORY-TRANSFER-SAFETY.md`, opened
PR #597. This is a planning artifact only -- no implementation in this
PR; the WI itself is the handoff for a separate session to pick up via
`/lrh-execute WI-LRH-MEMORY-TRANSFER-SAFETY`.

# Validation

`lrh validate` -- 0 errors, 0 warnings.
`lrh work-items readiness WI-LRH-MEMORY-TRANSFER-SAFETY` -- `prompt_ready: yes`.

# Follow-up

- A separate session will run `/lrh-execute WI-LRH-MEMORY-TRANSFER-SAFETY`
  to implement the fix and land PR #597 (or a follow-on PR, depending on
  how `/lrh-implement` branches).
- This WI deliberately does not implement the hub-and-spoke consolidation
  feature itself -- that requires its own design proposal, tracked
  separately.
