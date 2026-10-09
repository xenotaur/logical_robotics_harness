---
execution_id: 2026_10_09_23_50_27_CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS_REVIEW
prompt_id: PROMPT(AD_HOC:CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS_REVIEW)[2026-10-09T23:45:06+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_09_18_41_59_CONFIRM_FIXES_CI_PREDICATE_EMPTY_CHECKS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/807
commit: 7f3608c8c3b1bd36e2e7ca34ec2b45fee66baf5e
created_at: 2026-10-09T23:50:27+00:00
agent: claude-app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/807
session_transcript: pending
---

# Summary

Review-response round 1 for PR 807, run inline from `/lrh-land` Step 4. Two
review threads were open at HEAD `b1872dc8`. The user confirmed both fixes at
the Step 4 gate.

# Result

- **Copilot (discussion_r4233455263), fixed.** Step 8 in
  `lrh-confirm-fixes/SKILL.md` made its first CI read with a bare
  `gh pr checks`. It used the SHA-aware predicate only once CI was already
  pending, so a stale, all-passing rollup from the previous head could read
  as green. Step 8 now calls
  `check_ci_predicate <pr-url> "$(git rev-parse HEAD)"` and starts the bounded
  poll only on a return of 2. Applied to the src, `.claude`, and `.agents`
  copies. The section is outside the GATE-DEFINITION blocks, and
  `lrh chain-defaults status` still reports `stale: False`.
- **Codex P1 (discussion_r4233457567), fixed.** Regenerated only
  `lrh-confirm-fixes` in the tracked Antigravity target
  (`.gemini/plugins/lrh/skills/`) using
  `lrh skills install --local --target antigravity --force`. The source was a
  scratch copy containing just this skill, so the renderer produced the
  frontmatter. This also brought that copy up to date with src changes it
  had missed: the `lrh vcs merge` one-liner and the "Restricted network
  recovery" section. The `.gemini` copy is now a fourth root in the tests.
- **Tests:** added `ConfirmFixesStep8WiringTest`, which checks that every
  copy's Step 8 calls the predicate and contains no bare
  `gh pr checks <pr-url> --required`.

# Validation

- Ruff 0.15.12, Black 26.3.1, conda env `LrhCiPredicate`.
- `scripts/format --check --diff`: passed.
- `scripts/lint`: passed.
- `scripts/test`: 2156 tests OK.
- `lrh validate`: 0 errors, 0 warnings.
- Predicate and wiring test module: 13/13 OK.

# Follow-up

- Other skills under `.gemini/plugins/lrh/skills/` are still behind src.
  `lrh skills install --local --target antigravity --source current-repo
  --dry-run` lists about 18 with local modifications. Regenerating them is a
  separate task.
