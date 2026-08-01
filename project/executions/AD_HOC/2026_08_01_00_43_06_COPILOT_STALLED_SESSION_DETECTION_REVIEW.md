---
execution_id: 2026_08_01_00_43_06_COPILOT_STALLED_SESSION_DETECTION_REVIEW
prompt_id: PROMPT(AD_HOC:COPILOT_STALLED_SESSION_DETECTION_REVIEW)[2026-08-01T00:35:18+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_01_00_13_37_COPILOT_STALLED_SESSION_DETECTION
pr: https://github.com/xenotaur/logical_robotics_harness/pull/452
commit: 
created_at: 2026-08-01T00:43:06+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/452
session_transcript: claude-app:local_23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Address the first round of automated review on PR #452 (Codex +
`copilot-pull-request-reviewer`), via `/lrh-land`'s inlined
review-response step.

# Result

Four distinct findings (some duplicated across multiple Copilot comment
instances), all fixed:

1. **Codex, P2 (real, valid):** the "Issue timeline, for corroboration"
   check in `round-cap-gate.md` used any `copilot_work_started` event on
   the PR to corroborate the check-run signal, but `copilot_work_*`
   events are emitted by **both** Copilot products — the code-review bot
   this step retriggers, and the separate coding agent invoked by a bare
   `@copilot` comment mention elsewhere on the same PR. Matching event
   *type* alone could false-corroborate an unrelated coding-agent
   invocation, or miss a genuinely stalled code-review request with no
   coding-agent event at all. Fixed: only trust the `copilot_work_started`
   event that is the nearest one **after** this step's own
   `gh pr edit --add-reviewer @copilot` call by timestamp, not any such
   event found anywhere in the timeline.
2. **Copilot (real, valid):** the "Stall detected" question text in
   `SKILL.md` Step 8.3 said "not simple lag," which reads as a diagnosis
   rather than a heuristic, inconsistent with `round-cap-gate.md`'s own
   hedging that the API can't confirm cause. Softened the wording and
   named the specific `copilot_work_finished`/`copilot_work_finished_failure`
   events for consistency with `round-cap-gate.md`'s phrasing.
3. **Copilot (real, valid, x3 duplicate comments):** "Both signals
   together ... is stalled" had a subject-verb agreement error and
   asserted a definitive state rather than describing a heuristic signal.
   Fixed to "indicate a **stalled** session."
4. **Copilot (not literally present as described):** claimed the timeline
   event list "uses a shorthand '`_finished_failure`'" — no such literal
   string exists anywhere in the diff (verified by grep before touching
   any file). The closest legitimate concern — `SKILL.md`'s Step 8.3
   summary described "a terminal event" generically without naming the
   specific `copilot_work_finished`/`copilot_work_finished_failure` events
   `round-cap-gate.md` uses — is addressed by fix 2 above (which names
   both events explicitly), replied to the thread noting the literal quote
   didn't match but the underlying consistency point was taken.

Both `.claude/skills/lrh-confirm-fixes/` and `src/lrh/skills/lrh-confirm-fixes/`
mirrors updated identically.

# Validation

```
scripts/version tools          — Black, Ruff versions confirmed
scripts/format --check --diff  — 179 files unchanged
scripts/lint                   — all checks passed
scripts/test                   — Ran 808 tests, OK
lrh validate                   — 0 errors, 1 pre-existing unrelated warning
                                  (PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF
                                  on WS-LRH-ASSISTANTS, unrelated to this change)
diff .claude/skills/lrh-confirm-fixes/{SKILL.md,references/round-cap-gate.md} src/lrh/skills/lrh-confirm-fixes/{SKILL.md,references/round-cap-gate.md} — identical
```

# Follow-up

- Continue `/lrh-land`'s chain: re-check REVIEW-LANDED on the new HEAD,
  run confirm-fixes, then the merge gate and closeout.
