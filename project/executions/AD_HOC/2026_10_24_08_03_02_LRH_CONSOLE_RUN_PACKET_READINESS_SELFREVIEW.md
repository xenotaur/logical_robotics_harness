---
execution_id: 2026_10_24_08_03_02_LRH_CONSOLE_RUN_PACKET_READINESS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_RUN_PACKET_READINESS_SELFREVIEW)[2026-10-24T08:03:01+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_24_08_03_01_LRH_CONSOLE_RUN_PACKET_READINESS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/855
commit:
created_at: 2026-10-24T08:03:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/855
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers a diff-mode `/lrh-self-review` of `WI-LRH-CONSOLE-RUN-PACKET-READINESS` (commit `3d161eca`), run before the PR's first push (PR #855). A cold-context `general-purpose` subagent did the review, report-only. It used probes against `core_state`, `run_packet` and `serve`.

# Result

There were no High or Medium issues.

- **The implementer's claim was confirmed:** a declared but failing run-packet item blanks the project. Probes covered ten cases:
  - only the flag;
  - `execution_ready: false` with other fields;
  - a bad enum;
  - a wrong type;
  - an empty list;
  - a missing `autonomy_level`;
  - `max_review_rounds: 0`;
  - a bad `title`;
  - `id: 7`;
  - `required_evidence` only.

  All but the last gave 0 items and a 404; `required_evidence` only correctly shows Not declared. The reason: every `execution_readiness` issue is an error, and none is exempt from `_has_state_blocking_errors`.
- **The refactor is byte-for-byte unchanged:** same calls, argument order and concatenation order.
- **Blocked escaping and gating are correct.** No other `status == "blocked"` check is in scope; `_blocked_work_item_count` feeds the Statusboard counts, which the work item excludes.
- **The exception coverage is complete** for files that loaded.
- **Low items fixed in `47bd9de0`:**
  - **L1:** the proposal date.
  - **L2:** the stale "four terms" intro.
  - **L3:** the public `run_packet.validate_frontmatter` shared a name with `execution_readiness.validate_frontmatter`; it is now private, and the proposal citation is qualified.
  - **L4:** a redundant `UnicodeDecodeError`.
- **L5:** Copy stays enabled on closed items with valid fields. This matches the acceptance literally and the old behavior, so it is noted in the PR, not changed.
- **Pre-existing, noted:** an empty `title` passes `lrh validate` but makes the loader raise.

# Validation

- The reviewer's runs: `scripts/lint` exit 0, `scripts/format --check` exit 0, the serve and run-packet tests (137 OK), and `lrh validate` with 0 errors.

# Follow-up

- None from the review. The PR's first push gets the hosted bot review.
