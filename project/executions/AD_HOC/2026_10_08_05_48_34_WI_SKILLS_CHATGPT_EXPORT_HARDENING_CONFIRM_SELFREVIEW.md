---
execution_id: 2026_10_08_05_48_34_WI_SKILLS_CHATGPT_EXPORT_HARDENING_CONFIRM_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_CONFIRM_SELFREVIEW)[2026-10-08T05:48:34+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_06_03_50_00_WI_SKILLS_CHATGPT_EXPORT_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/775
commit: b559d3622b34f54dc35083babe1d8365fe68f763
created_at: 2026-10-08T05:48:34+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/775
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Round-2 PR-mode substitute review for PR #775: a targeted cold-context review
of commit `3513c569195caf99008fc07929ea52c12ba47c62` (the review-response
round-2 design fix), at HEAD `464d12fc6af35e004aff8fad0c7cadabf5a44b78`,
the SHA the merge was locked to. No hosted review bot was retriggered.
Landed in the closeout commit so the merge lock stayed on the reviewed head.

# Result

Verdict: safe to merge as a planning change, no P1/P2. The reviewer
confirmed:

- the three over-limit skills and their lengths (on stripped values; raw
  values are 2 higher);
- that no skill sits near the 1024 boundary;
- the 20-exported / 5-skipped baseline, from a real export;
- that the fold-or-section design is consistent across all WI sections;
- that it is implementable against the current exporter;
- that `lrh validate` and readiness pass.

P3 spec-clarity findings, **deferred** under the agreed P3 policy (the one
fix round was already used). They are recorded here and in the closeout note
for the implementer:

1. Strip trailing newlines from `description` and `when_to_use` (both `>`
   folded scalars) before joining and measuring.
2. Specify what a blank or non-string `when_to_use` does (fail, drop with a
   notice, or ignore); a naive fold would raise `TypeError` on `None`.
3. Name the existing text that pins the old behavior:
   - `tests/skills_exporter_test.py:135-166` (expects `when_to_use` to be
     stripped);
   - `docs/reference/cli/skills.md:141-143`;
   - `docs/how-to/use-lrh-with-agent-assistants.md:182` ("Skill
     instructions are exported unchanged");
   - the `ChatGPTSkillRenderer` docstring and the `exporter.py:32-34`
     comment.
4. Place the generated `## When to use` section after the skill's first H1,
   not above it. All three section-path skills start with `# <name> Skill`.

# Validation

CI on `464d12fc`: 5/5 success. Reviewer-run `lrh validate` 0 errors;
readiness prompt-ready.
