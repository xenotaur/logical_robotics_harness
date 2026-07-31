---
execution_id: 2026_07_31_21_08_14_WI_REVIEW_LANDED_CANONICAL_CHECK_REVIEW
prompt_id: PROMPT(AD_HOC:WI_REVIEW_LANDED_CANONICAL_CHECK_REVIEW)[2026-07-31T21:04:13+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_31_20_10_56_WI_REVIEW_LANDED_CANONICAL_CHECK_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/447
commit: f427824
created_at: 2026-07-31T21:08:14+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/447
session_transcript: claude-app:d4183878-ad9c-4bb6-80c3-dcd5aa45e103
---

# Summary

Round 3 of review-response on PR #447, addressing 2 new Codex P1 findings
on the round-2 `_CONFIRM` commit (`b7543dc`), plus a self-caught
inaccuracy discovered while fixing them.

# Result

- Human decision at this round's gate: stop retriggering/waiting on
  Copilot going forward (2 consecutive commits with no response despite
  explicit retrigger — treated as expected behavior, not a blocker); fix
  Codex's 2 new findings.
- Codex finding 1 ("Paginate the canonical review fetch"): the round-2
  REST reviews snippet omitted `--paginate`; the endpoint's `per_page=30`
  default risks silent truncation on PRs with >30 reviews. Added
  `--paginate` to the prescribed command everywhere it appears.
- Codex finding 2 ("Treat formal review bodies as REST reviews"): round 2
  conflated formal review bodies (which carry a real `commit_id` via the
  REST endpoint) with genuine issue comments (which don't) under one
  "SHA-matched text" bucket. Split them: `commit_id` correlation for
  formal reviews, SHA-text-matching reserved for the no-thread
  issue-comment case only.
- **Self-caught defect, not reviewer-flagged**: while fixing finding 2,
  grepped `lrh-confirm-fixes/SKILL.md` for `commit_id` and got zero
  matches — the WI had claimed, across all three rounds, that this skill
  "already performs the commit_id REST check." False. Verified its
  actual mechanism (`SKILL.md:363-364,389`) matches every response —
  reviews and issue comments alike — by SHA-text-citation only, with no
  `commit_id` check anywhere. Corrected every occurrence of this claim in
  Problem/Context, Scope, and Required Changes: the `commit_id` REST
  check is new work this item introduces to all three skills, not
  existing practice to cite. This inverts part of Required Change 3's
  framing (add the check, rather than "cite the pattern already
  followed").

# Validation

- `scripts/format --check --diff`: clean, 179 files unchanged
- `scripts/lint`: all checks passed
- `scripts/test`: 808 tests, OK
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)
- `grep -n "commit_id" .claude/skills/lrh-confirm-fixes/SKILL.md`: 0
  matches, confirming the self-caught correction

# Follow-up

- Next step in the `/lrh-land` chain: `/lrh-confirm-fixes` Step 2 onward
  against the new HEAD (`f427824`).
- Round-1 poll script bug (`poll_pr447_step8.sh`) root-caused this round:
  it filtered Copilot's REST review by the bare login
  `copilot-pull-request-reviewer`, but REST returns
  `copilot-pull-request-reviewer[bot]` (GraphQL's `author.login` omits
  the suffix; REST's `user.login` keeps it) — the filter never matched.
  Fixed in `poll_pr447_step8_r2.sh`. Worth a memory entry: this
  REST-vs-GraphQL bot-login inconsistency is generalizable beyond this
  PR and could silently break any future login-based filtering.
- Escalating review rounds on this PR (3 rounds, each finding real
  issues in the prior round's fix) closely mirror
  `WI-REVIEW-ROUND-ESCALATION-GATE`'s own motivating incident
  (PR #442, 14 unbounded retrigger rounds). No round cap exists yet
  (that WI is still `proposed`); this PR proceeded on explicit
  per-round human confirmation instead. Worth citing as a second,
  independent data point for that WI when it's implemented.
