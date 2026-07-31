---
execution_id: 2026_07_31_08_45_58_COPILOT_RETRIGGER_REVIEW_NOT_AGENT
prompt_id: PROMPT(AD_HOC:COPILOT_RETRIGGER_REVIEW_NOT_AGENT)[2026-07-31T08:41:39+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/446
commit: d0378e7d4070367c81b5784572ab2eaeab0cbf2d
created_at: 2026-07-31T08:45:58+00:00
agent: claude_app
instruction_source: ad_hoc conversation — user reported Copilot pushing unwanted commits to PRs and asked why, how to debug it, and how to fix it
session_transcript: claude-app:9e68ac13-8d87-42d3-bbd2-3997bd762717
---

# Summary

Debug and fix the root cause of `copilot-swe-agent[bot]` pushing unprompted
commits to PR branches (first observed on PR #444, commit `ba65489`,
recorded in [[feedback_copilot_swe_agent_autonomous_push]]). At the time
that memory was written the cause was assumed unknown/anomalous.

# Result

Root-caused via GitHub's own documentation and changelog (grounded, not
inferred):

- GitHub Copilot has two separate bot products sharing the "copilot" name:
  **Copilot code review** (`copilot-pull-request-reviewer[bot]`), invoked
  only by *requesting Copilot as a reviewer*, which "always leaves a
  'Comment' review" and never commits (GitHub Docs, "Using GitHub Copilot
  code review"); and **Copilot coding agent** (`copilot-swe-agent[bot]`),
  invoked by **@-mentioning `@copilot` in any comment body** (GitHub Docs,
  "Asking GitHub Copilot to make changes to an existing pull request").
  "Review" is not a reserved read-only keyword to the coding agent — it is
  free text the agent interprets as a task.
- Per the GitHub Changelog (2026-03-24, "Ask @copilot to make changes to
  any pull request"), the coding agent's default changed: it now pushes
  commits directly onto the existing PR's branch, replacing the prior
  behavior of opening a separate follow-up PR and leaving the original
  untouched.
- Found the exact trigger live in this repo: `lrh-confirm-fixes/SKILL.md`'s
  retrigger step used `gh pr comment <pr-url> --body "@copilot review"` —
  a plain comment, which always lands on the coding-agent trigger surface
  regardless of wording. Fixed by replacing it with
  `gh pr edit <pr-url> --add-reviewer @copilot` (the documented,
  non-commit-capable review-request path), in both
  `.claude/skills/lrh-confirm-fixes/SKILL.md` and
  `src/lrh/skills/lrh-confirm-fixes/SKILL.md`, with an inline warning and
  citations against regressing to a plain `@copilot` comment.
- `@codex review` (same retrigger step) is unaffected — Codex does not
  have this dual-surface ambiguity.
- Updated [[feedback_copilot_swe_agent_autonomous_push]] with the
  confirmed root cause, correcting its prior "may mean this" hedge and
  its incorrect assumption that `@copilot review` "normally just produces
  a review comment."

**Prior-art check:** no duplication (only the file just fixed used the
correct pattern, and only after this session's edit); one tangential
demand-adjacent hit — `WI-REVIEW-ROUND-ESCALATION-GATE.md` references
`@copilot review` in passing when defining "round" semantics for a
retrigger-escalation gate, but that WI addresses round-counting, not the
trigger-mechanism bug, so no action taken against it beyond noting its
example command text will read as slightly dated once this PR lands.

# Validation

```
scripts/version tools          — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff  — 179 files unchanged
scripts/lint                   — all checks passed
scripts/test                   — Ran 808 tests, OK
lrh validate                   — 0 errors, 1 pre-existing unrelated warning
                                  (PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF
                                  on WS-LRH-ASSISTANTS, unrelated to this change)
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/ — identical
```

# Follow-up

- Land via `/lrh-land https://github.com/xenotaur/logical_robotics_harness/pull/446`.
- Optional, not actioned here: refresh `WI-REVIEW-ROUND-ESCALATION-GATE.md`'s
  `@copilot review` example text to match the new `gh pr edit --add-reviewer`
  command once that WI is next touched.
