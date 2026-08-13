---
execution_id: 2026_08_06_23_48_57_WI_REVIEW_RESPONSE_INCLUDE_THREAD_REVIEW
prompt_id: PROMPT(AD_HOC:WI_REVIEW_RESPONSE_INCLUDE_THREAD_REVIEW)[2026-08-06T23:37:19-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_06_01_37_08_WI_REVIEW_RESPONSE_INCLUDE_THREAD
pr: https://github.com/xenotaur/logical_robotics_harness/pull/497
commit: 9b85e4804046b36db7706f059e0abbb35ba96eb7
created_at: 2026-08-06T23:48:57-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/497
session_transcript: claude-app:61881211-bfd7-40cb-8080-33938a265398
---

# Summary

Addresses the one review comment on PR #497 (implementation of
WI-REVIEW-RESPONSE-INCLUDE-THREAD). Copilot found a real latent bug in
the `extra_ids` change to `_matches_state`.

# Result

One commit pushed to branch `xenotaur/feat/wi-review-response-include-thread`:

- `9b85e48` — fixes the `extra_ids`/`state` interaction bug.

**Issue A — `extra_ids` bypasses the `state` filter entirely (Copilot):**
Fixed. `_matches_state`'s `extra_ids` check ran before the `state`
branching, so a thread named in `extra_ids` would incorrectly match
`state="resolved"`, `state="outdated"`, or `state="all"` queries too —
not just the intended `state="unresolved"` case. Not reachable in the
current code path (`format_threads_review`, the only caller passing
`extra_ids`, always calls with `state="unresolved"`), but a real latent
bug in a shared internal helper. Moved the `extra_ids` check into the
`unresolved`-only branch and added
`test_matches_state_extra_ids_does_not_leak_into_other_states` to lock
in the corrected scoping.

# Validation

scripts/version tools — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff — 179 files unchanged
scripts/lint — all checks passed
scripts/test — 831 tests, OK
lrh validate — 0 errors, 1 pre-existing unrelated warning
(`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- Update `session_transcript: pending` to `claude-app:<host-uuid-stem>`
  on the primary record if it differs after the session ends (this
  record's own `session_transcript` is already the resolved value).
- Suggest running `/lrh-confirm-fixes` before merge to verify the fix
  against the current diff and resolve the review thread.
