---
id: PROP-TAG-PUSH-PYPI-PUBLISHING
type: design_proposal
title: Option D tag-push PyPI publishing for safe-default lrh distribution
status: accepted
created_on: 2026-05-05
updated_on: 2026-05-05
---

## 1) Purpose

Define a design target for making LRH installable via `pipx install
lrh` (and `pip install lrh` where appropriate) by introducing a
tag-push release flow that builds, validates, smoke-tests, and
publishes the safe-default `lrh` distribution to PyPI using Trusted
Publishing.

This proposal is design-only. It does not implement workflows,
packaging metadata changes, package splits, or CLI behavior changes in
this PR.

## 2) Problem and motivation

LRH is intended to be reusable across independent project
repositories, not only from this source checkout. Today, practical use
still depends heavily on repository-local setup assumptions (clone,
editable install, repository-relative paths).

LRH should support standard contributor/user installation:

```bash
pipx install lrh
pip install lrh
```

Motivation:

- installed-package behavior should work without assuming source-tree
  layout;
- assist templates and runtime resources should be package-owned and
  loadable from installed-package resources;
- release outcomes should produce inspectable evidence (build
  artifacts, smoke-test results, release notes/publish results).

## 3) Proposed release goal

Target design:

```text
Option D: tag-push PyPI publishing for the safe-default `lrh` package.
```

Illustrative release trigger:

```bash
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

Illustrative workflow responsibilities:

1. check out repository,
2. set up Python,
3. install build/check tooling,
4. run canonical validation/test/lint/format checks as appropriate,
5. build sdist and wheel,
6. run artifact checks,
7. install built wheel in a clean environment,
8. run installed-package smoke tests,
9. publish to PyPI via Trusted Publishing (OIDC).

This is the design target for later implementation PRs.

## 4) Safe-default package semantics

The release target must remain compatible with safe-default,
non-agentic LRH packaging direction:

- `pipx install lrh` installs the safe-default non-agentic LRH
  CLI/toolkit;
- default `lrh` should not include LRH autonomous execution package or
  autonomous-loop command implementation;
- future agentic capability remains explicit via `lrh[agentic]`
  and/or `lrh-agentic`;
- initial publishing does not require full future package split.

Wording guardrail:

> The default `lrh` install does not include LRH's autonomous
> execution package or autonomous-loop command implementation.

This is a packaging/governance boundary statement, not a runtime
sandbox claim.

## 5) Relationship to future package split

Option D is compatible with a future capability split:

```text
lrh-core      # deterministic core: control plane, validation, snapshots, shared models
lrh-assist    # human-triggered assist workflows: request/snapshot/survey/templates
lrh-agentic   # autonomous loop and risky execution integrations
lrh           # user-facing safe-default distribution and CLI
```

Recommended incremental posture:

1. publish `lrh` first as safe-default distribution,
2. preserve current import/module layout initially,
3. avoid broad import churn or premature package splitting,
4. add `lrh[agentic]` when a concrete `lrh-agentic` package exists,
5. reserve/publish additional names only with concrete implementation
   need.

## 6) Packaging metadata and installed resources (design requirements)

Future implementation should keep `pyproject.toml` as packaging source
of truth and target:

- distribution name `lrh` (if available),
- CLI command `lrh`,
- console script wired to existing CLI entry point,
- complete package metadata (README, license, Python version,
  classifiers, dependencies, package data),
- runtime resources (assist templates, similar assets) loaded via
  package-resource semantics rather than repository-relative paths.

These are requirements for follow-on implementation work, not this PR.

## 7) Trusted Publishing design

The target should use PyPI Trusted Publishing rather than a long-lived
PyPI API token stored in GitHub secrets.

Design intent:

- GitHub Actions publishes with OIDC (`id-token: write`),
- PyPI trusts the specific repository/workflow identity.

Benefits:

- no long-lived token in repository secrets,
- short-lived credentials per publish event,
- clearer release provenance,
- repeatable/auditable publishing path,
- stronger supply-chain posture.

## 8) Workflow shape (illustrative)

```yaml
on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-python
      - install build tooling
      - run validation/tests/lint/format as appropriate
      - python -m build
      - twine check dist/*
      - run installed-wheel smoke tests
      - upload artifacts

  publish:
    needs: build
    permissions:
      id-token: write
    steps:
      - download artifacts
      - publish with pypa/gh-action-pypi-publish
```

This sketch is intentionally non-final and implementation-neutral.

## 9) TestPyPI rehearsal lane

Recommended posture:

- use TestPyPI rehearsal before first real PyPI release,
- use TestPyPI when changing release mechanics,
- do not force every routine release through TestPyPI when it becomes
  unnecessary overhead,
- document TestPyPI differences/limits in maintainer release docs.

## 10) Smoke tests and release evidence

Future release flow should include installed-wheel smoke checks such as:

```bash
python -m build
twine check dist/*
python -m venv "$tmpvenv"
"$tmpvenv/bin/python" -m pip install dist/*.whl
"$tmpvenv/bin/lrh" --help
"$tmpvenv/bin/lrh" validate --help
"$tmpvenv/bin/lrh" request --help
"$tmpvenv/bin/lrh" snapshot --help
"$tmpvenv/bin/lrh" survey --help
```

Future safe-default checks once command surface exists:

```bash
lrh agentic --help
# should clearly report that agentic support is optional and not installed
```

Release evidence should capture build output, artifact checks,
installed-wheel smoke results, and publish results.

## 11) User-facing install documentation direction

Future implementation docs should include:

```bash
pipx install lrh
pip install lrh
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lrh
```

Only after extra/package exists, document:

```bash
pipx install "lrh[agentic]"
```

Default recommendation should be `pipx install lrh` for normal CLI use;
`pip install lrh` remains useful for library use, CI, and development
contexts.

## 12) Open implementation choices to resolve

Still-open decisions:

- exact workflow filenames and TestPyPI/PyPI workflow split,
- trigger policy (tag push only vs. tag + release publication),
- Python versions for build/smoke jobs,
- release workflow scope vs prerequisite CI scope,
- whether release artifacts attach to GitHub Releases,
- exact versioning mechanics and interaction with version/tag scripts,
- whether to use GitHub environments/protection rules,
- how to document and verify package-resource loading for templates.

Recommended defaults:

- tag-push trigger,
- PyPI Trusted Publishing authentication,
- `lrh` distribution name and CLI command,
- non-agentic default install,
- TestPyPI rehearsal lane,
- clean-venv installed-wheel smoke checks,
- defer broad package splits.

## 13) Tradeoffs

### Pros

- one-command user/contributor install,
- no source checkout required for normal CLI use,
- repeatable release process,
- stronger credential posture than long-lived tokens,
- good fit for `pipx` command-line installation,
- compatible with future `lrh[agentic]` direction,
- explicit safe-default install story,
- evidence-friendly release pipeline.

### Cons

- release workflow complexity,
- PyPI/TestPyPI setup overhead,
- ongoing metadata and docs maintenance burden,
- possible first-release friction (name reservation/availability),
- risk of overclaiming safety from package boundaries,
- future compatibility/versioning burden if split distributions land,
- docs/workflow drift risk without discipline.

## 14) Risks and mitigations

- **Package name unavailable/conflicted.** Confirm `lrh` availability
  before first publish; fallback candidate could be
  `logical-robotics-harness` while preserving CLI command `lrh`.
- **Installed-package behavior breaks due to source assumptions.** Add
  installed-wheel smoke tests and package-resource checks.
- **Publish from wrong ref/event.** Restrict workflow to version tags
  and narrow Trusted Publisher configuration.
- **Credential leakage risk.** Prefer Trusted Publishing over stored
  long-lived API tokens.
- **Misread safe-default claim.** Document boundary as
  packaging/governance intent, not runtime sandboxing.

## 15) Phased implementation sequence (follow-up work)

1. land this proposal (plus index pointers),
2. verify packaging metadata/resource-loading plan,
3. add/refine build + release-smoke scripts,
4. add local installed-wheel smoke checks,
5. add TestPyPI rehearsal workflow or documented rehearsal path,
6. configure TestPyPI Trusted Publisher,
7. configure PyPI Trusted Publisher,
8. add tag-push PyPI publish workflow,
9. update user install + maintainer release docs,
10. run rehearsal release, then first real release.

Follow-up PRs should remain narrow and evidence-backed.

## 16) Relationship to LRH principles and canonical docs

This design supports LRH direction by emphasizing:

- explicit state over implicit assumptions,
- evidence-backed status and release outcomes,
- deterministic validation/smoke checks,
- reusable harness behavior outside repository-local assumptions,
- small, reviewable implementation PRs,
- clear separation between safe human-triggered assist workflows and
  future autonomous execution capability.

Acceptance is reflected in `project/design/design.md`,
`project/design/architecture.md`, and `project/design/repository_spec.md`.
