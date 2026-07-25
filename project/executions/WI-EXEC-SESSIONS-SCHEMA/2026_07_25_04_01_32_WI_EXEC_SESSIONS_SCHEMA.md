---
execution_id: 2026_07_25_04_01_32_WI_EXEC_SESSIONS_SCHEMA
prompt_id: PROMPT(WI-EXEC-SESSIONS-SCHEMA:WI_EXEC_SESSIONS_SCHEMA)[2026-07-25T02:19:37-04:00]
work_item: WI-EXEC-SESSIONS-SCHEMA
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/421
commit: e7d7a0eb1a74ab21e0245f58798e8afbe54b2424
created_at: 2026-07-25T04:01:32-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-EXEC-SESSIONS-SCHEMA.md
session_transcript: claude-app:4c3d03d6-6ebd-418a-86b2-6f4041feb9db
---

# Summary

Implement WI-EXEC-SESSIONS-SCHEMA — Stage 2 of PROP-LRH-EXECUTION-SESSIONS:
advisory `lrh validate` warnings for the optional execution-session fields,
enforcing the backend-agnostic session pointer grammar from PR #411.

# Result

- **`src/lrh/control/validator.py`:** added `_validate_execution_record` and
  `_is_absolute_pathish`, wired an execution-record pass into
  `validate_project` (full-validate path). Discovers
  `project/executions/**/*.md` (skips `README.md`), parses frontmatter with
  the existing helpers, and warns (never errors) on:
  - `session_transcript` scalar or sequence — per element, skip `pending`/
    `none`; `EXECUTION_SESSION_TRANSCRIPT_ABSOLUTE_PATH` for `/`, `~`, or a
    Windows drive path; else `EXECUTION_SESSION_TRANSCRIPT_MALFORMED` when no
    `<scheme>:` prefix. The drive-letter check requires a path separator after
    the colon so `claude-app:` is never mistaken for `C:\`.
  - `instruction_source` — `EXECUTION_INSTRUCTION_SOURCE_ABSOLUTE_PATH` for
    absolute paths; suggests `promptspace:<relative-path>`.
  - `agent` — intentionally not enum-validated (open-ended `<other>`).
- **`tests/control_tests/validator_test.py`:** added
  `TestExecutionRecordValidation` (9 tests) covering each scheme, both
  sentinels, absolute-path (POSIX/home/Windows) and bare-id transcripts
  (scalar and sequence, incl. one-bad-element), absolute vs. scheme/relative
  instruction_source, open-ended agent, and README-not-parsed.

**Pre-existing corruption surfaced and fixed.** On first run the new pass
caught unresolved git merge-conflict markers (`<<<<<<< / ======= / >>>>>>>`)
in `project/executions/AD_HOC/2026_05_16_19_22_09_LRH_SERVE_UX_REVIEW_CRITERIA.md`
(frontmatter + body, three hunks), silently broken since May 2026. Resolved
all three to the `main` side (`status: in_progress` + review-feedback note;
`pr:`/`commit:` empty, consistent with never-closed-out), at the user's
explicit direction after a stop-and-report. Only file affected.

Prior-art: prompt-ready WI; no duplicate. `depends_on WI-EXEC-SESSIONS-DOCS`
judged non-blocking (README half shipped in #411; grammar documented;
PROMPTS.md prose orthogonal).

Landed via the execute-to-closeout chain: implement plan gate honored, one
review round (4 codex/Copilot comments tightening the scheme check → 4
fixes), human merge gate approved, PR #421 squash-merged as `e7d7a0e`.
WI-EXEC-SESSIONS-SCHEMA resolved and moved to `resolved/`.

CHAIN-NOTE: cycles=1; stops=1; gates=[plan,merge]; friction=pre-existing-merge-conflict-record-blocked-lrh-validate; note="feature caught 2026-05 corruption on first run; user OK'd fixing it in-PR"

# Validation

- `scripts/version tools` — LRH env (black 26.3.1)
- `scripts/format --check` — clean
- `scripts/lint` — clean
- `scripts/test` — 805 tests, OK (+9 new)
- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WS-LRH-ASSISTANTS`); 0 new warnings on the 138 real records

# Follow-up

- WI stays `proposed` until this PR merges and closeout resolves it.
- Absolute-path warning satisfies the Stage-2 privacy check
  `PROP-LRH-EXECUTION-SESSIONS` specified; the sequence form and
  `instruction_source` check were added per PR #420 review feedback.
