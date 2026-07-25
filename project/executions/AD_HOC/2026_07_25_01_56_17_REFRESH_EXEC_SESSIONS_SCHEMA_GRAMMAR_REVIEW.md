---
execution_id: 2026_07_25_01_56_17_REFRESH_EXEC_SESSIONS_SCHEMA_GRAMMAR_REVIEW
prompt_id: PROMPT(AD_HOC:REFRESH_EXEC_SESSIONS_SCHEMA_GRAMMAR_REVIEW)[2026-07-25T01:55:48-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_07_25_01_33_44_REFRESH_EXEC_SESSIONS_SCHEMA_GRAMMAR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/420
commit: 2237fd9
created_at: 2026-07-25T01:56:17-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/420
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---

# Summary

Address 3 review comments on PR #420 (refresh of WI-EXEC-SESSIONS-SCHEMA).
All three were valid; two made the WI more faithful to the decision-log
grammar, which the refresh had under-covered.

# Result

- **Scheme examples missing trailing colon (Copilot r3649556145):** the
  frontmatter acceptance example read `claude-app, codex-cloud, chatgpt`,
  which looks like the scheme is `claude-app` not `claude-app:`. Added
  trailing colons and backticks (`claude-app:`, `codex-cloud:`, `chatgpt:`)
  in the frontmatter to match the canonical `<backend>:` form.
- **Sequence form uncovered (codex P2 r3649557295):** the decision-log
  grammar permits `session_transcript` to be a *sequence* of scalars for
  genuinely multi-backend executions, but the refresh spoke only of scalars.
  Added acceptance criteria, a Required-Changes step (normalize scalar-or-
  sequence to a list; validate each element), and tests (all-valid sequence
  → no warning; sequence with a malformed element → warns on that element).
- **instruction_source absolute-path check missing (codex P2 r3649557298):**
  the same decision forbids absolute paths for `instruction_source` and
  requires scheme-prefixed external refs (e.g. `promptspace:`), but the WI
  claimed to validate all three fields while checking only two. Added an
  absolute-path advisory-warning criterion, a Required-Changes step, and
  tests for absolute vs. `promptspace:`/repo-relative `instruction_source`.

None conflicted with a design decision. The `agent` open-endedness call was
untouched.

# Validation

- `lrh validate` — 0 errors (1 pre-existing unrelated warning)
- `lrh work-items validate` — no warnings attributable to this WI
- `lrh work-items readiness WI-EXEC-SESSIONS-SCHEMA` — `prompt_ready: yes`

# Follow-up

- Confirm-fixes pass to resolve the 3 threads, then human merge gate.
- Cosmetic: the fixes commit (`2237fd9`) message embeds a guessed prompt-id
  timestamp (`01:52:00`) minted before the label call returned `01:55:48`;
  this record and its idempotence key carry the correct `01:55:48` ID. Not
  force-pushed. See [[reference_macos_date_colon_z]] neighbor lesson: copy
  `lrh prompt label` output verbatim, and mint before writing the commit.
