---
execution_id: 2026_08_07_19_56_40_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION_SELFREVIEW)[2026-08-07T19:56:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_07_16_17_43_WI_LAND_PRIMARY_RECORD_SUFFIX_COLLISION
pr: https://github.com/xenotaur/logical_robotics_harness/pull/508
commit: 0b21d28
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/508
session_transcript: pending
created_at: 2026-08-07T19:56:40+00:00
---

# Summary

PR-mode `/lrh-self-review` pass on PR #508 commit `0b21d28`, substituting
for a bot-retrigger round per the new fleet-wide policy (Codex credits
near monthly exhaustion — `feedback_never_manually_retrigger_github_bots`
in agent memory). This is round-cap `completed_count` batch 3.

# Result

Dispatched a cold-context `general-purpose` subagent to review the
cumulative PR #508 diff at commit `0b21d28`, given the prior 3 rounds'
context (orphan-record misclassification, repo-wide base-slug scoping,
review-response's stale glob). Found one real, serious regression:

**Round 3's glob fix regressed `rerun_of` for the PR's own motivating
case.** Aligning `lrh-review-response/SKILL.md`'s candidate glob to a
trailing-exact form (fixing Copilot's substring-collision concern)
structurally prevents that glob from ever matching a genuine sibling
side record when the target's own slug ends in a reserved suffix (a
sibling's slug is always `UPPER_SLUG` plus more, never exactly
`_${UPPER_SLUG}.md`) — sibling elimination becomes impossible, and the
record is wrongly downgraded to `$ambiguous`. Independently re-verified
by hand-tracing the actual algorithm against
`project/executions/AD_HOC/2026_08_02_15_14_34_WI_SKILLS_LRH_SELF_REVIEW.md`
and its real `_CONFIRM` sibling: confirmed the glob returns only 1
candidate, no sibling available, `$ambiguous` fires incorrectly. Also
found two lower-severity issues: `lrh-confirm-fixes` was left using the
broad substring glob (the same form Copilot flagged for
`lrh-review-response`) while `lrh-review-response` used trailing-exact —
an unaddressed cross-site inconsistency; and
`project/design/proposals/proposed/lrh-land-execute/00_proposal.md`
Decision 3 still described the pre-fix bare-suffix-exclusion rule.

Fixed by designing a distinct algorithm for these two `rerun_of` sites
(target-verification: gather candidates broadly via substring glob so a
genuine sibling is never excluded, but classify only the one candidate
whose slug exactly equals `UPPER_SLUG`), rather than reusing `/lrh-land`
Step 1's classify-every-candidate shape. A first attempt at this same
idea (classify-then-post-filter) also broke — an unrelated
substring-matching unsuffixed candidate could seize the primary slot
before the filter ran — caught and fixed before landing. Also fixed the
proposal's stale Decision 3 text.

# Validation

- Ran the exact bash extracted from the committed `land-workflow.md`
  file (not a paraphrase) against all four cases: the real self-review
  collision (PR #464), the doubled-suffix `ADOPT_PROP` case, the real PR
  #347 orphan, and a no-exact-match case — all four resolve correctly
- `diff -r` on all three skill mirror pairs → zero output
- `scripts/format --check --diff`, `scripts/lint` → clean
- `lrh validate` → 0 errors, 1 pre-existing unrelated warning

# Follow-up

Suggest re-running `/lrh-confirm-fixes https://github.com/xenotaur/logical_robotics_harness/pull/508`
before merge.
