---
execution_id: 2026_09_26_01_04_09_WI_SKILLS_CHATGPT_EXPORT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_REVIEW)[2026-09-26T00:40:41+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_09_25_19_26_00_WI_SKILLS_CHATGPT_EXPORT_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/720
commit: 06f9f1d2eb1901c5f1e4a133839444fa25dc9704
created_at: 2026-09-26T01:04:09+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/720
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Second review-response round for PR #720, addressing the non-thread findings
surfaced by the substitute PR-mode self-review
(`2026_09_25_21_57_31_WI_SKILLS_CHATGPT_EXPORT_SELFREVIEW`) on the `_CONFIRM`
HEAD `15acec2c`. `lrh request review_response` reported `Nothing to resolve:`
because the findings have no review thread; they were carried into this
protocol by hand. The prior `_REVIEW` record (authored by an earlier ChatGPT
session) matched the slug idempotence check; the user explicitly authorized
this rerun at the confirm gate.

# Result

Fix commit: `59ac546e8234b1d49fbcb9df4b19572b62bd8f6c`.

- **P2 manual-only invocation policy (fixed).** `WI-SKILLS-CHATGPT-EXPORT`
  now requires: the default all-skills export excludes manual-only skills,
  which are exported only via explicit `--skill`; manual-only status is
  detected from either canonical marker (Claude `disable-model-invocation:
  true` or Codex `policy.allow_implicit_invocation: false`); an equivalent
  ChatGPT explicit-only control is emitted if documented, otherwise a
  non-blocking manual-only compatibility notice; tests cover the
  default-exclusion and explicit-export paths. Added matching frontmatter
  acceptance, body acceptance criterion, Required Changes 1/3/7/8 edits, and
  a Risk Note citing `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL` Decision 2.
- **P3 proposal frontmatter (partially fixed).** Bumped `updated_on` to
  2026-09-24. `implementation_status: implemented` deliberately left
  unchanged — the proposal's scoped first-slice stages are implemented; the
  ChatGPT stage is tracked by the new WI.
- **P3 Stage 7 cross-reference (fixed).** Now points to Decision 8 rather
  than "Decision 8's follow-up".
- **P3 inferred bundle format (fixed).** Added a WI Risk Note that the
  ChatGPT-app format is partly inferred from the API Skills guide and must be
  confirmed by the dogfood run.
- **P3 `agent: chatgpt` table value (skipped — validity/scope).**
  Informational; other off-table values already exist; out of scope for a
  planning PR.

# Validation

- `scripts/version tools`: local black 25.11.0 vs. pinned 26.3.1, so
  `scripts/format --check --diff` and `scripts/lint` could not run locally.
  The diff touches only two Markdown planning files (no Python), so neither
  tool's scope is affected; CI's pinned "Lint and formatting checks" job is
  the evidence for the pushed HEAD. No `--isolated`/config bypass was used.
- `scripts/test` with `PYTHONPATH=<checkout>/src`: 1718 tests, OK. (Without
  it, the editable `lrh` install resolves to a different checkout and 2
  unrelated `claude_export_test` cases fail; both pass against this
  checkout's source.)
- `lrh validate` (this checkout's source): 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-CHATGPT-EXPORT`: ready.

# Follow-up

Reply on the PR citing the fix commit (non-thread finding: no
`resolveReviewThread`), then re-run `/lrh-confirm-fixes`, which needs a fresh
review signal on the new HEAD.
