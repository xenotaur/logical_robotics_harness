---
execution_id: 2026_04_27_06_15_06_RELEASE_WORKFLOW_FIXES
prompt_id: PROMPT(AD_HOC:RELEASE_WORKFLOW_FIXES)[2026-04-27T02:25:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-04-27T06:15:06+00:00
---

# Summary

Harden release workflow docs and scripts by adding explicit cleanup/release-smoke entry points, declaring `build` as a dev dependency, and replacing fragile README release shell fragments.

# Result

Added `scripts/release-smoke` plus `lrh.dev.release_smoke` to rebuild artifacts cleanly, install exactly one wheel in a temporary venv, and validate installed CLI commands. Reworked `scripts/clean` into a conservative Python-backed helper with `--help`/`--dry-run`, and updated release docs in `README.md` plus scripts documentation.

# Validation

- Ran `scripts/format --check` (fails due pre-existing unrelated formatting in `tests/control_tests/parser_test.py`).
- Ran `scripts/lint` (ruff passes; black check fails due same pre-existing formatting issue).
- Ran `scripts/test` (passes).
- Ran `scripts/release-smoke` (fails in this environment because `python -m build` is unavailable; failure path verified).

# Follow-up

Install project dev dependencies in the execution environment (`pip install -e ".[dev]"`) before running full release-smoke end-to-end.
