---
execution_id: 2026_09_11_07_25_08_WI_AGENT_TEST_FRAMEWORK_GUARDRAILS_REVIEW
prompt_id: PROMPT(WI-AGENT-TEST-FRAMEWORK-GUARDRAILS:WI_AGENT_TEST_FRAMEWORK_GUARDRAILS_REVIEW)[2026-09-11T07:25:08+00:00]
work_item: WI-AGENT-TEST-FRAMEWORK-GUARDRAILS
status: in_progress
rerun_of: 2026_09_11_06_10_57_WI_AGENT_TEST_FRAMEWORK_GUARDRAILS
pr: https://github.com/xenotaur/logical_robotics_harness/pull/663
commit: bbb7dd0c
created_at: 2026-09-11T07:25:08+00:00
agent: gemini_3_8_flash
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/663
session_transcript: antigravity:ee9322ca-0c0c-4693-99c5-261848a6d19f
---

# Summary

Review response for PR #663 addressing Copilot and Codex review feedback.

# Result

- Implemented AST-based test framework guardrails in `src/lrh/control/test_guardrails.py` and integrated into `scripts/lint` to mechanically detect and reject standalone `test_*` functions and pytest fixtures.
- Added comprehensive unit tests in `tests/guardrails_tests/test_framework_guardrails_test.py`.
- Updated `AGENTS.md` mandate to explicitly name `scripts/test`, `scripts/lint`, and `scripts/format --check --diff`.
- Set `commit: null` in primary execution record while in-progress.
- Synchronized `canonical-validation.md` across `.agents/` and `.gemini/` skill directories.
- Renamed `tmp_path` parameter to `target_dir` in `tests/conversations_tests/antigravity_export_test.py`.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12 confirmed
- `scripts/format --check --diff` — 252 files unchanged
- `scripts/lint` — all checks passed (including test framework guardrails check)
- `scripts/test` — 1409 tests OK
- `lrh validate` — 0 errors, 1 warning (pre-existing)

# Follow-up

- Run confirm-fixes pass and proceed with merge gate.
