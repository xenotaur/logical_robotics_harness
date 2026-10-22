---
execution_id: 2026_10_10_00_03_47_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_SELFREVIEW)[2026-10-10T00:03:46+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_10_00_04_59_WI_SKILLS_CHATGPT_EXPORT_HARDENING
pr: https://github.com/xenotaur/logical_robotics_harness/pull/810
commit: 4e97f0e57215d41b12c5ae8427d9007b67adc4d5
created_at: 2026-10-10T00:03:47+00:00
agent: claude_app
instruction_source: .claude/skills/lrh-self-review/SKILL.md
session_transcript: claude-app:9a96d262-76e5-4e8e-92e0-0e30d7776fbf
---

# Summary

`/lrh-implement` Step 7.5 diff-mode `/lrh-self-review` for the
`WI-SKILLS-CHATGPT-EXPORT-HARDENING` implementation, run before the first push.
A cold-context `general-purpose` subagent reviewed the uncommitted diff against
the fork point `0a6e8454` (the local `main` ref was stale, so `git diff main`
would have included unrelated commits). Orientation was the WI plus the four
implementer notes in
`2026_10_08_05_48_36_WI_SKILLS_CHATGPT_EXPORT_HARDENING_CLOSEOUT_NOTE`.
`rerun_of` is empty by construction: diff-mode runs before Step 9 creates the
primary record.

# Result

Verdict: the diff plausibly satisfies every Required Change, Acceptance
Criterion, and implementer note; no P1/P2. The reviewer mutation-tested the new
tests (removing the `.` filter, reordering it ahead of the symlink check,
reverting the null-marker check, forcing the section to the top, re-reporting
`when_to_use` as stripped) and each mutation was caught, so none is vacuous.

Six P3 findings:

1. Fence tracking in `_insert_when_to_use_section` toggled on any ```` ``` ````
   or `~~~` line, so a tilde line inside a backtick fence, or a shorter fence
   inside a longer one, misplaced the section.
2. `str.splitlines` split on non-Markdown line breaks, a CRLF body got an
   LF-only section, and an indented ATX H1 (1-3 spaces) was not recognized.
3. The grouped capability notice still said "instructions are exported
   unchanged", now inaccurate for sectioned skills.
4. The new Notices line in `docs/reference/cli/skills.md` was not wrapped.
5. The reference doc attributed the non-blank `compatibility` rule to the
   Agent Skills spec, which only says 1-500 characters.
6. Test gaps: no limit+1 boundary test; the canonical test pins only one
   sectioned skill (left as is to avoid churn when canonical text changes).

Top finding (1) was independently re-verified by the invoking session: both
probe bodies put the section inside the code block after `# inside`, and the
CRLF probe produced mixed line endings.

Mode was report-only (no `--apply`). The implementing session then fixed
findings 1-5 and the limit+1 gap from 6 in the working tree, since all were
verified and in scope: CommonMark-style fence matching (same character, at
least as long, nothing after), lines split on `\n` only with the section using
the heading's line ending, 0-3 spaces of H1 indent, reworded notice and docs,
plus `test_fold_one_over_limit_becomes_section` and
`test_section_placement_follows_markdown_structure`. No PR-mode routing
applies.

# Validation

After the fixes (Step 7 re-run): `scripts/format --check --diff` clean,
`scripts/lint` exit 0, `scripts/test` 2185 tests OK, `lrh validate` 0 errors.
A canonical ChatGPT export still writes 20 bundles and skips the same 5
manual-only skills, and every bundled `SKILL.md` is byte-identical to the
export taken before the fixes.

# Follow-up

- None beyond the deliberately unpinned sectioned-skill set (finding 6).
