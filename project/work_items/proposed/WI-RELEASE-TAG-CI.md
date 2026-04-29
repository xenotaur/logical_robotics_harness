---
resolution: null
blocked_reason: null
blocked: false
id: WI-RELEASE-TAG-CI
title: Add release tag CI verification workflow
type: operation
status: proposed
priority: high
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-02
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - add_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - GitHub Actions workflow triggers on release-like tags matching `v*.*.*`
  - tag workflow checks out the exact tag and runs version verification, build, and release-smoke validation steps
  - workflow logs/artifacts provide enough traceability for release auditability
  - docs describe release tag CI behavior and expected checks
  - PyPI/TestPyPI publishing remains out of scope unless explicitly covered by a separate publishing work item
required_evidence:
  - code_diff
  - test_result
  - manual_review
artifacts_expected:
  - workflow_yaml
  - ci_run_log
  - documentation_diff
---

## Summary

Add a dedicated release-tag CI workflow so LRH release tags are independently verified in CI before any future publication automation is considered.

## Scope

In scope:

- add a GitHub Actions workflow that triggers on tags such as `v*.*.*`
- checkout the tagged revision under test
- install development dependencies needed for release verification
- run version/build/release-smoke validation suitable for a tagged release candidate
- capture and expose enough workflow output for release audit trails
- document how tag CI behaves and what it verifies

Out of scope:

- PyPI/TestPyPI publishing automation
- trusted publishing credentials or OIDC policy setup
- non-release branch CI redesign

## Acceptance Criteria

- workflow triggers when a release tag like `v1.2.3` is pushed
- workflow verifies release version semantics against the tag under test
- workflow builds release artifacts and executes release-smoke validation
- workflow output is retained in logs/artifacts to support post-hoc release review
- documentation includes a concise explanation of tag CI behavior

## Notes

Future trusted publishing to PyPI/TestPyPI should be tracked as a separate work item unless explicitly scoped elsewhere.

## Required Changes

- Add a GitHub Actions workflow for release-tag validation.
- Trigger the workflow on pushed version tags matching `v*.*.*`.
- Check out the tagged commit.
- Set up the project's supported Python version.
- Install the project with development dependencies.
- Run the release verification workflow for the tag, using the tag name from the GitHub ref.
- Run `scripts/release-smoke` against the tag.
- Ensure the workflow does not publish to PyPI or TestPyPI.
- Update release documentation to mention tag-triggered CI if needed.

## Validation

- Run `scripts/format --check`
- Run `scripts/lint`
- Run `scripts/test`
- Run `scripts/version verify "$TAG_UNDER_TEST"`
- Run `scripts/release-smoke "$TAG_UNDER_TEST"`
- Review the GitHub Actions workflow and confirm it triggers on pushed tags matching `v*.*.*`.
- Confirm the workflow uses the pushed tag name, such as `${{ github.ref_name }}`, when invoking release checks.

Also confirm the GitHub Actions workflow is configured to trigger on pushed tags:

```yaml
on:
  push:
    tags:
      - "v*.*.*"
```

and confirm the implementation uses the pushed tag name (for example `${{ github.ref_name }}`) when invoking release checks and validation commands.

