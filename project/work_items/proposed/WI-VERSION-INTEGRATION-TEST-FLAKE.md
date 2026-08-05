---
resolution: null
blocked_reason: null
blocked: false
id: WI-VERSION-INTEGRATION-TEST-FLAKE
title: Remove ambient-environment-coupled version integration test
type: operation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - delete_file
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_ci_pipeline
acceptance:
  - tests/cli_tests/version_integration_test.py no longer exists
  - tests/version_test.py and tests/smoke/version_install_smoke.py are unchanged
  - project/work_items/proposed/WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION.md no longer references version_integration_test.py
  - scripts/test passes with 0 failures
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - tests/cli_tests/version_integration_test.py (deleted)
  - project/work_items/proposed/WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION.md
---

## Summary

Remove `tests/cli_tests/version_integration_test.py`, a hermetic-suite test
whose assertion depends on ambient local-environment install state and races
against concurrent editable reinstalls, since its coverage is already
provided hermetically by `tests/smoke/version_install_smoke.py`.

## Problem / Context

`tests/cli_tests/version_integration_test.py` asserts that `lrh --version`'s
subprocess output matches `importlib.metadata.version("lrh")` read in the
parent pytest process. Both reads hit the same on-disk `.dist-info`
metadata for whatever `lrh` install is active in the ambient environment —
for a PEP 660 editable install, that metadata is frozen until the next
`pip install -e .` reinstall. This test has failed intermittently across many
unrelated PR-landing sessions in this repo's local dev conda env
(`/Users/centaur/anaconda3/envs/LRH`), with mismatches like
`'lrh 0.2.5.dev83+g40da6c798' != 'lrh 0.2.5.dev1028+gef78f71dd'`, confirmed
not caused by the changes under test (reproduced on a clean stash, before any
edits, every time). The mechanism: multiple Claude Code sessions running in
separate git worktrees share this one conda env, and each independently runs
`scripts/develop` (`pip install -e ".[dev]"`) as part of its own workflow. A
reinstall triggered by a concurrent, unrelated session can land on disk
between this test's two reads, flipping the `.dist-info` version string
mid-test. Every GitHub Actions workflow installs once per job before running
tests, so this race has only ever been observed locally, never in CI.

This is exactly the environment coupling `AGENTS.md`'s hermetic-unit-test
rule (line 135) exists to keep out of the unit suite: "Keep unit tests fast,
deterministic, and hermetic: avoid pip/installer calls, package-index/network
access, Git remotes, and heavyweight subprocesses in the normal unit suite
... Put real install/build/package checks in `tests/smoke/*_smoke.py`."
There is direct precedent this session for moving a real-subprocess test out
of the unit suite for this reason: `CrossPrDiscoveryGitSimulationTest` was
relocated from `tests/assist_tests/` to
`tests/smoke/prompt_workflow_slug_cross_pr_smoke.py`.

Critically, `tests/smoke/version_install_smoke.py`
(`VersionInstallSmokeTests.test_lrh_version_matches_metadata_for_editable_and_wheel_installs`)
already asserts the identical CLI-vs-metadata invariant — and does so more
rigorously, by building isolated temp venvs for both an editable install and
a built wheel, so it is immune to ambient-environment drift. The
ambient-environment version in `tests/cli_tests/` therefore adds no coverage
beyond what the smoke test already provides, while being the sole source of
this flake. `tests/version_test.py`'s in-process unit coverage of
`format_cli_version()` is unaffected and remains the fast unit-level check
for that function's logic.

### Duplication search
- In-repo: Related: `tests/smoke/version_install_smoke.py` already covers
  the same CLI-vs-metadata assertion hermetically (stronger coverage, via
  isolated venvs for both editable and wheel installs).
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed — remove the redundant, flake-prone ambient-env
  test rather than extend it.

### Demand search
- Work items: Found: `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION` — "Migrate
  remaining per-subcommand cli_tests files into cli_tests/main_tests/" lists
  `version_integration_test.py` as a file that stays at `tests/cli_tests/`
  (unrelated to this WI's own scope, but stale once this file is deleted;
  update its reference as part of this WI's Required Changes).
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No closeout action beyond the reference update noted above
  (that WI's own scope is untouched).

## Scope

- Delete `tests/cli_tests/version_integration_test.py`.
- Update the stale reference to that file in
  `project/work_items/proposed/WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION.md`.
- Leave `tests/version_test.py` and `tests/smoke/version_install_smoke.py`
  unchanged.

## Required Changes

1. Delete `tests/cli_tests/version_integration_test.py`.
2. Remove the `version_integration_test.py` bullet from
   `project/work_items/proposed/WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION.md`'s
   "Files that stay at `tests/cli_tests/`" list (Required Changes section),
   since the file no longer exists.
3. Run the full validation sequence below and confirm no other file
   references `tests/cli_tests/version_integration_test.py`.

## Non-Goals

- Do not modify `tests/version_test.py` — its in-process coverage of
  `format_cli_version()` is hermetic and unaffected by this change.
- Do not modify `tests/smoke/version_install_smoke.py` — it already provides
  the coverage this WI relies on as replacement.
- Do not implement `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION`'s broader file-move
  scope — only its stale reference to the deleted file is touched here.
- Do not add a new isolated-venv-per-test hermetic version integration test
  to the unit suite; `tests/smoke/version_install_smoke.py` already fills
  that role at the appropriate (smoke) tier.

## Acceptance Criteria

- `tests/cli_tests/version_integration_test.py` no longer exists.
- No remaining references to `version_integration_test` in the repository
  outside of historical `project/executions/` records.
- `scripts/test` passes with 0 failures.
- The editable-install case of
  `tests/smoke/version_install_smoke.py::VersionInstallSmokeTests::test_lrh_version_matches_metadata_for_editable_and_wheel_installs`
  (the CLI-vs-metadata assertion this WI relies on as replacement coverage)
  passes. Note: that same test's wheel-install case currently fails on
  `main` for an unrelated, pre-existing reason (`--no-deps` wheel install
  omits the `PyYAML` runtime dependency, which `lrh.cli.main` imports
  transitively) — out of scope here; tracked separately.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- **Coverage gap risk:** if `tests/smoke/version_install_smoke.py` is ever
  itself removed or weakened, the CLI-vs-metadata invariant would go
  unchecked. Low risk in practice since that test is the more rigorous of
  the two and has no known issues.
- **Stale WI reference:** `WI-TEST-LAYOUT-MAIN-TESTS-MIGRATION` is still
  `proposed`; if it is implemented before this WI's reference update lands,
  its implementor would hit a missing file. Landing both in the same PR
  removes this risk.
- **Unrelated pre-existing smoke failure:** confirmed independently (via
  `git stash` on a clean checkout of this branch's base) that
  `tests/smoke/version_install_smoke.py`'s wheel-install case fails on
  `main` today with `ModuleNotFoundError: No module named 'yaml'` — a
  `--no-deps` wheel install skips the `PyYAML` runtime dependency that
  `lrh.cli.main`'s import chain requires. This is unrelated to this WI and
  is not fixed here; flagged separately for its own fix.
