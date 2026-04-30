---
execution_id: 2026_04_30_23_54_49_ADD_INSTALLED_CLI_SMOKE_TESTS_REVIEW_FIXES
prompt_id: PROMPT(WI-INSTALLED-PROMPT-WORKFLOW:ADD_INSTALLED_CLI_SMOKE_TESTS)[2026-04-29T22:07:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_04_30_23_45_03_ADD_INSTALLED_CLI_SMOKE_TESTS
pr: 
commit: 
created_at: 2026-04-30T23:54:49+00:00
---

# Summary

Addressed PR review feedback for installed prompt CLI smoke coverage.

Work item `WI-INSTALLED-PROMPT-WORKFLOW` was not present under `project/work_items/`, so this execution was recorded under `AD_HOC` per prompt instructions.

# Result

Updated `tests/smoke/prompt_cli_install_smoke.py` to:

- rename timeout constant from `_PIP_COMMAND_TIMEOUT_SECONDS` to `_COMMAND_TIMEOUT_SECONDS`
- build a wheel (`pip wheel`) from the checkout and install that wheel into the temp venv before command assertions
- keep non-interactive pip flags and dependency-free install/build paths for deterministic smoke behavior

Updated `scripts/README.md` wording to use `--slug example` instead of placeholder text that could be read as literal input.

# Validation

- `python -m unittest tests.smoke.prompt_cli_install_smoke` (passed with skip in this environment due to unavailable install/build dependencies)

# Follow-up

- If desired, run `scripts/smoke` in an environment with available wheel-build dependencies to exercise this test without skip.
