---
execution_id: 2026_05_03_16_22_19_TOOL_VERSION_CONTRACT
prompt_id: PROMPT(WI-DEV-TOOLCHAIN-RECONCILIATION:TOOL_VERSION_CONTRACT)[2026-05-03T11:10:00-04:00]
work_item: WI-DEV-TOOLCHAIN-RECONCILIATION
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-05-03T16:22:19+00:00
---

# Summary

Added a reproducible Black/Ruff version contract by introducing a root constraints file,
adding tool-level required-version enforcement in `pyproject.toml`, and updating maintainer/CI
docs and setup/install commands to use constrained dev installs.

# Result

- Added `constraints-dev.txt` with `black==26.3.1` and `ruff==0.15.12`.
- Added Black and Ruff required-version settings in `pyproject.toml`.
- Updated `scripts/develop`, root `README.md`, `scripts/README.md`, and GitHub Actions install
  steps to use `python -m pip install -e ".[dev]" -c constraints-dev.txt`.
- Version choices were aligned to the prompt-specified CI expectation (`black 26.3.1`,
  `ruff 0.15.12`) because workflow files did not previously pin versions.

# Validation

Ran:
- `python -m pip install --upgrade pip`
- `python -m pip install -e ".[dev]" -c constraints-dev.txt` (failed in this environment due to
  blocked index/network access; see command output in PR evidence)
- `scripts/version tools`
- `scripts/format --check --diff` (failed intentionally due to required-version mismatch,
  demonstrating enforcement in current environment)
- `scripts/lint` (failed intentionally due to required-version mismatch,
  demonstrating enforcement in current environment)
- `scripts/test` (passed)

# Follow-up

- Ensure CI runner/tool cache can install `black==26.3.1` and `ruff==0.15.12` from package index.
- Optionally expand constraints coverage beyond Black/Ruff for broader environment reproducibility.
- Optionally add a lightweight CI assertion that install commands always include
  `-c constraints-dev.txt`.
