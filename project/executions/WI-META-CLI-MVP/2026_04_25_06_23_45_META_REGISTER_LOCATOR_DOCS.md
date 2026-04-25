---
execution_id: 2026_04_25_06_23_45_META_REGISTER_LOCATOR_DOCS
prompt_id: PROMPT(WI-META-CLI-MVP:META_REGISTER_LOCATOR_DOCS)[2026-04-24T22:37:00-04:00]
work_item: WI-META-CLI-MVP
status: landed
rerun_of: 
pr: 
commit: 891dd0488236890572c2bbd16a50e64ee1ef4609
created_at: 2026-04-25T06:23:45+00:00
---

# Summary

Document locator semantics for `lrh meta register` and related `meta` surfaces so
`repo_locator` is clearly treated as a repository/ref locator and `project_dir`
as a path relative to that locator.

# Result

- Updated top-level `README.md` meta CLI notes with explicit locator-model wording.
- Added a concrete GitHub tree URL example and normalized-record explanation:
  `.../tree/master/project` registers as `repo_locator: .../tree/master` and
  `project_dir: project`.
- Clarified truth-first setup-state wording so remote locators remain
  `not_checked` unless remote probing is explicitly implemented.
- Updated CLI help text for `lrh meta register`, `lrh meta list`, and
  `lrh meta inspect` to align with the same locator semantics and setup-state
  language.
- Added a CLI unit test that verifies register help includes the locator
  semantics and GitHub tree example.

# Validation

- `pytest -q tests/cli_tests/main_test.py` (pass)
- `scripts/test` (pass)
- `scripts/lint` (ruff pass; black check failed due unrelated pre-existing
  formatting issue in `tests/control_tests/parser_test.py`)
- `scripts/format --check` (failed due unrelated pre-existing formatting issue
  in `tests/control_tests/parser_test.py`)
- `python -m black --check src/lrh/cli/main.py tests/cli_tests/main_test.py`
  (pass)

# Follow-up

- Live remote probing remains intentionally deferred; this prompt only documents
  current truth-first semantics (`not_checked` for remote locators).
