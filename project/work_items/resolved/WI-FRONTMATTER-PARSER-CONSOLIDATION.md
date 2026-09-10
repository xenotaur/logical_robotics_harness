---
resolution: 'Implemented and merged in PR #614 (commit 2f7f228e)'
blocked_reason: null
blocked: false
id: WI-FRONTMATTER-PARSER-CONSOLIDATION
title: Consolidate LRH frontmatter parsers onto PyYAML
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-FRONTMATTER-PARSER
related_design:
  - project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_migration_tool
acceptance:
  - src/lrh/control/parser.py and src/lrh/control/validator.py share one yaml.safe_load-based parse_frontmatter_mapping() function
  - validator.py no longer defines _parse_simple_yaml
  - _check_list_field_items_are_strings() is added to the WORK_ITEM_LIST_FIELDS, WORKSTREAM_LIST_FIELDS, and DESIGN_PROPOSAL_LIST_FIELDS schema checks
  - prompt_workflow_records.py, prompt_workflow_slug.py, and prompt_workflow_search.py handle datetime.date/datetime.datetime values explicitly via .isoformat() instead of falling through to str()/dropping them
  - Every file in project/ with a colon-collapse list item or a hard-syntax-error scalar (re-locate at implementation time via the old-parser-vs-yaml.safe_load diff technique -- 27 files at the original 2026-08 audit, already 30 at re-verification before filing this WI, and growing as new content lands) is fixed so it parses correctly under real YAML
  - tests/control_tests/loader_test.py::test_load_project_from_repo_root (loads the real project/ tree) passes
  - lrh validate reports 0 errors on the full project/ tree after the change
required_evidence:
  - lrh_validate
  - test_output
  - manual_review
artifacts_expected:
  - src/lrh/control/parser.py
  - src/lrh/control/validator.py
  - src/lrh/prompt_workflow_records.py
  - src/lrh/prompt_workflow_slug.py
  - src/lrh/prompt_workflow_search.py
  - tests/control_tests/parser_test.py
  - tests/control_tests/validator_test.py
---

## Summary

Replace LRH's two independently hand-rolled frontmatter parsers
(`control/parser.py`'s `_parse_frontmatter_mapping`, `control/validator.py`'s
`_parse_simple_yaml`) with one shared `yaml.safe_load`-based parser, and fix
the real project content that isn't yet compatible with real YAML's
plain-scalar grammar.

## Problem / Context

`PROP-LRH-FRONTMATTER-PARSER` (adopted via PR #531) documents why LRH's two
hand-rolled parsers disagree on what valid frontmatter is (see its
Background/Motivation and Design Decisions 1-3), and why a naive swap to
`yaml.safe_load` would silently mishandle real existing content in three
distinct ways it identifies and fixes for. This work item is Decision 1-3's
implementation slice — steps 1-3 of the proposal's Implementation Plan.

**Independent narrow fix already landed, does not substitute for this WI.**
Commit `2e1af28d` (2026-08-20, a separate session) patched
`_parse_frontmatter_mapping`'s block-list scanner to skip `#`-prefixed lines,
fixing the specific "comment interleaved in a list" crash the original bug
report described. That fix is real and correct but narrow: it patches the
existing hand-rolled `parser.py` in place rather than consolidating onto a
standard parser, leaves `validator.py`'s separate `_parse_simple_yaml`
untouched (the parser/validator disagreement itself is not fixed), and does
not address any of the other three landmine classes `PROP-LRH-FRONTMATTER-
PARSER` documents (colon-collapse into a one-entry mapping, hard syntax
errors on backtick/multi-colon scalars, silent mid-scalar truncation at
`" #"`). This WI's scope is unaffected by that patch and remains necessary.

### Duplication search
- In-repo: Related — commit `2e1af28d` (above) is a narrower, already-landed
  fix for the same originating bug report, superseded in scope (not
  duplicated) by this WI and the governing proposal.
- Sibling repos: None identified.
- External libraries: PyYAML (already the proposal's Decision 1 choice; no
  new evaluation needed here).
- Recommendation: Proceed.

### Demand search
- Work items: None found beyond the two already-superseded ancestors
  (`WI-VALIDATOR-YAML-PARSER`, `WI-PARSER-HARDENING`), both closed in
  PR #531 and PR #569.
- Proposals: `PROP-LRH-FRONTMATTER-PARSER` (adopted) — this WI is its
  implementation, not a duplicate.
- Backlog: No matching entries.
- Recommendation: No further action.

## Scope

- Replace `control/parser.py`'s and `control/validator.py`'s frontmatter
  parsing with one shared `yaml.safe_load`-based function.
- Add the non-string list-item schema check across all three planning-node
  types.
- Patch the 3 identified downstream consumers of raw `created_at` values.
- Fix the files already found incompatible with real YAML (count drifts as
  content lands; re-locate at implementation time, do not rely on a cached
  number).

## Required Changes

1. In `src/lrh/control/parser.py`, replace `_parse_frontmatter_mapping` with
   a `parse_frontmatter_mapping()` function built on `yaml.safe_load`,
   wrapping `yaml.YAMLError` as `ValueError` and rejecting a non-dict top
   level, per `PROP-LRH-FRONTMATTER-PARSER` Decision 1.
2. In `src/lrh/control/validator.py`, delete `_parse_simple_yaml` and its
   call site; import and call `parser.parse_frontmatter_mapping()` instead.
3. Add a shared `_check_list_field_items_are_strings()` helper to
   `validator.py`, wired into the `WORK_ITEM_LIST_FIELDS`,
   `WORKSTREAM_LIST_FIELDS`, and `DESIGN_PROPOSAL_LIST_FIELDS` schema checks,
   per Decision 3.
4. In `src/lrh/prompt_workflow_records.py`, `src/lrh/prompt_workflow_slug.py`,
   and `src/lrh/prompt_workflow_search.py`, add an
   `isinstance(value, (datetime.date, datetime.datetime))` branch calling
   `.isoformat()` in each function that currently falls through to
   `str(value)` or drops non-`str` values, per Decision 2.
5. Fix the affected files (unquoted `key: value`-shaped list items, or
   backtick-leading/multi-colon plain scalars — 27 files at the original
   2026-08 audit, already 30 at re-verification just before filing this WI)
   by quoting or block-scalar-encoding the affected values — re-locate the
   current instances with the same old-parser-vs-`yaml.safe_load` diff
   technique described in the proposal's Background section, since real
   project content changes continuously and any cached count or file list
   will be stale by implementation time.
6. Update/replace `tests/control_tests/parser_test.py` and
   `tests/control_tests/validator_test.py` for the new shared parser,
   including the comment-in-list regression tests already added by commit
   `2e1af28d` (verify they still pass under the new implementation) and new
   coverage for the datetime, colon-collapse, and syntax-error cases.

## Non-Goals

- Does not build the migration tool (`lrh project doctor --fix-frontmatter`)
  or the `lrh validate` lint guard — see `WI-FRONTMATTER-MIGRATION-LINT-GUARD`.
- Does not update frontmatter-authoring skill guidance — also deferred to
  `WI-FRONTMATTER-MIGRATION-LINT-GUARD`.
- Does not touch `conversations/frontmatter.py` (the deterministic writer) —
  out of scope per the proposal's own Non-Goals.

## Acceptance Criteria

- `src/lrh/control/parser.py` and `src/lrh/control/validator.py` share one
  `yaml.safe_load`-based parser; `_parse_simple_yaml` no longer exists.
- `lrh validate` and `lrh work-items validate` agree on well-formed
  frontmatter for the same file.
- The 3 datetime consumers handle `datetime`/`date` values explicitly, with
  tests covering the `.isoformat()` path.
- Every file with a colon-collapse list item or hard-syntax-error scalar
  (re-locate at implementation time; do not rely on a cached count) parses
  correctly; `lrh validate` reports 0 errors on the full `project/` tree.
- `tests/control_tests/loader_test.py::test_load_project_from_repo_root`
  (the real-project-tree regression guard) passes.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-FRONTMATTER-PARSER.md`
- Design: `project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md`
