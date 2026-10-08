---
execution_id: 2026_10_07_23_04_01_WI_SKILLS_CHATGPT_EXPORT_HARDENING_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_REVIEW)[2026-10-06T06:14:21+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_06_05_24_00_WI_SKILLS_CHATGPT_EXPORT_HARDENING_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/775
commit:
created_at: 2026-10-07T23:04:01+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/775
session_transcript: pending
---

# Summary

Review-response round 2 for PR #775, run inline from `/lrh-land` after
substitute self-review round 1
(`2026_10_06_05_29_22_WI_SKILLS_CHATGPT_EXPORT_HARDENING_SELFREVIEW`)
surfaced a P2 that fired the run's stop-work condition. The user chose
"option A, fix it now" and confirmed the edit plan at the review-response
gate. This is a same-land-run continuation of the round-1 `_REVIEW` record.

# Result

Fix commit: `3513c569195caf99008fc07929ea52c12ba47c62`.

- **P2, the `when_to_use` fold could not carry over-limit skills (fixed by
  redesign).**
  - Required Change 4 now folds `when_to_use` into `description` with a
    single-space separator when the combined text is at most 1024
    characters.
  - Otherwise it keeps `description` unchanged and adds a generated
    `## When to use` section at the top of the bundled `SKILL.md` body, with
    a notice. `when_to_use` is never silently lost.
  - The three section-path skills are named, with re-verified lengths:
    `lrh-export-claude` 1480, `lrh-work-remains` 1155, `lrh-config-gates`
    1143.
  - Problem 4, the Non-Goals (narrowed to allow only the generated section),
    tests, docs, acceptance criteria, and Risk Notes were updated to match.
- **P3, the frontmatter acceptance list did not mirror the body (fixed):**
  added the 20-exported / 5-skipped baseline and the "absent key does not
  fail" clause.
- **P3, separator and `stripped_metadata` notice unspecified (fixed):**
  single space; a folded or sectioned `when_to_use` is not reported as
  stripped.
- **P3, stale PR body (fixed):** the description was refreshed with
  `gh pr edit`.
- **Optional `gate_staleness.py` comment note:** left for implementation
  time.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-CHATGPT-EXPORT-HARDENING`:
  prompt-ready.

# Follow-up

Confirm-fixes, then a cold delta review of `3513c569` under the agreed P3
policy.
