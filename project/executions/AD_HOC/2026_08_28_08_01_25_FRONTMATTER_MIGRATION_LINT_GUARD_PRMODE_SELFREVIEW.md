---
execution_id: 2026_08_28_08_01_25_FRONTMATTER_MIGRATION_LINT_GUARD_PRMODE_SELFREVIEW
prompt_id: PROMPT(AD_HOC:FRONTMATTER_MIGRATION_LINT_GUARD_PRMODE_SELFREVIEW)[2026-08-28T08:01:19+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/642
commit: 4088ca025362737d1e61c0d8d86cef4bf572b766
created_at: 2026-08-28T08:01:25+00:00
agent: claude_app
instruction_source: 'command lrh-self-review --pr 642, run after the automatic bot-review round''s findings were fixed, before asking for merge authorization -- proactive follow-up given the P1 finding involved destructive rewrites'
session_transcript: claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8
---

# Summary

PR-mode substitute self-review of PR #642 (`WI-FRONTMATTER-MIGRATION-LINT-GUARD`)
after the automatic bot review's 4 findings had already been fixed and
threads resolved, run proactively before asking for merge authorization
given the prior P1 finding involved destructive content rewrites.
Dispatched a cold `general-purpose` subagent with the PR URL, HEAD SHA,
and full round-1/round-2 context; the invoking session independently
re-verified the top finding by direct reproduction.

# Result

The subagent confirmed all four round-2 fixes genuinely hold (verified
directly against current code, not just the PR's own reply comments), and
independently ran the full test suite and `lrh validate` itself. It found
one new, real, moderate-severity issue, independently re-verified by the
invoking session via direct reproduction (not merely accepted): a
`- key: value` list item under a `KNOWN_STRING_FIELDS` member (e.g.
`acceptance`) that is actually a multi-key YAML mapping entry (a
continuation line indented to align with the first key, e.g. a second
`detail:` key) would still be wrongly treated as a flat scalar by the P1
fix, which only exempted *unrecognized* fields, not known ones with real
nested structure. Reproduced directly: `fix_file` raised an uncaught
`yaml.ParserError` on such input, and `fix_project` has no per-file
try/except, so a real `--apply` run would abort mid-batch (files already
written keep their changes; the crashing file and everything after it in
iteration order never get processed).

Fixed by detecting nested continuation structurally
(`_has_nested_continuation` in `frontmatter_lint.py`): any list item
followed by a line indented deeper than the item's own dash, that isn't
itself a new list item, is left alone entirely -- regardless of the
owning field -- since rewriting only the first line would always orphan
the continuation. Verified the fix doesn't regress the two prior colon-
collapse detection cases (a genuine single-line colon-collapse under a
known field, and the P1 fix's unrecognized-field exemption).

A second, lower-severity finding (a literal `null` in `display_name`,
which is required for contributor records but not in
`STRICT_NON_NULL_STRING_FIELDS`, slips past the lint silently) was left
undocumented as a known limitation rather than expanding the allow-list
further without a full schema audit -- consistent with the module's own
"not a closed enumeration" framing and this session's established
practice of deferring narrow edge cases.

# Validation

- `lrh validate`: 0 errors, 0 warnings (re-run after the fix).
- Full `pytest`: 1471 tests, all pass (up from 1469 before this fix's two
  new regression tests).
- `scripts/format --check --diff`, `scripts/lint`: clean.
- Independently reproduced the crash directly (`fix_file` on a scratch
  fixture) both before and after the fix, confirming the fix actually
  eliminates it rather than just suppressing a symptom.

# Follow-up

- The `display_name: null` silent-miss gap (see Result) is not tracked as
  its own work item; if it ever needs fixing, the same
  `STRICT_NON_NULL_STRING_FIELDS` opt-in mechanism this fix already
  established would apply directly -- add `display_name` to that set
  after confirming it's genuinely never legitimately null across the
  contributor schema.
