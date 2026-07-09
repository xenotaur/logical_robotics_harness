# Release runbook

## Purpose

This is the maintainer runbook for validating, tagging, smoke-testing, and
publishing Logical Robotics Harness (LRH) releases. The main `README.md` keeps
only a short release summary and points here as the canonical release procedure.

Use this document when preparing release evidence, rehearsing TestPyPI
publishing, creating version tags, publishing to PyPI, and verifying the
published package.

## Release model

LRH uses a staged, publish-last release model:

- Release preparation happens through ordinary pull requests first.
- Local validation and installed-wheel smoke tests should pass before a release
  tag is pushed.
- The `lrh` distribution is the safe-default package boundary for the harness.
  This is a packaging and governance boundary, not a security sandbox.
- Package versions are derived from Git tags through `setuptools-scm`; Git tags
  are the source of truth for released versions.
- Production publishing is tag-push based for version tags such as `v0.1.0`.
- TestPyPI and PyPI publishing use Trusted Publishing/OIDC through GitHub
  Actions, not long-lived PyPI API tokens stored in GitHub secrets.
- The default `lrh` install is non-agentic. It does not include LRH's autonomous
  execution package or an autonomous-loop command implementation.
- Do not document future install modes such as `lrh[agentic]` as current
  behavior unless the extra and package behavior have actually been implemented.

## Version tag format

The repository's release and TestPyPI workflows currently accept production and
rehearsal tags matching this exact semantic-version shape:

```text
vMAJOR.MINOR.PATCH
```

For example, `v0.1.0` resolves to package version `0.1.0`.

The local `scripts/version` helper validates tag names with Git's ref-format
rules, but `.github/workflows/release.yml`,
`.github/workflows/release-tag-ci.yml`, and
`.github/workflows/testpypi-rehearsal.yml` currently reject pre-release tags such
as `v0.1.0rc1`. Do not rely on `vMAJOR.MINOR.PATCHrcN` tags for the current CI
publishing path unless the workflows are changed in the same release-prep work.

## Pre-release local readiness checks

Start from the intended release branch and confirm the toolchain before running
release validation:

```bash
git checkout main
git pull
scripts/version tools
```

These commands ensure the maintainer is on `main`, has the latest remote state,
and can see the local versions of the release toolchain.

Before pushing a release tag, the candidate commit should already have passing
pull-request or main-branch CI. Then run local release checks from the repository
root, replacing `v0.1.0` with the intended release tag:

```bash
scripts/version verify v0.1.0
scripts/release-smoke v0.1.0 --strict-isolation
```

What these commands prove:

- `scripts/version verify v0.1.0` checks that the tag name is a valid Git ref,
  requires a clean working tree, and runs the repository lint, format, and unit
  test gates.
- `scripts/release-smoke v0.1.0 --strict-isolation` rebuilds artifacts, checks
  them, installs the built wheel in a clean temporary virtual environment, and
  verifies the installed CLI. Strict isolation makes pre-install LRH visibility a
  hard failure, which is appropriate for CI and maintainer release audits.

`scripts/release-smoke` also supports running without a tag argument, and the
installed-wheel smoke workflow uses that form for generic wheel-smoke coverage.
For release readiness, prefer passing the intended tag so the smoke test verifies
`lrh --version` against the expected release version.

## Release smoke test

`scripts/release-smoke` is the canonical installed-package smoke test. It should
build distribution artifacts, run artifact checks, install the built wheel into a
clean temporary virtual environment, and verify installed CLI behavior from that
environment.

Expected installed CLI coverage includes:

```bash
lrh --help
lrh validate --help
lrh request --help
lrh snapshot --help
lrh survey --help
```

When an expected version is supplied, the smoke test also checks `lrh --version`
against that version. The script resolves the built wheel dynamically from
`dist/`; do not hard-code a wheel filename.

Useful smoke-test modes:

- `scripts/release-smoke v0.1.0 --strict-isolation` fails if LRH is visible in
  the temporary environment before the wheel under test is installed.
- `scripts/release-smoke v0.1.0 --diagnose` prints pre-install isolation
  diagnostics while preserving the default continue-on-warning behavior.
- `scripts/release-smoke v0.1.0 --diagnose --preserve` keeps the temporary
  environment for investigation.

## TestPyPI rehearsal

Run a TestPyPI rehearsal before the first real PyPI release and whenever release
mechanics change.

**Tag collision warning:** `release.yml` triggers on any pushed tag matching
`vMAJOR.MINOR.PATCH`, with no distinction between a "rehearsal" tag and a
production tag. Pushing a tag to satisfy the rehearsal's tag-ref requirement
therefore also arms a real `release.yml` publish attempt at the same time.
There is no way to create a tag that only the rehearsal workflow can see. See
[Rehearse-then-approve sequencing](#rehearse-then-approve-sequencing) below
for how the `pypi` environment's required-reviewer gate is used to make this
safe.

Current implementation:

- Workflow: **TestPyPI rehearsal publish**
- File: `.github/workflows/testpypi-rehearsal.yml`
- Trigger: manual `workflow_dispatch` from a tag ref
- Accepted tag shape: `vMAJOR.MINOR.PATCH`
- Publish mechanism: PyPI Trusted Publishing/OIDC via PyPA's publishing action

External/manual prerequisite: a maintainer must configure TestPyPI Trusted
Publishing in the TestPyPI web UI for the `lrh` project before this workflow can
publish. Use repository `xenotaur/logical_robotics_harness`, workflow
`testpypi-rehearsal.yml`, and GitHub environment `testpypi`.

To rehearse:

1. Choose or create a unique `vMAJOR.MINOR.PATCH` tag for the rehearsal.
2. In GitHub Actions, open **TestPyPI rehearsal publish**.
3. Select the tag ref, not a branch ref.
4. Run the workflow manually.
5. Confirm the workflow ran `scripts/release-smoke "$TAG_UNDER_TEST" --strict-isolation` and published checked `dist/` artifacts.
6. Verify the TestPyPI package page at `https://test.pypi.org/project/lrh/`.
7. Test install from TestPyPI in a clean environment, replacing `VERSION` with
   the version shown by the workflow or package page:

```bash
python -m venv /tmp/lrh-testpypi-venv
/tmp/lrh-testpypi-venv/bin/python -m pip install --upgrade pip
/tmp/lrh-testpypi-venv/bin/python -m pip install --index-url https://test.pypi.org/simple/ --no-deps lrh==VERSION
/tmp/lrh-testpypi-venv/bin/lrh --help
/tmp/lrh-testpypi-venv/bin/lrh validate --help
```

TestPyPI caveats:

- TestPyPI has separate accounts, project configuration, package history,
  availability, and security posture from production PyPI.
- Package versions and files cannot be re-uploaded after TestPyPI accepts them;
  choose a unique rehearsal version.
- LRH currently has no runtime package dependencies, so `--no-deps` is
  appropriate for this verification. Future runtime dependencies may require an
  adjusted install command or an extra index for dependencies unavailable on
  TestPyPI.

## PyPI Trusted Publisher setup

Before production publishing can work, a maintainer must complete these external
setup steps in PyPI and GitHub:

- Configure or reserve the PyPI project `lrh` under the intended maintainer
  account or organization.
- Configure PyPI Trusted Publishing for repository
  `xenotaur/logical_robotics_harness`, workflow `release.yml`, and environment
  `pypi`.
- Confirm the publishing workflow grants `id-token: write` only to the publishing
  job that needs to mint the OIDC token.
- Confirm GitHub environment protection and approval rules for `pypi` match
  maintainer intent.
- Avoid storing long-lived PyPI API tokens in GitHub secrets for the production
  publishing path.

The PyPI project and Trusted Publisher entries are configured manually in the
PyPI web UI by a maintainer with access to that project.

Current implementation: the `pypi` GitHub environment has a required-reviewer
protection rule (reviewer: `xenotaur`, i.e. Anthony Francis), so
`release.yml`'s `publish-pypi` job pauses for manual approval after
`build-check-smoke` succeeds. The `testpypi` environment intentionally has no
protection rule. See `project/memory/decision_log.md` (2026-07-09: "PyPI
Release Environment Protection Rules") for the rationale.

## Rehearse-then-approve sequencing

Because the `pypi` environment requires manual approval and `testpypi-rehearsal.yml`
can only be dispatched against a tag that already contains the workflow file,
the recommended sequence for the first release, and for any release where
rehearsal is warranted, is:

1. Push the intended real release tag as usual (see
   [Tagging and publishing](#tagging-and-publishing) below).
2. **Release tag validation** and **Smoke validation** run automatically and
   complete. `release.yml`'s `build-check-smoke` job also runs automatically
   and completes, but `publish-pypi` pauses with status "Waiting for review"
   because the `pypi` environment requires approval.
3. While `publish-pypi` is pending, open **TestPyPI rehearsal publish** in
   GitHub Actions and dispatch it against the same tag.
4. Verify the TestPyPI package page and a clean-environment install (see
   [TestPyPI rehearsal](#testpypi-rehearsal) above).
5. If the rehearsal looks correct, approve the pending `pypi` deployment to
   let the real publish proceed. If it does not, reject the deployment; the
   tag's version cannot be reused, so fix forward with a new version per
   [Failure and recovery notes](#failure-and-recovery-notes).

For routine releases where rehearsal is not warranted, simply approve the
pending `pypi` deployment once `build-check-smoke` has succeeded.

## Tagging and publishing

Do not push a production release tag until the release-readiness checklist is
complete and local validation has passed. Pushing the tag does not immediately
publish: the `pypi` environment's required-reviewer gate holds the real
publish pending approval (see
[Rehearse-then-approve sequencing](#rehearse-then-approve-sequencing) above).
When a TestPyPI rehearsal is warranted, verify it during that pending window,
before approving the deployment — not before pushing the tag.

Create or confirm the release tag and then push it:

```bash
scripts/version tag v0.1.0
scripts/version push v0.1.0
```

`scripts/version tag v0.1.0` creates the tag after running release verification.
It is idempotent when the tag already exists at the current commit.

`scripts/version push v0.1.0` pushes the matching local tag to `origin` and is
safe when local and remote tag state already match. If the remote tag exists at a
different commit, stop and investigate; do not force-push or move a release tag
as part of the normal release flow.

Pushing a `vMAJOR.MINOR.PATCH` tag starts tag-push CI:

- **Release tag validation** (`.github/workflows/release-tag-ci.yml`) validates
  the tag, runs `scripts/version verify "$TAG_UNDER_TEST"`, runs
  `scripts/release-smoke "$TAG_UNDER_TEST"`, and captures audit artifacts.
- **Publish release to PyPI** (`.github/workflows/release.yml`) validates the
  tag, runs `scripts/version verify "$TAG_UNDER_TEST"`, runs
  `scripts/release-smoke "$TAG_UNDER_TEST" --strict-isolation`, uploads checked
  artifacts, and publishes to PyPI after the build/check/smoke job passes.
- **Smoke validation** (`.github/workflows/smoke.yml`) also runs on pushed tags
  matching `v*`.

## Post-release verification

After production publishing succeeds, verify the release from clean environments.
For CLI-focused verification, `pipx run` avoids modifying the maintainer's
persistent pipx home:

```bash
pipx run --spec lrh==VERSION lrh --help
pipx run --spec lrh==VERSION lrh validate --help
```

A persistent `pipx` install is also appropriate for a maintainer sanity check:

```bash
pipx install lrh
lrh --help
lrh validate --help
```

Also verify a clean `pip install` path when appropriate:

```bash
python -m venv /tmp/lrh-pypi-venv
/tmp/lrh-pypi-venv/bin/python -m pip install --upgrade pip
/tmp/lrh-pypi-venv/bin/python -m pip install lrh==VERSION
/tmp/lrh-pypi-venv/bin/lrh --help
/tmp/lrh-pypi-venv/bin/lrh validate --help
```

Finally, confirm the package page at `https://pypi.org/project/lrh/` shows the
expected version, metadata, and files.

## Failure and recovery notes

- **Local smoke test fails:** do not tag or publish. Inspect the failure, rerun
  with `--diagnose --preserve` if isolation is unclear, fix the issue in a normal
  PR, and rerun local validation.
- **TestPyPI publishing fails:** inspect the failed workflow job and TestPyPI
  project configuration. If no files were accepted, fix the workflow or Trusted
  Publisher setup and rerun for the same tag. If files were accepted, use a new
  version for the next rehearsal.
- **Production publish fails after a tag exists:** inspect GitHub Actions before
  changing Git state. If PyPI accepted no files, fix external setup or a
  transient workflow issue and rerun the failed job for the same tag. If PyPI
  accepted files, preserve evidence, do not reuse the version, and publish a
  follow-up version after a normal fix.
- **Package metadata is wrong after upload:** package files are immutable on PyPI.
  Document the issue, fix metadata in a PR, bump the version, and publish a new
  release.
- **Version already exists on PyPI:** choose a new version. Do not attempt to
  overwrite or reuse an existing PyPI version.

Do not delete history, force-push release tags, or move published tags unless a
separate maintainer-approved recovery plan explicitly requires it.

## Release evidence

After a release, preserve or reference enough evidence to support release status
claims:

- local `scripts/release-smoke` output,
- GitHub Actions workflow links for release tag validation, smoke validation,
  TestPyPI rehearsal when used, and production publishing,
- TestPyPI and PyPI project links,
- the release tag,
- release notes,
- clean-install verification output,
- any relevant LRH evidence or status artifact under `project/` if project
  convention calls for updating release readiness or release status.

Status should remain evidence-backed. Do not make optimistic release claims in
project-control documents without linking the validation, workflow, package-page,
or install-verification evidence that supports them.
