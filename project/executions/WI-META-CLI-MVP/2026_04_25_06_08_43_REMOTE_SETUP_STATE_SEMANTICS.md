---
execution_id: 2026_04_25_06_08_43_REMOTE_SETUP_STATE_SEMANTICS
prompt_id: PROMPT(WI-META-CLI-MVP:REMOTE_SETUP_STATE_SEMANTICS)[2026-04-24T22:36:00-04:00]
work_item: WI-META-CLI-MVP
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-04-25T06:08:43+00:00
---

# Summary

Clarify remote `setup_state` semantics for Meta CLI records so unchecked remote
URL locators no longer report `not_set_up` (which implies a local existence
check that LRH did not perform).

# Result

Updated setup-state detection in `src/lrh/meta/workspace.py` to return
`not_checked` for non-local locators while preserving existing local-path
behavior (`lrh_project_present`/`not_set_up`) based on actual filesystem checks.
Added focused tests in `tests/meta_tests/register_test.py` and
`tests/meta_tests/inspect_test.py` to lock semantics for a normalized GitHub
record (`https://github.com/xenotaur/taurworks/tree/master` + `project`) and to
keep `lrh meta inspect` derived path fields truth-first (`<not_applicable>`) for
remote locators. Updated root `README.md` to document the new semantics.

# Validation

- `python -m unittest tests.meta_tests.register_test tests.meta_tests.inspect_test` (pass)
- `scripts/test` (pass)
- `scripts/lint` (fails due to repo-wide Black check)
- `scripts/format --check` (fails because repository currently has a pre-existing
  Black issue in `tests/control_tests/parser_test.py`; no unrelated formatting
  changes were kept in this prompt run)

# Follow-up

- Intentionally deferred by prompt: live remote setup probing (GitHub/API/network
  checks) for remote URL locators.
- Intentionally deferred by prompt: migration/repair logic for existing records
  with misleading historical setup-state values.
