---
execution_id: 2026_10_10_05_48_47_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_REVIEW)[2026-10-10T05:45:10+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_05_37_09_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/810
commit: 4e97f0e57215d41b12c5ae8427d9007b67adc4d5
created_at: 2026-10-10T05:48:47+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/810
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Review-response round 2 for PR #810. This is the single verified P3 fix
round allowed by the P3 policy agreed at the `/lrh-execute` chain gate. It
addresses the non-thread findings from the PR-mode substitute self-review
`2026_10_10_05_44_49_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_CONFIRM_SELFREVIEW`
(safe to merge, P3 only).

The slug check matched round 1's `in_progress` record. That record was
authored earlier in this same land run, so the same-land-run carve-out
applied and `rerun_of` links to it.

# Result

Fixed:

- **P3 #1, stale PR body.** The PR description was edited (`gh pr edit`) to
  describe the first-line-H1 placement rule and the CRLF handling of
  multi-line guidance, replacing the removed "CommonMark-aware, ignores
  fenced code" text. It also notes that both manual-only markers are always
  validated. The primary execution record's Result still mentions fences;
  its body is left unchanged as the primary record, and round 1's `_REVIEW`
  record documents the change.
- **P3 #3, undocumented fail-safe.** In `9628ee5c`,
  `docs/reference/cli/skills.md` now states that both markers are checked even
  when one already marks the skill manual-only. A malformed or unreadable
  `agents/openai.yaml` therefore fails validation and stops the export.

Deferred under the P3 policy:

- **#2, WI wording.** Required Change 4 says "immediately after the
  frontmatter", while implementer note 4 places the section after the
  opening H1. This is recorded at closeout when the WI is resolved.
- **#4, blank `policy:`.** A blank `policy:` in `agents/openai.yaml` still
  reads as "no policy". This is a follow-up outside the WI's literal scope.
- **#5, placement edge cases.** An HTML comment or setext title before the
  H1, or a body that already has its own `## When to use`, is affected. No
  canonical skill is.

Publication: pushed directly.

# Validation

- `scripts/version tools`: ruff 0.15.12, black 26.3.1.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: exit 0.
- `scripts/test`: 2187 tests, OK.
- `lrh validate`: 0 errors.

# Follow-up

- Confirm-fixes round 2, then a cold delta review of `9628ee5c` and the PR
  body edit.
