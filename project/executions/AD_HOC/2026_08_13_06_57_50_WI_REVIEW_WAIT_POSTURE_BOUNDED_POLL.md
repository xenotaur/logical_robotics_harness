---
execution_id: 2026_08_13_06_57_50_WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL
prompt_id: PROMPT(AD_HOC:WI_REVIEW_WAIT_POSTURE_BOUNDED_POLL)[2026-08-13T06:55:41+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/549
commit: 02c5eacc
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL.md
session_transcript: pending
created_at: 2026-08-13T06:57:50+00:00
---

# Summary

Ran `/lrh-work-item` to file `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL`,
following up on the outstanding "file a work item for Decision 3's
implementation" note from `PROP-REVIEW-WAIT-POSTURE` (PR #522, merged
earlier in this same session).

# Result

Created `project/work_items/proposed/WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL.md`,
`related_workstreams: [WS-INVOCATION-AND-GATE-RESET]`. Before drafting,
checked the current state of `round-cap-gate.md`, `confirm-fixes-workflow.md`,
and `land-workflow.md` directly rather than assuming Decision 3 was still
fully open — confirmed `WI-RETRIGGER-REMOVAL-STAGE1` (resolved, PR #545)
had already rescoped `PROP-REVIEW-WAIT-POSTURE` itself (closing Decisions
1 and 2 as obviated) but had not touched the wait-mechanism gap: grepping
the current skill files for any poll/sleep/background construct found
none.

**A scope question surfaced and was resolved live with the user before
drafting:** `PROP-INVOCATION-AND-GATE-RESET`'s own Non-Goals state "Does
not resolve the round-cap gate's final shape... the canonical replacement
is Stage 4 scope, informed by real post-Stage-1 evidence" — Stage 4 being
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` plus a new Increment 3, owned by
`WS-LRH-CHAIN-DEFAULTS`, explicitly excluded from
`WS-INVOCATION-AND-GATE-RESET`'s scope. `round-cap-gate.md`'s own
"Historical risk notes" similarly flag a "persistent reviewer-wait
primitive" as future-stage work. Rather than either filing the whole of
Decision 3 (risking preempting Stage 4's evidence-gated policy design) or
blocking entirely on Stage 4, split it: the CI-wait predicate (needed
regardless of round-cap policy, independent of self-review-round
evidence) is in scope now; the bot-response-wait predicate (tied to the
round-cap/no-progress-counting redesign Stage 4 owns) is explicitly
deferred and named as such in the WI's own Non-Goals and acceptance
criteria, so a future reader doesn't assume this WI closes Decision 3 in
full.

Prior art check: no duplicate implementation found (grepped current skill
files directly); no other open work item claims this scope; demand is
recorded directly in `PROP-REVIEW-WAIT-POSTURE` Decision 3's own
already-`bash -n`-verified loop shape.

# Validation

- `PYTHONPATH="$(pwd)/src" lrh validate`: 0 errors, 1 pre-existing
  unrelated warning (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`, unrelated to this change)
- Manual review: frontmatter checked against
  `references/work-item-schema.md`; confirmed `status: proposed` and
  `proposed/` bucket placement match; confirmed no existing
  `WI-REVIEW-WAIT-POSTURE-BOUNDED-POLL.md` before writing (both at Step 1
  and again after the fresh `main` pull at Step 6)

# Follow-up

- Implementation itself (editing `confirm-fixes-workflow.md`,
  `lrh-land/SKILL.md`, `land-workflow.md`, and their `.claude/`/`.agents/`
  mirrors) is this WI's own future work, not done in this PR.
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after this session ends.
