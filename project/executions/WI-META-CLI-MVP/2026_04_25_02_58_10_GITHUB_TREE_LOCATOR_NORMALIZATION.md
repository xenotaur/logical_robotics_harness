---
execution_id: 2026_04_25_02_58_10_GITHUB_TREE_LOCATOR_NORMALIZATION
prompt_id: PROMPT(WI-META-CLI-MVP:GITHUB_TREE_LOCATOR_NORMALIZATION)[2026-04-24T22:35:00-04:00]
work_item: WI-META-CLI-MVP
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T02:58:10+00:00
---

# Summary

Normalize `lrh meta register` handling of GitHub tree URLs that include a
project subpath so stored `repo_locator` and `project_dir` are separated
deterministically (for example `.../tree/master/project` -> repo locator
`.../tree/master`, project dir `project`) without adding network probing.

# Result

Implemented a narrow runtime change in `src/lrh/meta/workspace.py` so inferred
registration metadata now includes a normalized repo locator for GitHub tree
URLs when no explicit `--project-dir` override is provided. Added focused
runtime and CLI tests in `tests/meta_tests/register_test.py` for
`taurworks/tree/master/project` and nested `widgets/tree/main/docs/project`
cases. Updated `README.md` metadata bullet to reflect normalized storage
behavior.

# Validation

- `python -m unittest tests.meta_tests.register_test` (pass)
- `scripts/test` (pass)
- `scripts/lint` (pass)
- `scripts/format --check` (fails because repository currently has a pre-existing
  Black issue in `tests/control_tests/parser_test.py`; no unrelated formatting
  changes were kept in this prompt run)

# Follow-up

- Intentionally deferred by prompt: migration/repair logic for existing records
  created with conflated GitHub tree locators.
- Intentionally deferred by prompt: remote GitHub setup probing/network checks.
