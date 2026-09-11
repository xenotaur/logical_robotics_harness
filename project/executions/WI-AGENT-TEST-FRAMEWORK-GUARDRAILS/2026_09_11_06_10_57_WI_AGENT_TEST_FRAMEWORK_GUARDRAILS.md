---
execution_id: 2026_09_11_06_10_57_WI_AGENT_TEST_FRAMEWORK_GUARDRAILS
prompt_id: PROMPT(WI-AGENT-TEST-FRAMEWORK-GUARDRAILS:WI_AGENT_TEST_FRAMEWORK_GUARDRAILS)[2026-09-10T18:37:36+00:00]
work_item: WI-AGENT-TEST-FRAMEWORK-GUARDRAILS
status: landed
rerun_of: null
pr: https://github.com/xenotaur/logical_robotics_harness/pull/663
commit: 449425a1
created_at: 2026-09-11T06:10:57+00:00
agent: gemini_3_8_flash
instruction_source: project/work_items/proposed/WI-AGENT-TEST-FRAMEWORK-GUARDRAILS.md
session_transcript: antigravity:ee9322ca-0c0c-4693-99c5-261848a6d19f
---

# Summary

Implement `WI-AGENT-TEST-FRAMEWORK-GUARDRAILS` to enforce standard library `unittest` usage and canonical script wrappers (`scripts/test`, `scripts/lint`, `scripts/format`) across all AI agents and human contributors via a two-layer closed-loop guidance system.

# Result

- Updated `AGENTS.md` with explicit `## Testing and Validation Mandate` section under `## Environment setup before validation`.
- Configured Ruff `flake8-tidy-imports.banned-api` (`TID251`) in `pyproject.toml` to ban `pytest` with a message citing `STYLE.md Rule 5`.
- Updated test discovery requirements in both `src/lrh/skills/lrh-implement/references/canonical-validation.md` and `.claude/skills/lrh-implement/references/canonical-validation.md`.
- Ran `/lrh-self-review` diff-mode subagent pass; verified 0 issues and confirmed acceptance criteria satisfaction.
- Opened implementation PR #663.

# Validation

- `scripts/version tools`: Black 26.3.1, Ruff 0.15.12, Python 3.11.15 confirmed.
- `scripts/format --check --diff`: 250 files unchanged.
- `scripts/lint`: All checks passed.
- `scripts/test`: Ran 1404 tests in 83.945s OK.
- `lrh validate`: 0 error(s), 0 warning(s).
- `diff -r src/lrh/skills/lrh-implement/ .claude/skills/lrh-implement/`: 0 differences.
- Mechanical error verification: `ruff check` on `import pytest` triggers `TID251: STYLE.md Rule 5: Use standard library unittest.TestCase subclasses; pytest is prohibited.`.

# Follow-up

- Monitor reviewer feedback on PR #663 and run `/lrh-land` to review, confirm, and merge.
