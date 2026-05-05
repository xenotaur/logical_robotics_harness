---
execution_id: 2026_05_05_16_13_44_SAFE_DEFAULT_AGENTIC_EXTRA_PROPOSAL
prompt_id: PROMPT(AD_HOC:SAFE_DEFAULT_AGENTIC_EXTRA_PROPOSAL)[2026-05-05T11:35:54-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-05T16:13:44+00:00
---

# Summary

Added a focused design-only proposal set describing safe-default
non-agentic LRH installation and explicit opt-in agentic capability
via `lrh[agentic]` / `lrh-agentic`, including install semantics,
capability boundaries, CLI behavior, phased strategy, and future
validation expectations.

# Result

Created:

- `project/design/proposals/safe-default-agentic-extra-packaging/00_proposal.md`
- `project/design/proposals/safe-default-agentic-extra-packaging/README.md`

Updated:

- `project/design/proposals/README.md` with a minimal index pointer to
  the new proposal set.

No runtime implementation changes were made (no package split, no
module moves, no CLI behavior changes).

# Validation

- `lrh validate` (pass: 0 errors, 0 warnings)

# Follow-up

- Implement optional `lrh agentic` dispatch behavior and missing-extra
  guidance.
- Add install-mode smoke tests for default, extra, and direct-agentic
  package install paths.
- Decide later whether distribution/package splits are warranted after
  agentic runtime scope is concrete.
