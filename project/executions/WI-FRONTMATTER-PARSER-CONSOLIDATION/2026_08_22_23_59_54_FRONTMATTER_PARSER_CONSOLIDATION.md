---
execution_id: 2026_08_22_23_59_54_FRONTMATTER_PARSER_CONSOLIDATION
prompt_id: PROMPT(WI-FRONTMATTER-PARSER-CONSOLIDATION:FRONTMATTER_PARSER_CONSOLIDATION)[2026-08-22T23:58:33+00:00]
work_item: WI-FRONTMATTER-PARSER-CONSOLIDATION
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/614
commit: 2f7f228eab72e0fb6624f23d3b6edc1ba0a1913f
created_at: 2026-08-22T23:59:54+00:00
agent: claude_app
instruction_source: 'chat (user ran /lrh-execute WI-FRONTMATTER-PARSER-CONSOLIDATION to implement and land the work item end-to-end)'
session_transcript: claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8
---

# Summary

Implemented `WI-FRONTMATTER-PARSER-CONSOLIDATION`: consolidated
`control/parser.py` and `control/validator.py` onto one shared
`yaml.safe_load`-based `parse_frontmatter_mapping()`, added the
non-string list-item schema check, patched the 3 raw-`created_at`
consumers, and fixed the 31 real `project/` files with a colon-collapse
or hard-syntax-error field, using the old lenient parser's reading as
ground truth (Decision 4).

# Result

- `src/lrh/control/parser.py`: `_parse_frontmatter_mapping` replaced with
  `parse_frontmatter_mapping()` built on `yaml.safe_load`.
- `src/lrh/control/validator.py`: `_parse_simple_yaml` deleted; calls the
  shared parser instead; added `_check_list_field_items_are_strings()`,
  wired into `WORK_ITEM_LIST_FIELDS`, `WORKSTREAM_LIST_FIELDS`, and
  `DESIGN_PROPOSAL_LIST_FIELDS`.
- `src/lrh/prompt_workflow_records.py` and
  `src/lrh/prompt_workflow_search.py`: added explicit
  `datetime.date`/`datetime.datetime` handling via `.isoformat()`.
  `prompt_workflow_slug.py` needed no direct change -- its only
  `created_at` consumption already flows through the patched helper.
- 31 files under `project/` fixed (colon-collapsed list items or
  backtick-leading plain scalars).
- New test coverage in `tests/control_tests/parser_test.py` and
  `tests/control_tests/validator_test.py` for the datetime,
  colon-collapse, and hard-syntax-error cases; updated
  `test_colon_near_misses_warn_malformed` to reflect that two of its
  four previously-silently-accepted inputs are genuine YAML syntax
  errors under real YAML.

# Validation

- `lrh validate`: 0 errors, 0 warnings on the full `project/` tree.
- `scripts/format --check --diff`: clean.
- `scripts/lint`: clean.
- `scripts/test`: 1295 tests, all pass.
- `tests/control_tests/loader_test.py::test_load_project_from_repo_root`:
  passes.

# Follow-up

- The migration tool (`lrh project doctor --fix-frontmatter`) and the
  `lrh validate` lint guard are deferred to
  `WI-FRONTMATTER-MIGRATION-LINT-GUARD`, per this WI's Non-Goals.
