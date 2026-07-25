---
execution_id: 2026_07_25_04_12_46_WI_EXEC_SESSIONS_SCHEMA_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EXEC_SESSIONS_SCHEMA_REVIEW)[2026-07-25T04:12:20-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_25_04_01_32_WI_EXEC_SESSIONS_SCHEMA
pr: https://github.com/xenotaur/logical_robotics_harness/pull/421
commit: e7d7a0eb1a74ab21e0245f58798e8afbe54b2424
created_at: 2026-07-25T04:12:46-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/421
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---

# Summary

Address 4 review comments on PR #421 (execution-session schema validator).
All four exposed real gaps in the colon-based scheme check; all fixed.

# Result

Added `_is_scheme_prefixed()` and rewrote the `session_transcript` element
loop in `src/lrh/control/validator.py`:

- **Loose colon check (Copilot r3649855057, codex r3649857877):** the old
  `":" not in element` accepted near-misses like `:id`, `backend:`,
  `some/path:foo`, and `not a scheme: text`. Now requires a genuine
  `<scheme>:<id>` — non-empty scheme with no path separators/whitespace, a
  colon, and a non-empty id — else warns malformed.
- **Quoted sequence elements (codex r3649857873):** `_parse_simple_yaml`
  keeps surrounding quotes on list elements, so a quoted Windows path like
  `['C:\\Users\\me\\a.jsonl']` slipped past the drive-letter and colon
  checks. Now each element is quote-stripped before the checks (also applied
  to `instruction_source`).
- **Non-string values (codex r3649857881):** an unquoted YAML bool
  (`session_transcript: true`) parsed to `bool` and was silently skipped;
  now warns malformed.

Added 3 tests (colon near-misses, non-string bool, quoted-absolute in a
sequence). None of the comments conflicted with a design decision.

# Validation

- `scripts/format --check` — clean
- `scripts/lint` — clean
- `scripts/test` — 808 tests, OK (+3 over the implementation commit)
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning; 0 new warnings
  on the real records

# Follow-up

- Confirm-fixes pass to resolve the 4 threads, then human merge gate.
