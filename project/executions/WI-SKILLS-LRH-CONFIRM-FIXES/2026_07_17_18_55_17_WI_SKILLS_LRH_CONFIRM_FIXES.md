---
execution_id: 2026_07_17_18_55_17_WI_SKILLS_LRH_CONFIRM_FIXES
prompt_id: PROMPT(WI-SKILLS-LRH-CONFIRM-FIXES:WI_SKILLS_LRH_CONFIRM_FIXES)[2026-07-17T17:46:02-04:00]
work_item: WI-SKILLS-LRH-CONFIRM-FIXES
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/397
commit: d6f3b9468772b3a6e61ec6acea20a14358f83e8d
created_at: 2026-07-17T18:55:17-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-LRH-CONFIRM-FIXES.md
session_transcript: claude-app:49a80683-68ef-40ff-a81c-28253a11ca8e
---

# Summary

Implement `/lrh-confirm-fixes`, a pre-merge verification and thread-resolution
skill, per `WI-SKILLS-LRH-CONFIRM-FIXES` and `PROP-LRH-CONFIRM-FIXES`.

# Result

Created `src/lrh/skills/lrh-confirm-fixes/SKILL.md` (8-step flow: detect PR →
gather state → fresh-eyes verification → confirm gate → execute resolutions →
compute thread-resolution verdict → record + validate → readiness report) and
`references/confirm-fixes-workflow.md` (verification taxonomy, `gh api
graphql` primitives, CI check mechanism with post-push re-verification,
`_CONFIRM` execution-record convention, idempotency edge cases). Mirrored
byte-for-byte to `.claude/skills/lrh-confirm-fixes/`.

Added the `/lrh-confirm-fixes` entry to `CLAUDE.md`'s `## Skills` index.

Wired the handoff into `/lrh-review-response` (both `SKILL.md` and
`references/review-response-workflow.md`, both `src/` and `.claude/` trees):
the `rerun_of` exclusion glob now also excludes `_CONFIRM.md` (a confirm-fixes
side record can no longer be mismatched as a primary execution record), the
lifecycle diagram gained a `/lrh-confirm-fixes` node between "repeat review
rounds" and "Merge + closeout", and Step 7's report now suggests running
`/lrh-confirm-fixes` before merge.

`WI-SKILLS-LRH-CONFIRM-FIXES` was already listed in
`WS-SKILLS-CONFIRM-FIXES.md`'s `work_items:` — no change needed there.

No `--subagent`/`--surface-human` CLI-flag parsing infrastructure exists
outside this skill's own documentation of how to interpret trailing
arguments; the flags are handled the same way `/lrh-review-response`
interprets its `[pr-url]` argument-hint — by the model reading the invocation
text, not a dedicated arg-parser. This matches the project's existing
slash-command convention (no skill in this repo parses flags programmatically).

# Validation

```
scripts/version tools  — lrh 0.2.5.dev83, Ruff 0.15.12, Black 25.11.0 confirmed
scripts/format --check --diff  — pre-existing environment mismatch (Black 26.3.1 required, 25.11.0 installed); unrelated to this PR, 0 Python files touched
scripts/lint  — Ruff: all checks passed; Black check fails for the same pre-existing environment reason
scripts/test  — 785 tests, OK
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — identical
diff -r src/lrh/skills/lrh-review-response/ .claude/skills/lrh-review-response/  — identical
```

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after the
  session ends.
- `/lrh-confirm-fixes` has not yet been exercised against a real PR with open
  review threads — the first live run (e.g. against this PR's own eventual
  review comments, or the next `/lrh-review-response`-touched PR) is the
  practical validation of the `gh api graphql` primitives beyond design-time
  review.
- Once this PR merges: run `/lrh-closeout` to resolve
  `WI-SKILLS-LRH-CONFIRM-FIXES`, close `WS-SKILLS-CONFIRM-FIXES` (its only
  work item), and adopt `PROP-LRH-CONFIRM-FIXES`.
