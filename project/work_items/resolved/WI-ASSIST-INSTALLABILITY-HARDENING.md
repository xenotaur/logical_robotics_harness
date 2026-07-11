---
resolution: "Implemented and merged in PR #387 (commit fd5d71b): scripts/release-smoke now runs real installed-wheel invocations (lrh request templates list, lrh project init + snapshot) proving package-resource template loading works outside a source checkout; also fixed a pre-existing tests/dev_tests/ test-discovery gap and hardened the check against maintainer-local template-override env vars."
blocked_reason: null
blocked: false
id: WI-ASSIST-INSTALLABILITY-HARDENING
title: Harden installed-package template loading and packaging smoke checks
type: operation
status: resolved
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on:
  - WI-ASSIST-TEMPLATES-PACKAGING
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - template loading uses package resources rather than source-tree-relative paths
  - install/build flow includes smoke checks for `lrh request` and `lrh snapshot` behavior from an installed package context
  - documentation records installed-package expectations
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - code_diff
  - smoke_test_output
---

## Summary

Treat package-data correctness and installed-package behavior as first-class requirements before broader collaborator-facing publication.

## Scope

In scope:

- extend `scripts/release-smoke` to run real, non-`--help` invocations of
  `lrh request templates list` and `lrh project init` + `lrh snapshot`
  against the installed wheel, proving package-resource template resolution
  actually works outside a source checkout
- document the expanded smoke coverage in `docs/how-to/run-a-release.md`

Out of scope / already satisfied by prior work:

- migrating template loading to package resources — `WI-ASSIST-TEMPLATES-PACKAGING`
  already did this. `src/lrh/assist/template_resolver.py`,
  `src/lrh/assist/request_templates.py`, and `src/lrh/project/bootstrap.py`
  all resolve templates via `importlib.resources`, and
  `pyproject.toml`'s `[tool.setuptools.package-data]` already declares the
  assist, project-bootstrap, and skills template directories as package data.
  No source-tree-relative template path construction remains.

## Required Changes

- Edit `src/lrh/dev/release_smoke.py`: after the existing `--help` coverage
  loop, add a `lrh request templates list` invocation (run with `cwd` pinned
  to an isolated, override-free directory) and assert every resolved
  template reports `source: package`; add an `lrh project init --profile
  minimal --project-root <tmp>` + `lrh snapshot project --project-root <tmp>
  --stdout` sequence as a real end-to-end check.
- Add a `_check_template_sources_are_package` helper that raises
  `ReleaseSmokeError` on empty output or any non-`package` source.
- Update `tests/dev_tests/release_smoke_test.py` mocked-command fakes and
  assertions to match, plus direct unit tests for the new helper.
- Update `docs/how-to/run-a-release.md`'s "Release smoke test" section to
  document the expanded coverage.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- Manually run `scripts/release-smoke` once locally to confirm the new
  invocations pass against a real built wheel.
