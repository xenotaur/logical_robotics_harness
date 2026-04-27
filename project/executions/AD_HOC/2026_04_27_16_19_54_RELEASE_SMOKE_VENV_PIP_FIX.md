---
execution_id: 2026_04_27_16_19_54_RELEASE_SMOKE_VENV_PIP_FIX
prompt_id: PROMPT(AD_HOC:RELEASE_SMOKE_VENV_PIP_FIX)[2026-04-27T12:20:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-27T16:19:54+00:00
---

# Summary

Fix `scripts/release-smoke` installation behavior so the smoke venv installs the exact built wheel under test and validates the installed `lrh` entry point reliably.

# Result

Updated `src/lrh/dev/release_smoke.py` to install via `<venv>/bin/python -m pip install --force-reinstall <wheel>` instead of invoking `<venv>/bin/pip` directly, added pre-install pip visibility diagnostics, and added an explicit actionable failure when `<smoke-root>/venv/bin/lrh` is missing after install. Updated unit tests in `tests/dev_tests/release_smoke_test.py` to assert the new install command shape and preserve/cleanup behavior. Updated release docs in `README.md` to clarify the `<smoke-root>/venv/...` paths and force-reinstall flow.

# Validation

- Ran `python -m unittest tests/dev_tests/release_smoke_test.py` (passes).
- Ran `scripts/test` (passes).
- Ran `scripts/format --check` (fails due pre-existing unrelated formatting in `tests/control_tests/parser_test.py`).
- Ran `scripts/lint` (ruff passes; fails black check because of the same pre-existing formatting issue).
- Ran `scripts/release-smoke v0.2.1` (fails in this environment because `python -m build` module is unavailable).

# Follow-up

Install development build dependencies in the environment (`pip install -e ".[dev]"`) and rerun `scripts/release-smoke v0.2.1` for full end-to-end confirmation.
