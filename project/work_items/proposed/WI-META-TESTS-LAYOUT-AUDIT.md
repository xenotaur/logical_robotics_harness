---
resolution: null
blocked_reason: null
blocked: false
id: WI-META-TESTS-LAYOUT-AUDIT
title: Audit meta_tests/ layout ambiguity and produce a reorganization plan
type: investigation
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
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - move_any_files
  - edit_style_md
acceptance:
  - Audit report identifies every file in tests/meta_tests/ and classifies it as true module mirror, CLI-dispatch test, or integration test
  - Report assesses whether the current placement creates real confusion or gaps
  - "Report recommends one of: leave as-is, split into meta_tests/ (module mirrors) + cli_tests/main_tests/meta_tests/ (CLI dispatch), or another approach"
  - Report is captured as a design artifact or work item comment with a concrete follow-on action
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/design/audits/meta-tests-layout-audit.md
---

## Summary

Audit the `tests/meta_tests/` directory to resolve its dual-purpose
ambiguity — it simultaneously mirrors `src/lrh/meta/` and houses CLI-dispatch
tests for `lrh meta <subcmd>` — and produce a concrete reorganization plan or
a documented decision to leave it as-is.

## Problem / Context

The `tests/meta_tests/` directory serves two distinct purposes that the
STYLE.md rules do not account for: (1) it is a true module mirror for
`src/lrh/meta/` (containing `workspace_test.py` and `local_state_model_test.py`),
and (2) it houses tests for the `lrh meta` subcommand group (`init_test.py`,
`list_test.py`, `register_test.py`, `inspect_test.py`, `set_unset_test.py`,
`where_test.py`, `config_test.py`).

This ambiguity was surfaced during the test-layout design session that
produced `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION` and
`WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION`. A post-design survey found that most
`meta` subcommand tests route through `subprocess.run([sys.executable, "-m",
"lrh.cli.main", *args])`, but `config_test.py` was subsequently found to
import `lrh.meta` library modules directly with no subprocess or `cli_main`
call — meaning `lrh meta config` CLI dispatch may be untested at the wiring
layer. The audit must determine whether this is a real gap and, if so, flag
it for `WI-CLI-WIRING-TESTS-VALIDATE-GITHUB-WORKSTREAMS` or a new WI.

This investigation should be executed after both migration WIs land so the
auditor can evaluate the post-migration state of `tests/cli_tests/` and
`tests/cli_tests/main_tests/` as context.

## Scope

- Classify every file in `tests/meta_tests/` as: true module mirror, CLI-dispatch test, or integration test
- For each CLI-dispatch test file, confirm whether it routes through `cli_main.main()` or `subprocess.run([..., "lrh.cli.main", ...])` or tests the library directly
- Explicitly assess whether `lrh meta config` CLI wiring is tested at the dispatch layer
- Assess whether the dual-purpose placement causes real confusion, maintenance risk, or convention violations
- Evaluate the proposed split: true mirrors stay in `tests/meta_tests/`; CLI-dispatch tests move to `tests/cli_tests/main_tests/meta_tests/`
- Produce a written recommendation: reorganize (with a follow-on operation WI) or leave as-is (with documented rationale)

## Required Changes

1. Read and classify all files in `tests/meta_tests/` against the post-migration
   STYLE.md rule.

2. Write an audit report to
   `project/design/audits/meta-tests-layout-audit.md` containing:
   - Classification table (file → category)
   - Assessment of real vs. cosmetic ambiguity
   - Recommendation (reorganize or leave as-is)
   - If reorganize: a concrete list of files to move and a suggested follow-on WI title

3. If the recommendation is "reorganize," draft a follow-on operation WI
   in the conversation (do not write it to disk — that is a separate action
   requiring user confirmation).

## Non-Goals

- Do not move any files in this investigation.
- Do not amend STYLE.md — amendments are handled by the convention WIs.
- Do not add or modify test logic.

## Acceptance Criteria

- `project/design/audits/meta-tests-layout-audit.md` exists with a classification
  table, assessment, and concrete recommendation.
- No files in `tests/meta_tests/` or `tests/cli_tests/` have been moved.
- `lrh validate` passes with 0 errors.

## Validation

- `lrh validate`

## Dependencies / Order

This investigation should be executed after `WI-TEST-LAYOUT-SUBDIRECTORY-CONVENTION`
and `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION` both land, so the auditor can
evaluate `tests/meta_tests/` in the context of the completed post-migration
`tests/cli_tests/main_tests/` layout. The `depends_on` fields will be
populated once those WIs are resolved.

## Risk Notes

- If the audit recommends reorganization, the follow-on operation WI will
  touch ~9 files in `tests/meta_tests/`. This is a low-risk pure relocation,
  but it will require verifying that the `lrh meta` subprocess tests continue
  to pass under the new path.
- The `project/design/audits/` directory may not yet exist; create it as
  needed.
