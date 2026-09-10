---
execution_id: 2026_07_31_20_01_01_WI_REVIEW_ROUND_ESCALATION_GATE_COPILOT_WORDING
prompt_id: PROMPT(AD_HOC:WI_REVIEW_ROUND_ESCALATION_GATE_COPILOT_WORDING)[2026-07-31T19:59:36+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/450
commit: 9d42c5013aa5d829352d3f1c5e852bcdb71e467f
created_at: 2026-07-31T20:01:01+00:00
agent: claude_app
instruction_source: 'ad_hoc conversation — user asked to fix the stale @copilot review example in WI-REVIEW-ROUND-ESCALATION-GATE.md, flagged but not fixed at the end of the PR #446 land'
session_transcript: claude-app:9e68ac13-8d87-42d3-bbd2-3997bd762717
---

# Summary

Fix a stale `@copilot review` comment-mention example in
WI-REVIEW-ROUND-ESCALATION-GATE.md's "round" definition, left unfixed at
the end of the PR #446 land (a different concern — that PR fixed the
actual retrigger command, this WI's prose just illustrated the old one).

# Result

Updated the "Define 'round' as..." bullet in
`project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md` (moved to
`resolved/` by a separate concurrent session mid-task, via PR #445, while
this fix was in flight — carried over cleanly through git's rename
detection on `git pull` + `stash pop`) to describe both current retrigger
mechanisms: `@codex review` (still a comment mention) and
`gh pr edit --add-reviewer @copilot` (a reviewer request, per PR #446).

# Validation

```
lrh validate — 0 errors, 1 pre-existing unrelated warning
```

# Follow-up

- None. This is a documentation-only wording fix with no functional
  change to the round-cap gate mechanism itself.
