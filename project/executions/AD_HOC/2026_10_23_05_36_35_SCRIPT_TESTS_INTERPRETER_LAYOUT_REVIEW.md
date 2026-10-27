---
execution_id: 2026_10_23_05_36_35_SCRIPT_TESTS_INTERPRETER_LAYOUT_REVIEW
prompt_id: PROMPT(AD_HOC:SCRIPT_TESTS_INTERPRETER_LAYOUT_REVIEW)[2026-10-15T06:01:29+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/843
commit:
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/843
session_transcript: claude-app:0e4e3c2a-6f50-4437-97b6-1a9381812245
created_at: 2026-10-23T05:36:35+00:00
---

# Summary

Addressed two open Copilot review threads on PR #843 (harden desktop script
tests against interpreter layout; warn on wrong env). Both asked for
deterministic test coverage of the new behavior. This was the single P3 fix
round agreed at the /lrh-land Step 2 chain gate.

# Result

**Thread 1** (`#discussion_r4265983391`, Copilot) — the `scripts/test`
wrong-environment warning had no automated coverage. Present and valid.
Added `tests/scripts_tests/test_script_environment_warning_test.py`, which
runs `scripts/test` with a stub `python3` and a controlled PATH and asserts:
a warning naming the env prefix and interpreter when `CONDA_PREFIX` or
`VIRTUAL_ENV` is set but `python3` resolves outside it; no warning when
`python3` is inside the env; no warning when no env is active.

**Thread 2** (`#discussion_r4265983427`, Copilot) — the `_tools_dir`
fallback was not exercised deterministically. Present and valid. Added
`ToolsDirTest` to `tests/scripts_tests/desktop_modes_test.py`, patching
`sys.executable` and `shutil.which`: a Homebrew-style layout links `python`
(to the interpreter) and the missing `black`/`ruff`/`pip` to the `which`
results; tools already beside the interpreter are not linked; a tool absent
from PATH is left out.

Non-regression check: the new tests were run against an extracted
`git archive origin/main` tree (which lacks both the warning and
`_tools_dir`): the two warning tests failed and the three `ToolsDirTest`
tests errored, as intended; the two "silent" cases pass there by design.

Publication: pushed directly to the PR branch (`9bff0568..cc5c29b3`).

No primary execution record exists for this PR (opened ad hoc outside
/lrh-implement), so `rerun_of` is empty.

# Validation

- `scripts/version tools`: pinned versions match (LRH conda env first on PATH)
- `scripts/format --check --diff`: 299 files unchanged
- `scripts/lint`: ruff, black, and test-framework guardrails clean
- `scripts/test`: 2319 tests OK (2312 existing + 7 new)
- `lrh validate`: 0 errors, 0 warnings

# Follow-up

- The Codex issue comment on the PR is not a review thread; it is assessed
  in the confirm-fixes step.
- Unifying the bare `python` calls in `scripts/version`, `lint`, `clean`
  with `${PYTHON:-python3}` remains deferred (needs its own change).
