---
resolution: null
blocked_reason: null
blocked: false
id: WI-VERSION-INSTALL-SMOKE-YAML-DEPS
title: Fix wheel-install smoke test missing PyYAML runtime dependency
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
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_ci_pipeline
acceptance:
  - tests/smoke/version_install_smoke.py's wheel-install case no longer passes --no-deps to the `pip install` step
  - The wheel-build `pip wheel --no-deps` step is unchanged (building only lrh's own wheel remains correct)
  - python -m unittest tests.smoke.version_install_smoke passes both the editable-install and wheel-install cases
  - lrh validate passes with 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - tests/smoke/version_install_smoke.py
---

## Summary

Fix `tests/smoke/version_install_smoke.py`'s wheel-install case, which fails
on `main` today with `ModuleNotFoundError: No module named 'yaml'` because it
installs the built wheel with `pip install --no-deps`, skipping the
`PyYAML` runtime dependency that `lrh.cli.main`'s import chain requires.

## Problem / Context

`VersionInstallSmokeTests.test_lrh_version_matches_metadata_for_editable_and_wheel_installs`
builds a wheel from the repo, then installs it into a fresh isolated venv
with `pip install --no-input --no-deps <wheel>` before running
`lrh --version` and a resource-loading check against that venv. `PyYAML` is
a declared runtime dependency (`pyproject.toml`'s `dependencies` list), and
`lrh.cli.main` transitively imports `lrh.conversations.export_inspector`,
which does `import yaml` unconditionally at module load time. A `--no-deps`
install into a venv with nothing else installed cannot run the CLI at all,
so the test fails with `ModuleNotFoundError: No module named 'yaml'`
regardless of whether the version metadata itself is correct — this is
orthogonal to the CLI-vs-metadata invariant the test exists to check.

This was discovered and flagged (not fixed) while investigating and fixing
`WI-VERSION-INTEGRATION-TEST-FLAKE` (`project/work_items/resolved/WI-VERSION-INTEGRATION-TEST-FLAKE.md`):
that work replaced a flaky ambient-environment version-check test with
reliance on this smoke test as equivalent hermetic coverage, and found the
smoke test's wheel-install case was itself already broken on `main`,
independent of that change (confirmed via `git stash` on a clean checkout).

Tracing the code's history: `--no-deps` appears on two separate commands in
this test — the `pip wheel --no-deps` **build** step (correct: it means
"build only lrh's own wheel, don't also build wheels for its dependencies"),
and the `pip install --no-deps` **install** step (the bug: it means "don't
install lrh's dependencies into this venv either," which breaks runtime).
Both flags have been present since the test's original introduction
(`WI-VERSIONING-HARDENING`'s `2026_04_25_16_47_34_SETUPTOOLS_SCM_MIGRATION`
execution record has no comment explaining the install-step `--no-deps`),
consistent with the install-step flag being an unintentional copy of the
build-step flag rather than a deliberate choice.

### Duplication search
- In-repo: No existing fix or open work item found for this specific bug.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this fix specifically (only the
  cross-reference from `WI-VERSION-INTEGRATION-TEST-FLAKE`'s Risk Notes,
  which flagged rather than requested it).
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Remove `--no-deps` from the wheel-install `pip install` command in
  `tests/smoke/version_install_smoke.py`.
- Leave the wheel-build `pip wheel --no-deps` command unchanged.
- Do not otherwise change the test's structure, assertions, or the
  editable-install case.

## Required Changes

1. In `tests/smoke/version_install_smoke.py`'s
   `test_lrh_version_matches_metadata_for_editable_and_wheel_installs`,
   remove the `"--no-deps"` argument from the `install_wheel` `pip install`
   invocation (around lines 189-198), so the wheel installs with its
   declared runtime dependencies (`PyYAML`), matching how a real end user
   installing this wheel would behave and matching the editable-install
   case earlier in the same test (a full `pip install -e .`, no
   `--no-deps`).
2. Leave the `pip wheel --no-deps` build-step invocation (around lines
   166-178) unchanged — it correctly scopes the wheel build to `lrh`
   itself.

## Non-Goals

- Do not change the wheel-build step's `--no-deps` flag.
- Do not add a new test or restructure the existing test's assertions.
- Do not address the ambient-environment flake that
  `WI-VERSION-INTEGRATION-TEST-FLAKE` already resolved.

## Acceptance Criteria

- The wheel-install `pip install` command in
  `tests/smoke/version_install_smoke.py` no longer passes `--no-deps`.
- `python -m unittest tests.smoke.version_install_smoke` passes both the
  editable-install and wheel-install cases.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `python -m unittest tests.smoke.version_install_smoke`

## Risk Notes

- **Slower installs:** installing with dependencies makes the wheel-install
  venv setup marginally slower (has to install `PyYAML`), but this is a
  smoke test, not run in the default `scripts/test` unit suite, so the
  cost is acceptable and matches the editable-install case's existing
  behavior.
- **Network/build-dependency availability:** the test's own
  `_maybe_skip_for_unavailable_build_deps` already skips gracefully when
  package-index access is unavailable; installing with deps exercises the
  same skip path, just for one more package.
