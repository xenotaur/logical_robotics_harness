---
resolution: null
blocked_reason: null
blocked: false
id: WI-REVIEW-RESPONSE-ISSUE-COMMENTS
title: Surface PR issue-comment findings in lrh request review_response
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - A PR with a real finding posted only as an issue comment (no reviewThreads entry) surfaces in review_response's prompt output
  - A PR with zero unresolved threads but an unaddressed issue-comment finding does not short-circuit to "Nothing to resolve"
  - Existing thread-only behavior is unchanged when no issue comments are present (regression coverage)
  - New unit tests cover the formatter, the fetch wiring, and the early-return gate change
  - lrh validate reports 0 errors; scripts/test passes
required_evidence:
  - test_output
  - lrh_validate
  - manual_review
artifacts_expected:
  - src/lrh/assist/request_service.py
  - src/lrh/integrations/github/formatters.py
  - src/lrh/assist/templates/request/review_response.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - .claude/skills/lrh-review-response/SKILL.md
  - tests/assist_tests/request_service_test.py
  - tests/integrations_tests/github_integration_test.py
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md (inspect only, per Required Change 5; edit only if it inlines or calls review_response directly)
  - src/lrh/skills/lrh-land/SKILL.md (inspect only, per Required Change 5; edit only if it inlines or calls review_response directly)
---

## Summary

`lrh request review_response`'s `generate_request()` only fetches and
surfaces formal GitHub `reviewThreads`, never issue comments — even
though `pull_reviews.get_pull_comments()` already fetches
`issue_comments` for other call sites. Wire issue comments into this
command's fetch, formatting, and early-return gate so a finding (or a
clean-pass confirmation) posted only as a PR issue comment is not
silently missed.

## Problem / Context

Surfaced in the LCATS repo during WI-ASSESS-0031's 5-round
review-response loop on PR #224 (2026-08-06): `chatgpt-codex-connector`
posted real findings via two inconsistent GitHub surfaces across rounds
of the same PR — sometimes a formal `reviewThreads` entry, sometimes a
plain PR issue comment (even a "clean pass" confirmation landed as an
issue comment in three separate rounds). Relying on `review_response`'s
current output would have missed real findings, or missed a clean pass
and kept waiting unnecessarily.

Confirmed directly against this repo's current source (2026-08-08):

- `src/lrh/integrations/github/pull_reviews.py:159`'s `get_pull_comments()`
  already fetches `issue_comments` (`GET .../issues/{n}/comments`)
  alongside `review_comments` and `review_threads`.
- `src/lrh/assist/request_service.py:125`'s `generate_request()` (the
  `review_response` code path) calls only
  `pull_reviews.get_pull_review_threads()`. `get_pull_comments()` is
  invoked elsewhere (`src/lrh/cli/github.py:58`, feeding
  `formatters.format_comments`, a different CLI surface) but never
  reaches `review_response`.
- `src/lrh/assist/templates/request/review_response.md` interpolates
  only `{{UNRESOLVED_THREADS}}`, built by
  `formatters.format_threads_review()` from `reviewThreads` data alone
  (`request_service.py:158`). There is no `{{ISSUE_COMMENTS}}` or
  equivalent variable.
- `request_service.py:148-156`: when `has_threads_for_state(...,
  state="unresolved")` is false and `--force`/`--include-thread` wasn't
  passed, the request short-circuits to `"Nothing to resolve"` without
  checking for an issue-comment-only finding. This reproduces the
  "missed a clean pass / missed a real finding" failure mode exactly.

**Checked and ruled out:** the original report also suspected a formal
review's `body` text could carry misleading boilerplate while real
findings live in separate threads. Grepped `pull_reviews.py` and
`formatters.py` for `.get("body")` / `review.*body`: the only such call
(`formatters.py:116`) reads a **thread comment's** body, not a review's
top-level `body` field, and nothing in the `review_response` path reads
a review body at all. This gap is not reachable in current code — no fix
needed for it.

### Duplication search
- In-repo: No existing implementation of issue-comment surfacing in
  `review_response`. Related but distinct: `formatters.format_comments`
  (used by `src/lrh/cli/github.py`, a separate CLI command) already
  formats issue comments for a different purpose.
- Sibling repos: None identified.
- External libraries: None identified — this is GitHub API plumbing
  specific to LRH's request-generation flow.
- Recommendation: Proceed.

### Demand search
- Work items: None found for issue comments specifically. Adjacent:
  `WI-REVIEW-RESPONSE-INCLUDE-THREAD` (resolved, PR #497) fixed a
  different `review_response` gap (surfacing a specific outdated-but-
  unresolved thread), not issue comments.
- Proposals: None found.
- Backlog: `project/design/backlog.md` has an entry on
  `review_response`'s unresolved-thread filter gap (lines 46-129,
  "cannot surface a specific outdated-but-unresolved thread") — related
  area, distinct root cause, no overlap with issue comments.
- Recommendation: No action; proceed as new item.

## Scope

- Fetch issue comments alongside review threads in `review_response`'s
  `generate_request()` path.
- Format issue comments into a new template variable and surface them in
  `review_response.md`.
- Extend the early-return gate to also detect unaddressed issue-comment
  findings.
- Propagate the fix to skills that wrap this command.

## Required Changes

1. In `src/lrh/assist/request_service.py`, call
   `pull_reviews.get_pull_comments()` (or its `issue_comments` half)
   alongside the existing `get_pull_review_threads()` call in
   `generate_request()`.
2. Add a formatter in `src/lrh/integrations/github/formatters.py`
   mirroring `format_threads_review()`'s shape (path/URL/author/body per
   entry) for issue comments.
3. Add an `{{ISSUE_COMMENTS}}` template variable to
   `src/lrh/assist/templates/request/review_response.md` and populate it
   from the new formatter in `request_service.py`.
4. Extend the `request_service.py:148-156` early-return gate to also
   check for unaddressed issue-comment findings before short-circuiting
   to "Nothing to resolve". Define "unaddressed" for an issue comment
   (which has no `isResolved`/`isOutdated` state): first cut may be "all
   issue comments newer than the PR's last review-response run" or
   simply "always include" if resolving true addressed/unaddressed
   state needs its own investigation — document whichever is chosen.
5. Propagate the fix to `src/lrh/skills/lrh-review-response/SKILL.md`
   (mirror to `.claude/skills/lrh-review-response/SKILL.md`), and check
   `lrh-confirm-fixes`/`lrh-land` for any place they inline or call
   `review_response` directly.
6. Add unit tests covering the new formatter, the fetch wiring, and the
   early-return gate change.

## Non-Goals

- Do not resolve full addressed/unresolved state tracking for issue
  comments if it requires its own investigation — a documented
  first-cut heuristic (e.g. "always include") is acceptable.
- Do not touch review-body-as-findings handling — confirmed not
  reachable in the current `review_response` code path (see Problem /
  Context).
- Do not change `src/lrh/cli/github.py`'s existing `format_comments`
  path, which serves a different command.
- Do not fix the unrelated outdated-but-unresolved-thread gap tracked
  separately in `project/design/backlog.md`.

## Acceptance Criteria

- A PR with a real finding posted only as an issue comment (no
  `reviewThreads` entry) surfaces in `review_response`'s prompt output.
- A PR with zero unresolved threads but an unaddressed issue-comment
  finding does not short-circuit to "Nothing to resolve".
- Existing thread-only behavior is unchanged when no issue comments are
  present (regression coverage).
- New unit tests cover the formatter, the fetch wiring, and the
  early-return gate change.
- `lrh validate` reports 0 errors; `scripts/test` passes.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- Issue comments include non-review noise (CI bot chatter, unrelated PR
  discussion); the formatter/gate should avoid flooding the prompt with
  irrelevant comments — consider filtering by known reviewer bot logins
  or requiring a minimum recency window.
- Without a real `isResolved` equivalent for issue comments, the
  "unaddressed" heuristic risks either false negatives (missing a real
  finding) or false positives (re-surfacing an already-handled comment
  every run) — document the chosen tradeoff clearly for future
  maintainers.
