---
execution_id: 2026_10_10_17_59_40_LRH_CONSOLE_CACHE_WARMUP_CONFIRM
prompt_id: PROMPT(WI-LRH-CONSOLE-CACHE-WARMUP:LRH_CONSOLE_CACHE_WARMUP_CONFIRM)[2026-10-10T17:59:40+00:00]
work_item: WI-LRH-CONSOLE-CACHE-WARMUP
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/817
commit:
agent: "claude_app"
instruction_source: "https://github.com/xenotaur/logical_robotics_harness/pull/817"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-10T17:59:40+00:00
---

# Summary

This record covers confirm-fixes for PR #817 (`WI-LRH-CONSOLE-CACHE-WARMUP`), run as part of
`/lrh-land` inside `/lrh-execute`. Hosted review bots review only a PR's first push, so a
cold-context substitute review stood in for them on the review-round head.

# Result

- **Substitute review** of `a55211b5..634d7169`:
  - all four bot threads are Clear-satisfied: fallback publish, control-dir de-duplication,
    reporting failed views, and sizing the cache;
  - each new test fails without its fix;
  - no blocking or medium regressions.
  The four threads were resolved after verification.
- **Owner-approved fixes** from the review, in `f3b2da1945ee360e3e253f45951f01ce64a83d31`:
  - A root without a `project/` directory was reported as a failure on every start, for example
    when running `lrh serve` in a plain directory, which is a supported mode. Such roots are now
    left out of the warm-up plan.
  - The de-duplication key resolves symlinks, so a symlinked `project/` is warmed only once.
  - Warm-up messages are cut to 300 characters.
  - Each has a test that fails without the fix.
- **Accepted as is:**
  - A late fallback can overwrite a newer entry with an older-fingerprint value. It is never
    served, and costs one extra rebuild.
  - Planning runs before `/meta`. It reads metadata only, and never makes the first request
    slower.
  - Minor test gaps remain: the timeout-path publish, and an end-to-end nested `project_dir`.
- **CI:** 7/7 green on `634d7169`. The final head is checked before the merge ask.

# Validation

- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `tests/smoke/desktop_protocol_smoke.py` pass.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `WI-LRH-CONSOLE-DESKTOP-LOADING-CUE`, and the pending owner check that edits appear without a
  restart.
