---
execution_id: 2026_08_08_05_28_56_REVIEW_WAIT_POSTURE
prompt_id: PROMPT(AD_HOC:REVIEW_WAIT_POSTURE)[2026-08-08T05:06:37+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/522
commit: e9de72e1730089c95df1dc300d0ce17b7c2a6108
created_at: 2026-08-08T05:28:56+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/review-wait-posture/00_proposal.md
session_transcript: claude-app:529191fc-e38a-4928-baf0-3196753dda62
---

# Summary

Ran `/lrh-design` to reassess the review-wait posture across `/lrh-land`,
`/lrh-confirm-fixes`, and `/lrh-review-response` now that bot-triggered
review (Codex/Copilot) can no longer be assumed available on demand (fleet
at 1/7 monthly Codex credits, 2026-08-07), then `/lrh-proposal` to capture
the resulting design as `PROP-REVIEW-WAIT-POSTURE`.

# Result

Authored and pushed `project/design/proposals/proposed/review-wait-posture/00_proposal.md`
(`id: PROP-REVIEW-WAIT-POSTURE`, `status: proposed`) to this PR. The design pass
grounded itself in real, cited in-repo evidence rather than inventing a
gap: `round-cap-gate.md`'s three-way gate already offers self-review as a
fourth answer but only past a ceiling of 3 real bot rounds; the
`self_review_preference` field in `project/config/chain-defaults.yaml` is
persisted but confirmed unconsumed by PR #512's own `_CONFIRM` record;
`PROP-LRH-SELF-REVIEW` Decision 4 explicitly defers "later-round skip
policy" as future work; and `backlog.md`'s "Self-review-first tier..."
entry names this exact gap as its unresolved Open Question 4. The proposal
also formalizes a bounded-poll wait mechanism (`Bash` +
`run_in_background: true`, reusing `round-cap-gate.md`'s existing
`STALE_AGE_SECONDS=900`) to replace an improvised `ScheduleWakeup` call
from an earlier session that worked once but is outside that tool's
documented `/loop`-scoped contract.

Five design decisions were recorded: (1) invert the Step 8 default to
self-review-first, bot retrigger as an opt-in exception, leaving
`PROP-LRH-SELF-REVIEW` Decision 4's first-round guarantee untouched; (2)
wire (but do not invent the value-space literals for) `self_review_preference`,
deferring exact naming to a required steelmanning session per
`WS-LRH-CHAIN-DEFAULTS`'s own established practice; (3) specify the
bounded-poll wait mechanism; (4) no automated credit/budget gate, since
GitHub exposes no such API; (5) scope this increment to Claude Code
sessions only, since `/lrh-self-review`'s dispatch mechanism is
Claude-Code-specific.

Deliberately deferred rather than invented in this proposal: the exact
new `self_review_preference` value-space literals, and whether any
periodic/final-pre-merge round keeps a mandatory real bot pass for
cross-vendor blind-spot coverage — both require a dedicated steelmanning
session, the user's own explicit choice during this run's interview
(over settling them in the same conversation).

`gh pr create` with a heredoc-piped `--body` initially stalled/failed
silently (a known heredoc-vs-backtick-heavy-markdown failure mode,
matching this project's own recorded `feedback_pr_body_file` guidance);
retried successfully using `--body-file` against a scratch file.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`, unrelated to this change)
- Manual review: proposal frontmatter checked against
  `references/proposal-schema.md` (required fields, status/bucket match,
  `implementation_status: not_started`); prior art check (duplication +
  demand search) run and recorded in the proposal body before drafting
  Design Decisions

# Follow-up

- Required steelmanning session to settle `self_review_preference`'s new
  value-space literals and the periodic/final-round bot-pass question
  (proposal's Open Questions and Implementation Plan step 1)
- `WI-DEC-REVIEW-WAIT-POSTURE-AMENDMENT` (or similarly named) to produce
  the `DEC-*` decision-log entry narrowing `PROP-LRH-SELF-REVIEW`
  Decision 4's neighborhood, required before implementation
  (Implementation Plan step 2)
- Implementation work item, to be filed once the above land, covering
  `round-cap-gate.md` Step 8.1 rewiring and wait-mechanism documentation
  across `src/lrh/skills/` and `.claude/skills/` mirrors
  (Implementation Plan step 3)
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after this session ends
