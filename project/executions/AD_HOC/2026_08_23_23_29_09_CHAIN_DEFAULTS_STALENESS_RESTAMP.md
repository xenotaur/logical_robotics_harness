---
execution_id: 2026_08_23_23_29_09_CHAIN_DEFAULTS_STALENESS_RESTAMP
prompt_id: PROMPT(AD_HOC:CHAIN_DEFAULTS_STALENESS_RESTAMP)[2026-08-23T23:27:52+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-CHAIN-DEFAULTS-STALENESS-RESTAMP.md
session_transcript: pending
pr: 
commit: 
created_at: 2026-08-23T23:29:09+00:00
---

# Summary

Creates `WI-CHAIN-DEFAULTS-STALENESS-RESTAMP`, capturing a gap found live
this session: the chain-defaults staleness fallback's own governing text
never re-stamps `confirmed_commit`/`confirmed_at` after a live
reconfirmation of unchanged values, only on first encounter or on
divergence -- so the fallback re-fires forever even after being
explicitly answered.

# Result

Wrote `project/work_items/proposed/WI-CHAIN-DEFAULTS-STALENESS-RESTAMP.md`.
Deliberately **not pushed and no PR opened yet**, per explicit user
request, in case further issues surface during the concurrent
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` implementation that should be folded
into this WI before it's finalized.

# Validation

- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Push this branch (`xenotaur/feat/wi-chain-defaults-staleness-restamp`)
  and open the PR once the user confirms nothing further needs folding in.
- `session_transcript: pending` should be updated to the durable session
  pointer before archiving.
