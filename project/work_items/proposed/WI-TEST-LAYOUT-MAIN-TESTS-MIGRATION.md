---
resolution: null
blocked_reason: null
blocked: false
id: WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION
title: Migrate remaining per-subcommand cli_tests files into cli_tests/main_tests/
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
  - delete_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - address_meta_tests_ambiguity
  - add_cli_wiring_tests
acceptance:
  - All per-subcommand test files for main.py subcommands live under tests/cli_tests/main_tests/
  - True module mirrors (argcomplete_adapter, completion_sources, github_cli, serve, serve_triage) and the integration test (version_integration) remain at tests/cli_tests/
  - tests/cli_tests/main_test.py remains at tests/cli_tests/ (whole-CLI wiring)
  - No orphaned files remain at the old paths
  - scripts/test passes with 0 failures
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - tests/cli_tests/main_tests/conversation_test.py
  - tests/cli_tests/main_tests/design_test.py
  - tests/cli_tests/main_tests/match_test.py
  - tests/cli_tests/main_tests/project_doctor_test.py
  - tests/cli_tests/main_tests/project_init_test.py
  - tests/cli_tests/main_tests/prompt_test.py
  - tests/cli_tests/main_tests/request_test.py
  - tests/cli_tests/main_tests/search_test.py
  - tests/cli_tests/main_tests/setup_test.py
  - tests/cli_tests/main_tests/snapshot_test.py
  - tests/cli_tests/main_tests/work_items_test.py
---

## Summary

Migrate all remaining per-subcommand test files for `src/lrh/cli/main.py`
subcommands from `tests/cli_tests/` into `tests/cli_tests/main_tests/`,
completing the layout reorganization begun in
`WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION`.

## Dependencies / Order

This work item must be implemented after `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION`
lands and merges. That WI establishes the `<mod>_tests/` convention in STYLE.md,
creates `tests/cli_tests/main_tests/__init__.py`, and migrates `survey_test.py` as
the proof-of-concept. The `depends_on` field will be populated once that WI is
resolved.

## Problem / Context

After `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION` lands, the new
`<mod>_tests/` convention is established and `survey_test.py` is the
proof-of-concept. However, eleven more per-subcommand test files remain at
`tests/cli_tests/` as peers of true module mirrors. Their placement is
inconsistent with the new rule and creates ambiguity for contributors adding
future subcommand tests. This WI completes the migration, leaving
`tests/cli_tests/` containing only true module mirrors and the whole-CLI
wiring file `main_test.py`.

## Scope

- Move the eleven per-subcommand test files into `tests/cli_tests/main_tests/`
- Leave true module mirrors and `main_test.py` in place at `tests/cli_tests/`
- Verify the full test suite still passes after all moves

## Required Changes

Move the following files from `tests/cli_tests/` to
`tests/cli_tests/main_tests/`:

1. `conversation_test.py`
2. `design_test.py`
3. `match_test.py`
4. `project_doctor_test.py`
5. `project_init_test.py`
6. `prompt_test.py`
7. `request_test.py`
8. `search_test.py`
9. `setup_test.py`
10. `snapshot_test.py`
11. `work_items_test.py`

For each moved file, update any `Path(__file__).resolve().parents[N]` repo-root
expressions: files currently at depth `tests/cli_tests/` use `parents[2]` to
reach the repo root; after moving one level deeper to
`tests/cli_tests/main_tests/`, these must be updated to `parents[3]`. Check
every moved file for this pattern before committing. No other logic changes
are permitted.

Files that stay at `tests/cli_tests/` (true module mirrors or whole-CLI):

- `main_test.py` — whole-CLI wiring tests
- `argcomplete_adapter_test.py` → mirrors `src/lrh/cli/argcomplete_adapter.py`
- `completion_sources_test.py` → mirrors `src/lrh/cli/completion_sources.py`
- `github_cli_test.py` → mirrors `src/lrh/cli/github.py`
- `serve_test.py` → mirrors `src/lrh/serve.py`
- `serve_triage_test.py` → mirrors `src/lrh/serve_triage.py`
- `version_integration_test.py` → integration test (broader than one module)

## Non-Goals

- Do not address the `meta_tests/` directory ambiguity — that is
  `WI-META-TESTS-LAYOUT-AUDIT`.
- Do not modify test logic beyond updating `parents[N]` repo-root path expressions necessitated by the directory move.
- Do not create new tests for any subcommand.
- Do not add CLI wiring tests for subcommands lacking them — that is
  `WI-CLI-WIRING-TESTS-VALIDATE-GITHUB-WORKSTREAMS`.

## Acceptance Criteria

- All eleven per-subcommand files listed in Required Changes exist under
  `tests/cli_tests/main_tests/` and no longer exist at `tests/cli_tests/`.
- True module mirror files and `main_test.py` remain at `tests/cli_tests/`.
- `scripts/test` passes with 0 failures.
- `lrh validate` passes with 0 errors.

## Validation

- `lrh validate`
- `scripts/test`
- `scripts/lint`

## Risk Notes

- **Path-depth breakage:** Several files compute the repo root via
  `Path(__file__).resolve().parents[2]`. At the current depth
  (`tests/cli_tests/`), `parents[2]` is the repo root. After the move to
  `tests/cli_tests/main_tests/`, `parents[2]` resolves to `tests/`, breaking
  subprocess cwd and project-root arguments. Every moved file must be audited
  for this pattern and updated to `parents[3]` before `scripts/test` will
  pass. Known affected files: `conversation_test.py`, `match_test.py`,
  `project_doctor_test.py`, `project_init_test.py`, `prompt_test.py`,
  `search_test.py`, `setup_test.py`, `snapshot_test.py`.
- `unittest` discovery (`scripts/test`) recurses into subdirectories by
  default; the `__init__.py` from `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION`
  should be sufficient, but verify after the move.
- Moving eleven files in one PR is the minimum necessary to reach a
  consistent state; splitting further would leave `tests/cli_tests/` in a
  partially-migrated state that contradicts the new rule.
