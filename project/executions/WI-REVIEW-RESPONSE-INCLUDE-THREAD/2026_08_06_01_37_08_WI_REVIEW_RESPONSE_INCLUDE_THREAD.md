---
execution_id: 2026_08_06_01_37_08_WI_REVIEW_RESPONSE_INCLUDE_THREAD
prompt_id: PROMPT(WI-REVIEW-RESPONSE-INCLUDE-THREAD:WI_REVIEW_RESPONSE_INCLUDE_THREAD)[2026-08-01T17:05:30-04:00]
work_item: WI-REVIEW-RESPONSE-INCLUDE-THREAD
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/497
commit: ea57443a1543cbe169ec67eeaf21c22722a382f6
created_at: 2026-08-06T01:37:08-04:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-REVIEW-RESPONSE-INCLUDE-THREAD.md
session_transcript: pending
---

# Summary

Implements WI-REVIEW-RESPONSE-INCLUDE-THREAD: adds a repeatable
`--include-thread <thread-id>` flag to `lrh request review_response` so
it can surface a specific outdated-but-unresolved GitHub review thread
by ID, independent of the default unresolved-and-current filter. Layer 1
(mechanical) of PROP-OUTDATED-THREAD-RECOVERY; WI-LRH-LAND-OUTDATED-THREAD-RECOVERY
(Layer 2) depends on this.

# Result

One commit (`ea57443`) on branch `xenotaur/feat/wi-review-response-include-thread`,
PR #497:

- `src/lrh/integrations/github/formatters.py` — new public
  `collect_thread_ids()`/`resolved_thread_ids()` helpers;
  `_matches_state()` gains an `extra_ids` param (matches a named thread
  ID unless it's already resolved, per the WI's race-condition
  requirement); `format_threads_review()` threads it through.
- `src/lrh/assist/request_cli.py` — new `--include-thread` flag
  (repeatable, `action="append"`) on the `review_response`-relevant
  parser only (a second, unrelated `--force`/parser pair exists for
  `codex_prompt_from_work_item` and was left untouched).
- `src/lrh/assist/request_service.py` — in the `review_response` branch:
  validates each `--include-thread` ID against `collect_thread_ids()`
  (raises `ValueError`, caught by the CLI as exit 2, for an unknown ID);
  separately checks `resolved_thread_ids()` and raises a distinct
  `ValueError` for an already-resolved ID rather than silently omitting
  it; a non-empty `--include-thread` list implies `--force` for the
  early-exit check; passes `extra_ids` into `format_threads_review`.
- Unit tests added to all three touched modules' existing test files.

All items in the WI's `acceptance:` list are met, including the two
added mid-implementation for robustness (already-resolved-ID handling,
public helper instead of reaching across the module boundary to the
private `_collect_threads`) that PR #457's own review surfaced during
design.

# Validation

scripts/version tools — Black 26.3.1, Ruff 0.15.12 confirmed
scripts/format --check --diff — 179 files unchanged (after one
`black`-applied reformat of the new CLI test file)
scripts/lint — all checks passed
scripts/test — 830 tests, OK
lrh validate — 0 errors, 1 pre-existing unrelated warning
(`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-LRH-ASSISTANTS`)

# Follow-up

- Update `session_transcript: pending` to `claude-app:<host-uuid-stem>`
  after the session ends.
- `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY` (Layer 2) depends on this item
  being resolved before it can be selected for implementation.
