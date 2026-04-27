---
execution_id: 2026_04_26_23_47_24_TESTING_POLICY_DOCS
prompt_id: PROMPT(AD_HOC:TESTING_POLICY_DOCS)[2026-04-26T10:05:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 7d6fe9a
created_at: 2026-04-26T23:47:24+00:00
---

# Summary

Documented LRH unit-vs-smoke testing policy across contributor guidance docs while preserving the "prefer real objects over heavy mocking" testing principle with explicit external-boundary exceptions.

# Result

- Updated `STYLE.md` testing guidance to require fast/deterministic/hermetic unit tests, prohibit installer/network/git-heavy subprocess activity in unit tests, and direct build/install/package checks to `tests/smoke/*_smoke.py` via `scripts/smoke`.
- Added concise agent-facing note in `AGENTS.md` with the same policy distinction.
- Added top-level README testing-tier command guidance for `scripts/test` vs `scripts/smoke`.

# Validation

- `scripts/test` passed.
- `scripts/lint` passed Ruff lint but failed Black check due to pre-existing formatting issue in `tests/control_tests/parser_test.py`.
- `scripts/format --check` reported the same pre-existing file (`tests/control_tests/parser_test.py`) would be reformatted.
- `scripts/smoke` executed and completed with 1 skipped smoke test.

# Follow-up

- Optional follow-up: run `scripts/format` in a dedicated formatting-focused PR to address the pre-existing `tests/control_tests/parser_test.py` Black drift.
