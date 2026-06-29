---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLI-WIRING-TESTS-VALIDATE-GITHUB-WORKSTREAMS
title: Add CLI-level wiring tests for lrh validate, lrh github, and lrh workstreams organize
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
  - edit_file
  - create_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_library_code
acceptance:
  - tests/cli_tests/main_tests/validate_test.py exists with tests covering exit-code 0/1 and --work-items / --project-dir argument parsing
  - tests/cli_tests/main_tests/github_test.py exists with at least one test routing through main.py (not importing lrh.cli.github directly)
  - tests/cli_tests/main_tests/workstreams_test.py exists with tests covering --dry-run default behavior and missing-subcommand error
  - scripts/test passes with 0 failures
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - tests/cli_tests/main_tests/validate_test.py
  - tests/cli_tests/main_tests/github_test.py
  - tests/cli_tests/main_tests/workstreams_test.py
---

## Summary

Add CLI-level wiring tests for `lrh validate`, `lrh github`, and
`lrh workstreams organize` — three subcommands whose `main.py` dispatch
paths are currently exercised only by library-level tests or not at all.

## Problem / Context

A survey conducted during the test-layout design session found three
subcommands with no test that routes through `src/lrh/cli/main.py`:

- **`lrh validate`** (dispatches `validate_project()` from `src/lrh/cli/main.py`):
  parses `--project-dir` and `--work-items`, calls `validate_project()`,
  formats the report, and exits with code 0 or 1.
  `control_tests/validator_test.py` tests `validate_project()` directly but
  the CLI wiring layer is untested.

- **`lrh github`** (dispatches to `github_cli.run_github_cli()` from
  `src/lrh/cli/main.py`): `cli_tests/github_cli_test.py` imports
  `lrh.cli.github` directly and never routes through `main.py`.

- **`lrh workstreams organize`** (dispatches to `workstreams_organize.*` from
  `src/lrh/cli/main.py`): parses `--dry-run`, `--apply`, `--project-dir` args
  and dispatches to `workstreams_organize.*`.
  `workstreams_tests/organize_test.py` tests the library directly.

This is the same class of gap fixed for `lrh setup` in PR #346. Tests that
bypass `main.py` do not verify argument parsing, exit-code contracts, or
dispatch correctness in the wiring layer.

## Scope

- Add wiring-layer tests for `lrh validate`, `lrh github`, and
  `lrh workstreams organize` at `tests/cli_tests/main_tests/`
- Tests should route through `cli_main.main()` (in-process with mocked argv)
  or `subprocess.run([sys.executable, "-m", "lrh.cli.main", ...])` — not
  via direct library imports
- Minimum coverage: exercise the dispatch path, verify exit codes, and test
  at least one argument-parsing edge case per subcommand

## Required Changes

1. Create `tests/cli_tests/main_tests/validate_test.py`:
   - Test that `lrh validate` exits 0 on a valid project and 1 on a project
     with validation errors.
   - Test that `--work-items` flag is accepted and restricts validation scope.
   - Test that `--project-dir` flag is accepted and points to the right directory.

2. Create `tests/cli_tests/main_tests/github_test.py`:
   - Add at least one test routing through `cli_main.main()` with
     `sys.argv = ["lrh", "github", ...]`.
   - The test may mock `github_cli.run_github_cli` to avoid network calls;
     the goal is to verify the dispatch path in `main.py`, not re-test
     `github_cli` behavior already covered in `github_cli_test.py`.

3. Create `tests/cli_tests/main_tests/workstreams_test.py`:
   - Test that `lrh workstreams organize --dry-run` exits 0 and prints a
     plan report.
   - Test that `lrh workstreams organize` without `--apply` defaults to
     dry-run (no file mutations).
   - Test that missing subcommand prints an error and exits non-zero.

Note: if `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION` has not yet landed,
create `tests/cli_tests/main_tests/__init__.py` as part of this WI; if it
has landed, that file already exists.

## Non-Goals

- Do not modify `github_cli_test.py`, `workstreams_tests/organize_test.py`,
  or `control_tests/validator_test.py` — those library-level tests remain
  valid and complementary.
- Do not add exhaustive coverage for every argument; the goal is to close the
  wiring gap, not replace the library tests.
- Do not address `meta_tests/` — that is `WI-META-TESTS-LAYOUT-AUDIT`.
- Do not perform the test-layout file moves — those are handled by
  `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION` and
  `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION`.

## Acceptance Criteria

- `tests/cli_tests/main_tests/validate_test.py` exists with tests covering
  exit-code 0/1 and `--work-items` / `--project-dir` argument parsing.
- `tests/cli_tests/main_tests/github_test.py` exists with at least one test
  routing through `main.py` (not directly importing `lrh.cli.github`).
- `tests/cli_tests/main_tests/workstreams_test.py` exists with tests covering
  `--dry-run` default behavior and missing-subcommand error.
- `scripts/test` passes with 0 failures.
- `lrh validate` passes with 0 errors.

## Validation

- `lrh validate`
- `scripts/test`
- `scripts/lint`

## Risk Notes

- `lrh validate` tests require a temporary project directory fixture; use
  `tempfile.TemporaryDirectory` with a minimal `project/` scaffold, similar
  to the pattern in `tests/cli_tests/work_items_test.py`.
- `lrh github` makes network calls; mock `github_cli.run_github_cli` at the
  boundary to keep tests hermetic.
- `lrh workstreams organize` reads `project/workstreams/`; use a temp
  directory with a minimal workstream fixture.
