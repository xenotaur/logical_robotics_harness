---
execution_id: 2026_08_05_06_26_06_VERSION_INTEGRATION_TEST_FLAKE
prompt_id: PROMPT(AD_HOC:VERSION_INTEGRATION_TEST_FLAKE)[2026-08-05T06:20:28+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/489
commit: 932f2f337b7540537d4cf245e6daadb18c24345a
created_at: 2026-08-05T06:26:06+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-VERSION-INTEGRATION-TEST-FLAKE.md
session_transcript: claude-app:75bc649d-3851-4e5e-944a-822d6315d2ae
---

# Summary

Investigated the intermittent `tests/cli_tests/version_integration_test.py`
failure (mismatched `lrh --version` vs. `importlib.metadata.version("lrh")`
across many unrelated PR-landing sessions), filed
`WI-VERSION-INTEGRATION-TEST-FLAKE` to document the root cause, and
implemented the fix in the same PR.

# Result

Confirmed the mechanism: multiple Claude Code sessions in separate git
worktrees share one local conda env and each independently reruns
`pip install -e .` (`scripts/develop`); a concurrent reinstall can flip the
on-disk `.dist-info` metadata for the PEP 660 editable install between the
test's two reads (parent-process `importlib.metadata.version()` and a
`lrh --version` subprocess spawned moments later). CI never hits this
because each job installs once, upfront. `tests/smoke/version_install_smoke.py`
already asserts the same CLI-vs-metadata invariant hermetically (isolated
temp venvs for both editable and wheel installs), so the ambient-environment
version added no coverage beyond what already exists while being the sole
source of the flake — matching this repo's `AGENTS.md` hermetic-unit-test
convention and its precedent of moving `CrossPrDiscoveryGitSimulationTest`
out of the unit suite for the same reason.

Deleted `tests/cli_tests/version_integration_test.py` and removed its now-stale
reference from `project/work_items/proposed/WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION.md`.
`tests/version_test.py` (in-process `format_cli_version()` coverage) and
`tests/smoke/version_install_smoke.py` are unchanged.

While validating, found and flagged (via a spawned background task, not
fixed here) an unrelated pre-existing bug: the wheel-install case of
`tests/smoke/version_install_smoke.py` fails on `main` today with
`ModuleNotFoundError: No module named 'yaml'`, because it installs the
built wheel with `--no-deps`, omitting the declared `PyYAML` runtime
dependency that `lrh.cli.main`'s import chain requires. Reproduced via
`git stash` on a clean checkout of this branch's base, so it predates and
is unrelated to this change.

# Validation

- `lrh validate` — 0 errors, 0 warnings
- `scripts/format --check --diff` — clean, 188 files unchanged
- `scripts/lint` — all checks passed
- `scripts/test` — 953 tests, OK
- `python -m unittest tests.smoke.version_install_smoke` — editable-install
  case passes; wheel-install case fails for the unrelated pre-existing
  reason noted above (reproduced identically on a clean stash of this
  branch's base, i.e. not caused by this change)

# Follow-up

- Flagged the pre-existing `tests/smoke/version_install_smoke.py`
  wheel-install `--no-deps`/`yaml` failure as a separate task
  (`task_d07fcd9c`) rather than fixing it in this PR.
