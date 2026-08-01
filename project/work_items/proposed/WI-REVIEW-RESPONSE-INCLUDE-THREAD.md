---
resolution: null
blocked_reason: null
blocked: false
id: WI-REVIEW-RESPONSE-INCLUDE-THREAD
title: Add --include-thread flag to lrh request review_response
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-EXECUTE
related_design:
  - project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_land_skill_flow
acceptance:
  - "lrh request review_response <pr> --include-thread <id> includes that thread's content even when isOutdated=true and no other unresolved threads exist"
  - Supplying --include-thread implies --force (no separate --force needed)
  - An --include-thread ID not present in the fetched thread list produces a clear error, not a silent no-op
  - An --include-thread ID that is already resolved (isResolved=true) by fetch time is not force-included -- a clear, distinct result, not a silent no-op or a stale re-surfacing
  - Existing default (no-flag) behavior is unchanged -- state="unresolved" still excludes outdated threads
  - New unit tests cover _matches_state/format_threads_review with extra_ids, the review_response branch with --include-thread and zero normal-unresolved threads, and CLI argument parsing
  - lrh validate reports 0 errors
  - scripts/test passes
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/assist/request_cli.py
  - src/lrh/assist/request_service.py
  - src/lrh/integrations/github/formatters.py
  - tests/integrations_tests/github_integration_test.py
  - tests/assist_tests/request_service_test.py
  - tests/assist_tests/request_cli_test.py
---

# Add `--include-thread` flag to `lrh request review_response`

## Summary

Add a repeatable `--include-thread <thread-id>` flag to
`lrh request review_response` so it can surface one or more specific
outdated-but-unresolved GitHub review threads by ID, independent of its
default narrow "unresolved" filter.

## Problem / Context

`lrh request review_response`'s notion of unresolved excludes outdated
threads (`src/lrh/integrations/github/formatters.py`'s `_matches_state`,
default branch requires `not isResolved and not isOutdated`), so an
outdated-but-unresolved thread that `/lrh-confirm-fixes` classifies as
needing a real fix is invisible to it entirely. This work item is Layer 1
of `PROP-OUTDATED-THREAD-RECOVERY` — the mechanical prerequisite Layer 2
(the governed `/lrh-land` recovery flow,
`WI-LRH-LAND-OUTDATED-THREAD-RECOVERY`) depends on.

### Duplication search
- In-repo: No existing implementation. `--force` already exists
  (`src/lrh/assist/request_cli.py`) but only bypasses the early exit, not
  the `state="unresolved"` filter itself
  (`src/lrh/assist/request_service.py:122-142`).
  `formatters._matches_state` already supports `state="all"`/`"outdated"`
  but isn't wired into the `review_response` template path.
- Sibling repos: None identified (Taurcode checked; no matching mechanism).
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: Found — `PROP-OUTDATED-THREAD-RECOVERY` (this item implements
  its Layer 1).
- Backlog: Found — `project/design/backlog.md`, "`lrh request
  review_response` cannot surface a specific outdated-but-unresolved
  thread." This work item, together with
  `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY`, is what that entry is waiting
  on before it can close.
- Recommendation: The backlog entry is already linked to this item (done
  when both were filed); close it only once this item and
  `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY` are both implemented and
  resolved — not merely filed.

## Scope

- Add `--include-thread <thread-id>` (repeatable) to `lrh request
  review_response`'s CLI.
- Thread an `extra_ids` set through the formatter functions that decide
  thread inclusion.
- Validate supplied thread IDs against the fetched thread list; error
  clearly if not found.
- Add unit test coverage for the new flag and formatter behavior.
- Does **not** touch `/lrh-land` or `/lrh-review-response` `SKILL.md` —
  that's `WI-LRH-LAND-OUTDATED-THREAD-RECOVERY`.

## Required Changes

1. `src/lrh/assist/request_cli.py` — add `--include-thread`
   (`action="append"`, default `[]`), documented alongside `--force`.
2. `src/lrh/integrations/github/formatters.py` — extend
   `_matches_state(thread, state, extra_ids=None)` to also return `True`
   when `thread.get("id") in extra_ids` **and the thread is not already
   resolved** (`not thread.get("isResolved", False)`) — a thread named
   via `--include-thread` that was resolved between confirm-fixes'
   classification and this command's fetch must not be force-included;
   thread `extra_ids` through `format_threads_review`. Add a small
   public helper (e.g. `collect_thread_ids(data) -> set[str]`, built on
   the existing private `_collect_threads`) instead of exposing
   `_collect_threads` itself across the module boundary.
3. `src/lrh/assist/request_service.py` — in the `review_response`
   branch: validate each `args.include_thread` ID exists in the fetched
   thread data via the new public helper (clear error if not found; a
   separate clear result — not a silent no-op or a forced re-fetch — if
   found but already resolved); treat a non-empty list the same as
   `--force` for the early-exit check; pass
   `extra_ids=set(args.include_thread)` into `format_threads_review`.
4. Unit tests in `tests/integrations_tests/github_integration_test.py`
   (formatters), `tests/assist_tests/request_service_test.py`
   (review_response branch), `tests/assist_tests/request_cli_test.py`
   (flag parsing).

## Non-Goals

- Does not change `/lrh-land` or `/lrh-review-response` `SKILL.md` —
  Layer 2 is a separate work item.
- Does not widen the default (no-flag) `review_response` behavior.
- Does not add thread-content injection for any command other than
  `review_response`.

## Acceptance Criteria

- `lrh request review_response <pr> --include-thread <id>` includes that
  thread's content even when it's the only thread and it's outdated.
- `--include-thread` implies `--force`.
- An unknown `--include-thread` ID errors clearly.
- An already-resolved `--include-thread` ID is not force-included; a
  clear, distinct result is returned instead.
- Default no-flag behavior is unchanged (regression-tested).
- New unit tests pass for all three touched modules.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Thread-ID validation must not become a second, divergent thread-fetch
  call — reuse the same `threads_data` already fetched for the normal
  `state="unresolved"` computation.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SKILLS-EXECUTE.md`
- Design: `project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md`
