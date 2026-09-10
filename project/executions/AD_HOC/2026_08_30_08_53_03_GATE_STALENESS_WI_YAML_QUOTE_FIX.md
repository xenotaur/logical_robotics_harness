---
execution_id: 2026_08_30_08_53_03_GATE_STALENESS_WI_YAML_QUOTE_FIX
prompt_id: PROMPT(AD_HOC:GATE_STALENESS_WI_YAML_QUOTE_FIX)[2026-08-29T17:06:32+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
agent: claude_app
instruction_source: ad_hoc conversation — fix FRONTMATTER_LINT_UNSAFE_SCALAR on WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md's acceptance field
session_transcript: claude-app:4ba135af-db45-4065-aa9c-a4ec9ad99ffa
pr: https://github.com/xenotaur/logical_robotics_harness/pull/655
commit: 1079313ab386ff0f01bdb2bf6fe88741d4cd2d1e
created_at: 2026-08-30T08:53:03+00:00
---

# Summary

Ad-hoc fix for `lrh validate`'s `[FRONTMATTER_LINT_UNSAFE_SCALAR]` warning
on `project/work_items/resolved/WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`
(reported at the user's request, discovered independently of any active
work item). The `acceptance:` list item at frontmatter line 37 contained an
unquoted `' #648'` inside a plain YAML scalar, which real YAML parsers read
as a comment start, silently truncating the string. Same bug class fixed
in PR #645 and PR #651 (`WI-EXECUTE-EARLY-CREATION-PR-CHECK`,
`WI-PROJECT-SLUG-SYMLINK-RESOLUTION`), both originally flagged by Copilot.

# Result

Wrapped the offending list item's string value in double quotes (no
internal `"` characters, so no escaping was needed). Verified the full
string — including the `#648` text — now round-trips through
`yaml.safe_load` without truncation, and that `lrh validate` no longer
reports `FRONTMATTER_LINT_UNSAFE_SCALAR` for this file's `acceptance`
field. A separate, pre-existing warning on the same file's `resolution:`
field (unquoted `': '`, a different unsafe-scalar sub-case) remains —
explicitly out of scope for this fix per the task framing, and reported to
the user as a follow-up candidate.

`/lrh-self-review` diff-mode ran before the first push (see
`2026_08_30_08_52_09_GATE_STALENESS_WI_YAML_QUOTE_FIX_SELFREVIEW.md`):
clean pass, independently re-verified by both the dispatched subagent and
this session.

# Validation

- `python3 -c "import yaml; ..."` — full acceptance-field string parses
  without truncation.
- `lrh validate` — 0 errors, 1 warning (the separate out-of-scope
  `resolution:` field warning only).
- `scripts/format --check --diff` — clean, 247 files unchanged.
- `scripts/lint` — ruff and black both pass.
- `scripts/test` — 1529 tests, all pass (an initial run showed 1 import
  error unrelated to this change — a stale editable `lrh` install pointing
  at a different worktree's `src/`; reinstalled with `pip install -e .
  --no-deps` for this worktree, then the full suite passed clean).

# Follow-up

- The same file's `resolution:` frontmatter field has its own,
  pre-existing `FRONTMATTER_LINT_UNSAFE_SCALAR` warning (unquoted `': '`)
  — out of scope for this fix, flagged to the user, not otherwise tracked.
