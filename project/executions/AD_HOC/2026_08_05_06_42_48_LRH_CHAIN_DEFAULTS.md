---
execution_id: 2026_08_05_06_42_48_LRH_CHAIN_DEFAULTS
prompt_id: PROMPT(AD_HOC:LRH_CHAIN_DEFAULTS)[2026-08-05T06:41:03+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/490
commit: ff89ec6d54aebed60b04f61dba76cb21b8dd114d
created_at: 2026-08-05T06:42:48+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Filed `PROP-LRH-CHAIN-DEFAULTS`, a design proposal for a persisted,
user-editable chain-defaults profile covering completion/stop-work
conditions, self-review-vs-bot-retrigger preference, and per-gate
autopilot policy across LRH's chain-running skills. Follows an inline
`/lrh-design` pass in the same session that surveyed prior art
(`WI-REVIEW-ROUND-ESCALATION-GATE`'s escalation-gate precedent,
`round-cap-gate.md`'s durable-state pattern) and best practices
(plan/apply separation, `sudo` timestamp caching, CI auto-merge,
progressive disclosure) before drafting the design decisions.

# Result

Created `project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md`,
opened PR #490. Confirmed no duplicate proposal or work item exists.
Five design decisions recorded: repo-level git-tracked YAML storage;
two-tier (chain-level + per-gate) structure; categorical exclusion of
the merge and chain-initiation gates from any autopilot tier;
per-invocation overrides never silently persist; staleness fallback to
`always_ask` when a gate's own skill logic has changed materially since
the profile was confirmed. Concrete default values were deliberately
left as an Open Question, per the user's explicit request for a
dedicated design-review session to steelman them before Increment 1
ships, rather than this proposal hard-coding example values as
defaults.

# Validation

- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- Next: `/lrh-workstream` to frame the two-increment delivery plan
  (chain-level defaults, then per-gate autopilot), per the user's
  stated order ("proposal first, then the workstream").
- A dedicated design-review session to steelman concrete default
  values is required before Increment 1 implementation begins (per
  this proposal's Open Questions section) — not yet scheduled.
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` before archiving.
