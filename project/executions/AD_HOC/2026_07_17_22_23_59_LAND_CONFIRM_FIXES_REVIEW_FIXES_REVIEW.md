---
execution_id: 2026_07_17_22_23_59_LAND_CONFIRM_FIXES_REVIEW_FIXES_REVIEW
prompt_id: PROMPT(AD_HOC:LAND_CONFIRM_FIXES_REVIEW_FIXES_REVIEW)[2026-07-17T20:50:54-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/398
commit: 3b1dde5f0394e873aee04994ae8d4bf77a099c1c
created_at: 2026-07-17T22:23:59-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/398
session_transcript: claude-app:49a80683-68ef-40ff-a81c-28253a11ca8e
---

# Summary

Address 2 findings (3 comments) on PR #398 (follow-up PR landing the
`/lrh-confirm-fixes` review fixes that PR #397 merged without) via
`/lrh-review-response`.

# Result

Both findings passed presence/validity/feasibility triage and were fixed:

1. **copilot-pull-request-reviewer (x2)** — the `--mode raw` JSON example in
   `confirm-fixes-workflow.md` included fabricated `path`/`line` fields.
   Verified empirically by live-running `lrh github threads --mode raw
   --state all` against PR #398 itself: real thread keys are exactly
   `{comments, id, isOutdated, isResolved}` — no `path`/`line`/`startLine`
   at all, since the underlying `get_pull_review_threads()` query never
   requests them. Fixed the example and documented that thread location
   must come from `gh pr diff` + comment body instead.
2. **chatgpt-codex-connector, P1** — `lrh github threads --state unresolved`
   (introduced in the prior review round to fix a pagination bug) requires
   *both* `not isResolved` and `not isOutdated`
   (`_matches_state` in `formatters.py`), silently dropping threads whose
   commented-on diff line moved but which GitHub still considers unresolved
   — exactly the threads a verification pass most needs to see. This was a
   regression introduced by the previous round's own fix. Switched to
   `--state all` + client-side `isResolved == false` filtering, and revised
   the "guaranteed to agree with `lrh request review_response`" claim from
   the prior round: that command uses the narrower `state="unresolved"`
   filter internally, so the two can now legitimately disagree when
   outdated-but-unresolved threads exist — that is `/lrh-confirm-fixes`
   correctly catching something the narrower command misses, not a bug.

No comments were skipped. `rerun_of` left empty: this branch
(`xenotaur/chore/land-confirm-fixes-review-fixes`) is a recovery PR that
cherry-picks commits from the original implementation branch, not a
slug-matched continuation of it, so the standard `rerun_of` search finds no
primary record. The related primary record is
`2026_07_17_18_55_17_WI_SKILLS_LRH_CONFIRM_FIXES` (the `/lrh-implement` run
for `WI-SKILLS-LRH-CONFIRM-FIXES`, whose `pr:` field points to #397 — the
PR this work actually originated in).

**Process note:** the fixes were applied to the tracked files before this
gate was presented (verification required running the corrected command
live against #398 to confirm the documented shape). Flagged transparently
before commit; nothing was pushed until explicit confirmation. This is a
repeat of the same ordering slip already recorded in
`feedback_review_response_edit_after_gate.md` from earlier in this session
— worth a stronger note in that memory, since a single mention did not
prevent recurrence two rounds later.

# Validation

```
scripts/version tools  — lrh 0.2.5.dev83, Ruff 0.15.12, Black 25.11.0 confirmed
scripts/format --check --diff  — skipped: no Python files changed (markdown-only skill edits)
scripts/lint  — skipped: no Python files changed
scripts/test  — skipped: no Python files changed
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — identical
lrh github threads <pr-url> --mode raw --state all  — live-tested against PR #398, output matches corrected documented shape exactly
```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after the
  session ends.
- No unresolved comments remain on PR #398 as of this record.
- Strengthen `feedback_review_response_edit_after_gate.md` with this
  recurrence, or consider whether the review-response protocol itself needs
  a harder checkpoint (not just a documented reminder) to prevent
  editing-before-gate.
