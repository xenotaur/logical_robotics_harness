---
execution_id: 2026_10_13_00_08_26_LRH_CONSOLE_MAP_FILTER_COLLAPSE_CLOSEOUT_NOTE
prompt_id: PROMPT(WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE:LRH_CONSOLE_MAP_FILTER_COLLAPSE_CLOSEOUT_NOTE)[2026-10-13T00:08:26+00:00]
work_item: WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE
status: landed
rerun_of: 2026_10_12_21_21_39_LRH_CONSOLE_MAP_FILTER_COLLAPSE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/835
commit: 4d4efd8751909bd8f6d53446ccbfc24b33771f22
created_at: 2026-10-13T00:08:26+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/835
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This is the closeout note for PR #835, which implemented `WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` through
`/lrh-execute MAP-FILTER-COLLAPSE`. The primary record's body is immutable, so the chain note lives
here instead.

# Result

CHAIN-NOTE: `cycles=1; stops=0; gates=[execute-chain, land-chain, review-response, owner-check, owner-changes, owner-recheck, small-fixes, confirm-fixes, merge]; friction=owner-found-confusing-filter-results; self_review_rounds=4; bot_rounds=1; note="This moved dependency-map filtering to the server. ?hide=<state>,... drops hidden cards before layout, so the map collapses: lanes and phases the filter empties disappear and lines re-route. On LCATS worldcon-2026 with Done hidden, the map went from 50 cards in 5 lanes (1948x3618 px) to 11 cards in 4 lanes (1596x932 px). The selection and unfinished needs stay visible. The Show toggles are plain links, every in-page link keeps the filter, and a note counts what is hidden with Show all. The pre-push review led to 5 fixes. Of the bot threads, 3 were fixed, including a Codex bug where tracing broke across hidden items; the map now carries its full edge list. The owner's Mac check found that the table kept Done rows from outside the view, and that a map left with no lines did not explain why. The table now filters outside rows and counts them, and cards show +N upstream hidden by filters. The owner's re-check passed, and 5 small review points were fixed at the owner's request. CI passed 8/8, and the merge was SHA-locked."`

PR #835 merged as `4d4efd8751909bd8f6d53446ccbfc24b33771f22`, using
`--match-head-commit 2034dd04`, after authorization in this session. Five records landed with that
commit, through `lrh prompt update-execution`: the primary, `_REVIEW`, `_OWNER_CHECK`, `_CONFIRM`,
and the pre-push `AD_HOC` `_SELFREVIEW`.

`WI-LRH-CONSOLE-MAP-FILTER-COLLAPSE` moved to `resolved/` with a resolution note.
`WS-LRH-CONSOLE-LOCAL-DOGFOOD` stays active.

# Validation

- `lrh validate` was run after these closeout edits. See the closeout commit.

# Follow-up

- Before L2, per the owner-confirmed L1 verdict: `WI-LRH-CONSOLE-READINESS-VOCABULARY`.
- Follow-up candidate: in a window about 1024 px wide, the drawer covers the rightmost lane, so a selected card there sits under it. This predates the PR.
- Without scripts, the page does not scroll to the selected card after a filter change.
