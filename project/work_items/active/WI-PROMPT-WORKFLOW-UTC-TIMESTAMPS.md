---
resolution: null
blocked_reason: null
blocked: false
id: WI-PROMPT-WORKFLOW-UTC-TIMESTAMPS
title: Generate execution-record filename timestamps from UTC, not local time
type: deliverable
status: active
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - rewrite_existing_execution_record_filenames
  - rewrite_existing_execution_record_created_at_values
acceptance:
  - datetime.datetime.now(datetime.timezone.utc) is used directly (no .astimezone()) as the single now value in run_prompt_cli's record/label path in src/lrh/prompt_workflow.py
  - the filename timestamp (timestamp_for_file, prompt_workflow.py:64) and the timestamp_for_id value (prompt_workflow.py:310) are both generated from that UTC now, so newly-created filenames sort lexicographically in true chronological order regardless of the host machine's local timezone
  - a new unit test asserts filename/timestamp generation is UTC regardless of the TZ environment variable at generation time (e.g. by monkeypatching TZ to two different non-UTC offsets and asserting identical, correctly-ordered output)
  - existing execution records' filenames and created_at values are left untouched; no migration or rewrite of historical records
  - lrh validate passes with 0 errors and the full test suite passes
required_evidence:
  - code_diff
  - unit_tests
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/prompt_workflow.py
  - tests/assist_tests/prompt_workflow_test.py
---

# Generate execution-record filename timestamps from UTC, not local time

## Summary

Fix `src/lrh/prompt_workflow.py:299` so the timestamp used to build
execution-record filenames and `PROMPT(...)[<timestamp>]` IDs is derived
directly from UTC, instead of being converted to the local system
timezone first — so filename lexicographic sort order matches true
chronological order on every machine, regardless of its local offset.

## Problem / Context

`src/lrh/prompt_workflow.py:299` reads:

```python
now = datetime.datetime.now(datetime.timezone.utc).astimezone()
```

This captures the correct UTC instant, then immediately calls
`.astimezone()` with no argument — which converts it to whichever
timezone the *local host* happens to be configured for, before that value
is used anywhere downstream:

- `timestamp_for_file` (`prompt_workflow.py:64`, via
  `suggested_execution_path`) formats it with
  `now.strftime("%Y_%m_%d_%H_%M_%S")` — no UTC offset in the output at
  all, into the execution-record filename.
- `timestamp_for_id` (`prompt_workflow.py:310`) formats the same local
  value the same way, for the execution record's `execution_id`.
- `build_prompt_label` (`prompt_workflow.py:51-54`) and the `created_at`
  frontmatter field (`prompt_workflow.py:331`) use `now.isoformat(...)`
  instead, which *does* retain the local UTC offset (e.g. `-04:00`) — so
  those two fields remain individually correct and comparable once
  parsed. The bug is specific to the two `strftime`-based, offset-free
  outputs: the filename and `execution_id`.

Because the filename carries no offset, two records created at the same
real instant produce different filename timestamps depending on the
generating machine's timezone — and worse, their **lexicographic order
can invert true chronological order**: a record created at local
`09:00-04:00` (`13:00 UTC`) sorts *before* one created at local
`12:00+00:00` (`12:00 UTC`), even though the first happened later in
real time. Every place that relies on "sort execution-record filenames,
take the last one, that's the most recent match" inherits this gap —
confirmed present in the idempotence checks of `lrh-proposal`,
`lrh-work-item`, `lrh-workstream`, and `lrh-review-response`.

PR #441 (harness) hit this directly during its cross-PR idempotence-check
hardening and worked around it *without* touching this file: it changed
the recency comparison in those four skills to read each candidate
match's `created_at:` frontmatter value and compare actual parsed
timestamps, rather than trusting filename order. That workaround is
already merged and correct on its own terms — it does not depend on this
work item to keep working. This work item fixes the root cause the
workaround was built around, so that filename order becomes trustworthy
again for any code (present or future) that assumes it, rather than only
for the specific call sites already patched.

Prior-art check performed 2026-07-30:

- **Duplication search:** `grep -rl idempoten project/work_items/` and a
  search for other work items touching `prompt_workflow.py`'s timestamp
  generation return no matches. The only existing reference to this bug
  is the "Execution-record filename timestamps use local time, not UTC"
  entry in `project/design/backlog.md`, which this work item resolves.
  Verdict: no duplicate.
- **Demand search:** the backlog entry itself, PR #441's round-5 review
  finding it cites, and the user confirming interest in resolving it as a
  companion to `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` (2026-07-30 session).
  Verdict: demand exists, previously deferred rather than uncaptured.

## Scope

Change the single `now` construction in `run_prompt_cli`'s
record/label path (`src/lrh/prompt_workflow.py:299`) to use the UTC
instant directly, with no local-timezone conversion. No other file needs
to change — `timestamp_for_file`, `timestamp_for_id`,
`build_prompt_label`, and the `created_at` field all already consume this
one `now` value; fixing it at the source fixes all four consistently.

This work item **shares `src/lrh/prompt_workflow.py` with
`WI-SLUG-IDEMPOTENCE-CLI-TOOLING`** (the new `--slug` cross-PR discovery
mode being added to the same file). Both are small, non-overlapping edits
to the same module (this one touches line 299 only; the other adds a new
subcommand and a new query-layer sibling module), so they can land
together in one PR without one blocking the other — there is no
functional dependency between them.

## Required Changes

- Change `prompt_workflow.py:299` from
  `datetime.datetime.now(datetime.timezone.utc).astimezone()` to
  `datetime.datetime.now(datetime.timezone.utc)`.
- Add a unit test in `tests/assist_tests/prompt_workflow_test.py` that
  monkeypatches the local timezone (e.g. via `TZ` env var and
  `time.tzset()`, or by patching whatever the test suite's existing
  convention is for time-dependent tests) to at least two different
  non-UTC offsets and asserts the generated filename timestamp and
  `execution_id` are identical UTC-based values in both cases — i.e. the
  bug this item fixes cannot regress silently.
- Confirm (by reading, not by executing) that no other code path assumes
  `now` carries the local offset — in particular, that `created_at`'s
  `isoformat()` output changing from a local offset (e.g. `-04:00`) to
  `+00:00` for newly-created records doesn't break any parser that
  expected a specific offset rather than parsing generically.

## Non-Goals

- No rewriting or migrating any existing execution record's filename or
  `created_at` value — this only changes generation of *new* records
  going forward. Historical records keep their local-time-based
  filenames permanently; nothing reads "filename timestamp scheme" as a
  versioned or negotiated field, so old and new records coexist safely.
- No change to the `created_at`-comparison workaround PR #441 already
  added to `lrh-proposal`/`lrh-work-item`/`lrh-workstream`/
  `lrh-review-response` — that logic remains correct and unaffected;
  this item does not require touching those skills at all.
- No change to `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`'s scope — that work item
  already sidesteps this bug via the same `created_at`-comparison
  approach and does not depend on this fix landing first or in any
  particular order.

## Acceptance Criteria

- `prompt_workflow.py:299` generates `now` from UTC directly, with no
  `.astimezone()` call.
- A new unit test proves filename/`execution_id` generation is
  timezone-independent (same UTC result regardless of the host's local
  `TZ` setting).
- No existing execution record is modified.
- `lrh validate` reports 0 errors; full test suite passes.

## Validation

- `pytest tests/assist_tests/prompt_workflow_test.py` (including the new
  timezone-independence test) passes.
- Manual check: run `lrh prompt label --slug <test-slug>` under two
  different `TZ` values (e.g. `TZ=America/New_York` and `TZ=UTC`) and
  confirm the resulting filename timestamps reflect the same real
  instant rather than each machine's local wall-clock time.
- `lrh validate` reports 0 errors.

## Risk Notes

Low blast radius: one line of production code, additive test-only
change otherwise, and no effect on any existing file. The only behavior
visible to existing tooling is that `created_at` on newly-created records
will show a `+00:00` offset instead of the generating machine's local
offset — worth a one-line mention in whichever PR description lands this,
but not a compatibility break, since every consumer of `created_at`
already parses it as a timezone-aware ISO 8601 value rather than assuming
a specific offset.
