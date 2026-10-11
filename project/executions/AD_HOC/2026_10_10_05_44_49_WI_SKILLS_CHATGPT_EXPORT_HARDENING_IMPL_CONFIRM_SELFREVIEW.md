---
execution_id: 2026_10_10_05_44_49_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_CONFIRM_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_CONFIRM_SELFREVIEW)[2026-10-10T05:44:49+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_10_00_04_59_WI_SKILLS_CHATGPT_EXPORT_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/810
commit:
created_at: 2026-10-10T05:44:49+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/810
session_transcript: pending
---

# Summary

PR-mode `/lrh-self-review` for PR #810, run at HEAD `9eadcc51` (the
`_CONFIRM` commit). It is the `/lrh-confirm-fixes` Step 8 **substitute review
signal**:
- No automatic reviewer responded to the commits after the first round
  (`dc38cdde` onward).
- No hosted review bot was retriggered.

A cold `general-purpose` subagent did the review.

# Result

Verdict: **safe to merge as-is**, no P1/P2. The reviewer independently
confirmed several things:
- The fixes are correct. It probed HEAD against `d29e9639`, which it
  extracted with `git archive`.
- The canonical export is 20/5, and the 3 sectioned skills are right.
- All 20 bundles are byte-identical to `d29e9639`'s.
- The spec citation is accurate.
- 160 targeted tests pass, and lint/format are clean.
- A clean `git merge-tree` against origin/main, 66 commits ahead.
- All 5 threads are genuinely addressed.

P3 findings:

1. The PR body still describes the removed CommonMark fence scanning, and
   so does the primary record's Result.
2. The WI's Required Change 4 still says "immediately after the frontmatter";
   the code follows implementer note 4 (after the opening H1).
3. Behavior change from `dc38cdde`: a manual-only skill with a malformed or
   unparseable `agents/openai.yaml` now fails validation (and, all-or-nothing,
   the whole export) instead of being skipped. This is intended fail-safe but
   undocumented.
4. A blank (null) `policy:` in `agents/openai.yaml` still reads as "no
   policy". It is the same class as the WI's null markers, but outside the
   WI's literal scope.
5. Placement edge cases that affect no canonical skill:
   - a body opening with an HTML comment or a setext title gets the section
     above it;
   - a body with its own `## When to use` heading gets two.

The invoking session re-verified the top findings directly:
- #1: `gh pr view --json body` still contains "Placement is CommonMark-aware:
  it ignores fenced code".
- #3: a probe skill with `disable-model-invocation: true` and an unparseable
  `openai.yaml` now fails with "invalid Codex metadata".

Disposition, under the P3 policy agreed at the `/lrh-execute` chain gate (one
verified fix round, then a cold delta review of that fix, then the rest are
deferred):
- **Fix round:** #1 (PR body edit) and #3 (reference-doc note), via
  review-response round 2.
- **Deferred:**
  - #2 is recorded at closeout, when the WI is resolved.
  - #4 is a follow-up outside the WI's scope.
  - #5 affects no canonical skill.

No finding was routed to `/lrh-confirm-fixes` Step 3 as a thread; these are
non-thread findings.

# Validation

CI at `9eadcc51`: 5/5 success, read via the bounded `check_ci_predicate`
poll, which exited green.
