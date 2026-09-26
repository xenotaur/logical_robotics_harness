---
resolution: null
blocked_reason: null
blocked: false
id: WI-TEST-OUTPUT-SUPPRESSION-AUDIT
title: Audit and suppress extraneous LRH unit-test print output
type: operation
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
  - create_file
  - edit_file
  - run_tests
forbidden_actions:
  - suppress_output_globally
  - modify_scripts_test_for_global_suppression
  - force_push
  - delete_branch
acceptance:
  - "A shared, unittest-compatible output-capture/suppression helper exists, providing at least a capture-for-assertion context manager and a pure-suppress context manager (no pytest fixtures)."
  - "STYLE.md documents the per-test suppression policy in the Testing Principles section, explicitly stating that scripts/test itself must never gain a global output-suppression mechanism."
  - "The confirmed noisy test files identified in the audit (starting from tests/cli_tests/pii_test.py, tests/cli_tests/secrets_test.py, tests/dev_tests/release_smoke_test.py) are updated to use the new helper instead of leaking library/CLI print() output."
  - "The 12 test files already using the ad hoc io.StringIO()+contextlib.redirect_stdout/redirect_stderr pattern (e.g. tests/cli_tests/main_test.py) are migrated to the new shared helper."
  - "src/lrh/control/test_guardrails.py gains a check that flags a test method invoking a known in-process CLI/library entry point without the new helper wrapping the call, wired into the existing scripts/lint invocation."
  - "A baseline vs. final scripts/test output comparison is captured in the execution record, analogous to LCATS's WI-TEST-0107 evidence."
  - "lrh validate reports 0 errors."
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/shared/test_capture.py
  - STYLE.md
  - src/lrh/control/test_guardrails.py
  - tests/cli_tests/pii_test.py
  - tests/cli_tests/secrets_test.py
  - tests/dev_tests/release_smoke_test.py
  - tests/cli_tests/main_test.py
---

## Summary

Add a shared, per-test output-capture/suppression helper for LRH's unit
tests, document the policy in STYLE.md, extend the existing
`test_guardrails.py` lint check to catch unwrapped in-process CLI/library
invocations, and use the helper to quiet the confirmed noisy test files —
without adding any global suppression mechanism to `scripts/test`.

## Problem / Context

A live `scripts/test` run on 2026-09-25 showed extensive print noise
interleaved with the dot-per-test output (JSON blobs, "release smoke
passed", fabricated `error: ...` lines, git subprocess chatter). A
same-session audit traced this to a specific, well-understood mechanism:
LRH's own testing principle of preferring "real in-process objects...
over heavy mocking" (`STYLE.md:348`) means ~30 of 116 test files invoke
CLI/library code in-process (e.g. `cli_main.main()`, `release_smoke.*`)
rather than via subprocess, and those code paths' legitimate `print()`
calls (386 total across `src/lrh`, e.g. `src/lrh/cli/main.py:1491-1511`)
leak straight into the test runner's own stdout/stderr because nothing
captures them. Two concrete, independently traced chains: (1)
`tests/cli_tests/pii_test.py:73` calls `cli_main.main()` in-process with
no redirect, producing both the `{"findings_count": ...}` JSON line (`src/lrh/cli/main.py:1511`)
and the fabricated `error: bad config` / `error: git rev-parse failed`
lines, which are real `print(f"error: {err}", file=sys.stderr)` calls
(`src/lrh/cli/main.py:1491-1508`) hit via mocked exceptions
(`tests/cli_tests/pii_test.py:113,149`), not real git stderr. (2)
`tests/dev_tests/release_smoke_test.py` calls into
`src/lrh/dev/release_smoke.py` in-process, which owns the "Using wheel:
...", "release smoke passed", "Preserved smoke environment: ..." prints
(15 `print()` calls in that one file).

LRH already has an *informal* version of the fix: 12 test files
(e.g. `tests/cli_tests/main_test.py:11-20`) hand-roll
`io.StringIO()` + `contextlib.redirect_stdout`/`redirect_stderr` per test
method, but this was never formalized into a shared helper, and the
noisiest files (`pii_test.py`, `release_smoke_test.py`, `secrets_test.py`)
don't use it at all. `STYLE.md` has no policy on print/output hygiene
anywhere in its 676 lines, and `pyproject.toml:83`'s ruff `select` list
(`["E", "F", "I", "TID"]`) has no print-related rule.

The sibling repo LCATS solved the identical problem via `WI-TEST-0107`
("Survey and suppress extraneous LCATS test output," PR #447): a
`lcats.utils.capture` module with `capture_output()`/`suppress_output()`
context managers, a STYLE.md policy (`STYLE.md:28-32`, `STYLE.md:209-223`:
"Avoid printing or use the lcats.utils.capture library to suppress
output"), and an explicit `forbidden_actions` list barring any global
suppression mechanism in their own `scripts/test`. LCATS's own
enforcement gap — no lint/CI rule catches a new bare `print()` from
landing, only documentary discipline — is a place LRH can do better,
since `src/lrh/control/test_guardrails.py` already gives `scripts/lint`
an AST-based hook into every test file (see Required Changes).

### Duplication search

- In-repo: No existing implementation found. Checked `src/`,
  `project/design/proposals/`, `project/workstreams/`,
  `project/work_items/`, `.claude/skills/`, `.agents/skills/` for
  print/output/suppress/capture terminology; no hits.
- Sibling repos: LCATS (`lcats.utils.capture.py`) has a working
  implementation of the same policy this work item ports — not a
  duplicate within this repo, but the primary design reference.
- External libraries: `pytest`'s `capsys`/`capfd` fixtures provide
  equivalent capture, but LRH prohibits `pytest`
  (`pyproject.toml:85-86`, `test_guardrails.py`). Python's stdlib
  `contextlib.redirect_stdout`/`redirect_stderr` (what LCATS's helper and
  LRH's own existing ad hoc pattern both already use) is the correct,
  dependency-free mechanism.
- Recommendation: Proceed.

### Demand search

- Work items: None found. `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION`,
  `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION`, `WI-META-TESTS-LAYOUT-AUDIT`,
  and `WI-CLI-WIRING-TESTS-VALIDATE-GITHUB-WORKSTREAMS` all concern test
  *layout*, not output hygiene.
- Proposals: None found.
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: No action.

## Scope

- Build a shared, unittest-compatible output-capture/suppression helper
  and document its use as project policy.
- Extend `test_guardrails.py` to give the policy a mechanical backstop.
- Apply the helper to the confirmed noisy files and to the files already
  using the informal ad hoc pattern.

## Required Changes

1. Add a shared helper (suggested home: `src/lrh/shared/test_capture.py`,
   or a `tests`-only support module if the implementer judges a
   test-only location preferable to shipping it in the installed
   package — decide and note the reasoning either way). Port LCATS's
   two-context-manager shape (`lcats/src/lcats/utils/capture.py`):
   a `capture_output()` context manager returning captured
   stdout/stderr for assertions, and a `suppress_output()` context
   manager that discards output, both built on
   `contextlib.redirect_stdout`/`redirect_stderr`. Include LCATS's
   `suppress_file_descriptors` option (a real `os.dup2` redirect,
   restored in `finally`) for child-process/subprocess output that
   `redirect_stdout` alone cannot catch, since LRH's tests spawn real
   `git` subprocesses.
2. Add a `STYLE.md` policy statement in the "Testing Principles" section
   (`STYLE.md:344-356`): prints are fine, especially for real debugging;
   a test that invokes CLI/library code in-process must suppress or
   capture its output locally via the new helper; `scripts/test` must
   never gain a global suppression mechanism.
3. Migrate the 12 files currently using the ad hoc
   `io.StringIO()`+`contextlib.redirect_stdout`/`redirect_stderr`
   pattern (found via `grep -rln "redirect_stdout" tests --include="*_test.py"`
   at audit time, e.g. `tests/cli_tests/main_test.py`) to the new
   helper.
4. Apply the helper to the confirmed noisy files: `tests/cli_tests/pii_test.py`,
   `tests/cli_tests/secrets_test.py`, `tests/dev_tests/release_smoke_test.py`.
   Then re-run the audit grep (`grep -rl` for test files importing a
   `print()`-containing `src/lrh` module — roughly 30 of 116 files at
   audit time) against current `main` to enumerate the full remaining
   set, since it will have shifted since this work item was filed, and
   apply the helper to whichever of those genuinely leak output when
   `scripts/test` is run (import alone does not guarantee a leak; verify
   each file empirically before editing it).
5. Extend `src/lrh/control/test_guardrails.py`'s AST walk
   (`check_test_ast`, `src/lrh/control/test_guardrails.py:27-102`) with a
   new check: a test method containing a call to a known in-process
   entry point (e.g. `*.main(` on an imported CLI module, or
   `subprocess.run`/`check_call`/`call` without `capture_output`/
   `stdout=`) that is not lexically nested inside a `with` block using
   the new helper. Keep the false-positive risk in mind — a narrower,
   reliable check (e.g. flagging uncaptured `subprocess.run`/`check_call`/`call`
   calls first) is preferable to a broad heuristic that misfires; document
   the exact detection scope chosen and its known limits directly in the
   guardrail's own module docstring, following the file's existing
   docstring convention (`test_guardrails.py:1`).

## Non-Goals

- Do not add a global output-suppression mechanism to `scripts/test`
  (per `forbidden_actions`).
- Do not rewrite `src/lrh`'s own 386 `print()` call sites to `logging` —
  those are legitimate CLI-facing output, not test noise, and are out of
  scope for this item.
- Do not add `pytest` or any `pytest` fixture (`capsys`/`capfd`) —
  prohibited by existing policy (`pyproject.toml:85-86`).
- Do not restructure the test directory layout — that is the separate,
  already-filed `WI-TEST-LAYOUT-*` items' concern.
- Do not suppress genuine test failure output, tracebacks, or
  `unittest`'s own dot/F/E reporting.

## Acceptance Criteria

- A shared, unittest-compatible output-capture/suppression helper exists
  with at least a capture-for-assertion and a pure-suppress context
  manager.
- `STYLE.md`'s Testing Principles section documents the policy,
  including the explicit no-global-suppression constraint.
- `tests/cli_tests/pii_test.py`, `tests/cli_tests/secrets_test.py`, and
  `tests/dev_tests/release_smoke_test.py` no longer leak print output
  into a `scripts/test` run.
- The 12 files using the ad hoc `redirect_stdout`/`redirect_stderr`
  pattern are migrated to the shared helper.
- `test_guardrails.py` flags at least one representative unwrapped
  in-process/subprocess call in a synthetic test fixture (covered by
  `tests/guardrails_tests/test_framework_guardrails_test.py`).
- `lrh validate` reports 0 errors.
- A baseline-vs-final `scripts/test` output comparison is recorded in the
  execution record.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `python -m unittest tests.guardrails_tests.test_framework_guardrails_test -v`

## Risk Notes

- The `test_guardrails.py` extension risks false positives if the
  "known in-process entry point" detection is too broad; start with the
  narrower, more mechanical `subprocess.run`/`check_call`/`call`
  without-capture check before attempting to generalize to arbitrary
  `*.main(` calls, and be willing to scope the guardrail addition down
  (or leave it as a documented follow-up) if a reliable general check
  isn't achievable within this item.
- The noisy-file list in Required Changes is a snapshot from the audit
  session; `main` will have moved by implementation time, so the
  implementer must re-run the identifying grep rather than treat the
  named files as the complete set.
- Migrating the 12 ad hoc-pattern files is mechanical but touches many
  files; per `STYLE.md`'s PR discipline ("Small and focused... Limited to
  a single concern"), the implementer may reasonably split this into more
  than one PR (e.g. helper + policy + guardrail first, file migrations
  after) rather than one large diff.
