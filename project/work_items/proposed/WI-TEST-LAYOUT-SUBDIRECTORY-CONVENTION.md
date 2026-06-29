---
resolution: null
blocked_reason: null
blocked: false
id: WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION
title: Extend STYLE.md test layout rule and migrate survey_test.py to main_tests/
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
  - migrate_remaining_per_subcommand_files
acceptance:
  - STYLE.md §"Test Tree Layout" documents the <mod>_tests/ subdirectory convention
  - tests/cli_tests/main_tests/__init__.py exists
  - tests/cli_tests/main_tests/survey_test.py exists with identical content to the former tests/cli_tests/survey_test.py
  - tests/cli_tests/survey_test.py no longer exists
  - scripts/test passes with 0 failures
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - STYLE.md
  - tests/cli_tests/main_tests/__init__.py
  - tests/cli_tests/main_tests/survey_test.py
---

## Summary

Extend the STYLE.md §"Test Tree Layout" rule with a `<mod>_tests/`
subdirectory convention for source modules hosting multiple distinct features,
and migrate `tests/cli_tests/survey_test.py` to
`tests/cli_tests/main_tests/survey_test.py` as the proof-of-concept.

## Problem / Context

The current STYLE.md flat-mirror rule (`src/lrh/<pkg>/<mod>.py` →
`tests/<pkg>_tests/<mod>_test.py`) breaks down when a single module hosts
many distinct features. `src/lrh/cli/main.py` registers ~20 subcommands;
per-feature test files have been placed at `tests/cli_tests/survey_test.py`,
`tests/cli_tests/conversation_test.py`, etc. — peer to module mirrors, not
inside a module-scoped directory. The STYLE.md rule gives no guidance for
this case, leaving contributors uncertain whether to follow the flat rule or
the organic per-feature placement. This WI establishes the canonical answer
as the first step of a two-part layout migration (see
`WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION` for the remainder).

## Scope

- Amend STYLE.md §"Test Tree Layout" with the `<mod>_tests/` extension rule
- Create `tests/cli_tests/main_tests/__init__.py`
- Move `tests/cli_tests/survey_test.py` → `tests/cli_tests/main_tests/survey_test.py`
- Verify the full test suite still passes after the move

## Required Changes

1. Edit `STYLE.md` §"Test Tree Layout": add a paragraph and example block
   documenting the `<mod>_tests/` convention. The rule: when
   `src/lrh/<pkg>/<mod>.py` contains multiple distinct features each
   warranting its own test file, per-feature tests live in
   `tests/<pkg>_tests/<mod>_tests/<feature>_test.py`. The root
   `<mod>_test.py` should still exist for whole-module wiring tests. The
   `<mod>_tests/` directory must contain an `__init__.py`.

2. Create `tests/cli_tests/main_tests/__init__.py` (empty).

3. Move `tests/cli_tests/survey_test.py` to
   `tests/cli_tests/main_tests/survey_test.py`. No content changes — this
   is a pure relocation. Update any import paths if affected.

## Non-Goals

- Do not migrate any other per-subcommand files from `tests/cli_tests/` into
  `main_tests/` — that is `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION`.
- Do not address the `meta_tests/` directory ambiguity — that is
  `WI-META-TESTS-LAYOUT-AUDIT`.
- Do not add or modify any test logic.
- Do not create new tests for any subcommand.

## Acceptance Criteria

- `STYLE.md` §"Test Tree Layout" documents the `<mod>_tests/` subdirectory
  convention with a concrete example (`main_tests/survey_test.py`).
- `tests/cli_tests/main_tests/__init__.py` exists.
- `tests/cli_tests/main_tests/survey_test.py` exists with content identical
  to the former `tests/cli_tests/survey_test.py`.
- `tests/cli_tests/survey_test.py` no longer exists.
- `scripts/test` passes with 0 failures.
- `lrh validate` passes with 0 errors.

## Validation

- `lrh validate`
- `scripts/test`
- `scripts/lint`

## Risk Notes

- `unittest` discovery (`python -m unittest discover -s tests -p '*_test.py'`,
  as used by `scripts/test`) recurses into subdirectories by default, so the
  new `tests/cli_tests/main_tests/` directory should be discovered automatically.
  Verify after the move that `scripts/test` still finds and runs the relocated file.
- The `__init__.py` is required for consistency with all other test
  subdirectories; omitting it causes `unittest` to fail to import test modules
  that use package-relative imports.
