---
execution_id: 2026_10_10_05_37_09_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_REVIEW)[2026-10-10T00:14:45+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_00_04_59_WI_SKILLS_CHATGPT_EXPORT_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/810
commit: 4e97f0e57215d41b12c5ae8427d9007b67adc4d5
created_at: 2026-10-10T05:37:09+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/810
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

Review-response round 1 for PR #810, run inline from `/lrh-land` Step 4. It
covered the 5 comments on reviewed commit `d29e9639`: 4 from Copilot and 1
from Codex. The human confirmed the triage plan at the Step 4 gate
("Proceed").

# Result

Fixed in `dc38cdde`:

1. **Copilot: manual-only marker bypass.** A valid
   `disable-model-invocation: true` returned before `agents/openai.yaml` was
   parsed, so a blank or non-boolean `policy.allow_implicit_invocation`
   escaped validation.
   - Fix: `_is_manual_only` now validates both markers (in
     `_claude_manual_only` and `_codex_manual_only`) before combining them.
   - Verified: the default selection now fails such a skill, and an
     explicit `--skill` selection fails it too.
   - Test: `test_valid_claude_marker_does_not_hide_bad_codex_policy`.
2. **Copilot: a backtick info string containing a backtick is not a fence**,
   and **Codex (P2): an H1-like line inside an HTML block or comment captures
   the section.** Both reproduced. They were fixed together by simplification
   instead of extending a partial CommonMark scanner.
   - The section now follows the H1 title only when that title is the body's
     first non-blank line. Otherwise it goes at the top of the body.
   - Fence scanning is removed.
   - Every canonical skill opens with its H1, so implementer note 4 still
     holds, and all 20 canonical bundles are byte-identical to before.
   - The reference doc and docstring are updated.
   - Tests: `test_section_goes_to_top_when_body_does_not_open_with_h1` and
     `test_section_placement_follows_opening_title`.
3. **Copilot: CRLF body with multi-line guidance kept embedded `\n`.**
   - Fix: the guidance's line breaks are converted to the body's newline.
   - Test: `test_section_matches_crlf_body_line_endings`.

Skipped:

4. **Copilot: missing primary execution record.** This is not present on the
   current branch. The primary record
   `2026_10_10_00_04_59_WI_SKILLS_CHATGPT_EXPORT_HARDENING` was added in
   `e8779a5b`, after the reviewed commit `d29e9639`.

Publication: pushed directly to
`xenotaur/feat/wi-skills-chatgpt-export-hardening-impl`.

# Validation

- `scripts/version tools`: ruff 0.15.12, black 26.3.1 (LRH conda env).
- `scripts/format --check --diff`: clean.
- `scripts/lint`: exit 0.
- `scripts/test`: 2187 tests, OK.
- `lrh validate`: 0 errors.
- Canonical `lrh skills export --target chatgpt --source current-repo`: 20
  exported, 5 manual-only skipped. Every bundled `SKILL.md` is byte-identical
  to the pre-review export.

# Follow-up

- Run confirm-fixes (`/lrh-land` Step 5) against the new HEAD.
