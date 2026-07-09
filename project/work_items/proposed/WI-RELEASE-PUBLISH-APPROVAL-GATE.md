---
resolution: null
blocked_reason: null
blocked: false
id: WI-RELEASE-PUBLISH-APPROVAL-GATE
title: Add required-reviewer approval gate to PyPI publish environment
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
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - the `pypi` GitHub environment requires manual review before `release.yml`'s `publish-pypi` job runs
  - the `testpypi` GitHub environment intentionally remains unprotected, with the reasoning recorded
  - `docs/how-to/run-a-release.md` documents that any `vMAJOR.MINOR.PATCH` tag push arms both the TestPyPI rehearsal tag requirement and the real `release.yml` publish path simultaneously, and describes the rehearse-then-approve sequencing this gate enables
required_evidence:
  - manual_review
artifacts_expected:
  - documentation_diff
---

## Summary

`PROP-TAG-PUSH-PYPI-PUBLISHING` §12 left "whether to use GitHub
environments/protection rules" as an open implementation choice. Resolve it
by adding a required-reviewer approval gate to the `pypi` GitHub environment,
and document the release/rehearsal sequencing this makes possible.

## Background

`release.yml` triggers on any `push: tags: v*.*.*` and has no gate between a
successful build/smoke job and the real PyPI publish step
(`.github/workflows/release.yml`). `testpypi-rehearsal.yml` is
`workflow_dispatch`-only and can only be dispatched against a tag ref that
already contains the workflow file in its tree — no tag prior to
2026-05-06 (`v0.2.0`-`v0.2.4`) qualifies. Because both workflows key off the
same tag shape, pushing a tag for rehearsal purposes also arms a real
production publish with no manual checkpoint, unless a GitHub environment
protection rule intervenes. See `project/memory/decision_log.md`
(2026-07-09: "PyPI Release Environment Protection Rules") for the full
decision record.

## Scope

In scope:

- configure a required-reviewer protection rule on the `pypi` GitHub
  environment (reviewer: `xenotaur`, i.e. Anthony Francis)
- confirm the `testpypi` environment remains unprotected
- update `docs/how-to/run-a-release.md` to document the tag/rehearsal
  collision and the rehearse-then-approve procedure it enables: push a real
  release tag, let `release-tag-ci.yml`/`smoke.yml` run and `release.yml`'s
  `publish-pypi` job pause for review, dispatch `testpypi-rehearsal.yml`
  against the same tag while it's pending, verify the TestPyPI install, then
  approve (or reject) the pending `pypi` deployment

Out of scope:

- exercising the gate end-to-end against a real release tag (depends on
  `WI-ASSIST-INSTALLABILITY-HARDENING` landing first, per the current
  sequencing decision to land packaging hardening before the next real
  publish); this will be evidenced when the first real post-hardening
  release actually runs, not by this work item
- changes to `release.yml` or `testpypi-rehearsal.yml` trigger conditions

## Notes

The `pypi` environment protection rule was configured directly via
`gh api -X PUT repos/xenotaur/logical_robotics_harness/environments/pypi`
during the design conversation that produced this work item, since it is a
non-code, immediately reversible, additive-safety change. This work item
formally records that action and captures the remaining documentation update.
