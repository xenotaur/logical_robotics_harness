---
execution_id: 2026_10_09_05_51_11_WI_EXECUTE_OPEN_PREREQ_PR_STOP_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EXECUTE_OPEN_PREREQ_PR_STOP_IMPL_REVIEW)[2026-10-08T06:33:04+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_10_08_06_29_00_WI_EXECUTE_OPEN_PREREQ_PR_STOP
pr: https://github.com/xenotaur/logical_robotics_harness/pull/795
commit: 0a6e845439bbf8355c68de75a1199d6b4089b1c9
created_at: 2026-10-09T05:51:11Z
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/795
session_transcript: claude-app:e4c60740-30c9-4440-8717-474f04557750
---

# Summary

Review-response round 1 on PR #795: three Copilot threads, all valid, all
fixed. Run from /lrh-land inside /lrh-execute.

# Result

1. Nested projects (2 sites): git ls-tree prints cwd-relative names but
   git show origin/main:$path reads from the repo root, so an LRH project
   below the repo root (e.g. lcats/) was falsely marked unavailable. Now
   git show "origin/main:./$path" at all three snippets, and the open-PR file
   match prepends git rev-parse --show-prefix. Added a behavioral test that
   extracts the docs' own bash snippets and runs them in real temp repos,
   at the repository root and nested.
2. The WS-ID lazy open-PR lookup now covers only candidates skipped by the
   availability check, not candidates that are proposed but failed
   depends_on/readiness/execution-record checks.
3. The "stale ref never gives a false positive" claim (2 sites) is replaced:
   the fetch is a point-in-time snapshot, and a failed fetch is an explicit
   blocker.
Every instance of each pattern was grepped before editing. No comment was
dismissed.

# Validation

format --check, lint, lrh validate pass; the new tests fail against the
previous commit's text (5 failures) and pass now (19 tests). Full suite
re-run before the push.

# Follow-up

confirm-fixes verifies and resolves the threads. session_transcript is
still pending.
