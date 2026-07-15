---
resolution: null
blocked_reason: null
blocked: false
id: WI-DEV-TOOLCHAIN-VERSION-GUARDRAILS
title: Native Black/Ruff runtime-version guardrails in canonical scripts
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-BOOTSTRAP
related_roadmap:
  - ROADMAP-PHASE-04
related_design:
  - project/design/proposals/adopted/dev-toolchain-env-resolution.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - A shared scripts/_env.sh is sourced by scripts/format, scripts/lint, and scripts/test and holds a single implementation of the tool-version check
  - The guardrail reads the pinned Black and Ruff versions from constraints-dev.txt (currently black==26.3.1, ruff==0.15.12) rather than hardcoding them, so the pin file stays the single source of truth
  - When the active black or ruff version is outside the pinned bound, the canonical script exits non-zero BEFORE running the tool, instead of silently reformatting or linting under the wrong version
  - The failure message names the expected pinned version, the detected active version, and the two supported remedies (activate the documented project environment, or run under Taurworks)
  - The guardrail works in a bare CI checkout with no .taurworks/ present and no Taurworks on PATH (native enforcement is not gated on Taurworks detection)
  - Regression guard for the 2026-07-14 failure mode: with an out-of-bound Black active (e.g. base-anaconda black 25.11.0 vs the 26.3.1 pin), scripts/format --check and scripts/lint fail fast on the version mismatch rather than running the wrong-version tool and proposing an out-of-scope reformat
  - Tests cover in-bound (pass), out-of-bound (fail-fast with explanatory message), and missing-tool cases
  - lrh validate passes 0 errors / 0 warnings on the full project after the change
required_evidence:
  - test_result
  - manual_review
artifacts_expected:
  - scripts/_env.sh
  - scripts/format
  - scripts/lint
  - scripts/test
  - test_module
---

## Summary

Add native runtime-version guardrails for Black and Ruff to LRH's canonical
`scripts/format`, `scripts/lint`, and `scripts/test` so that a stale or wrong
formatter/linter version fails fast with an explanatory message instead of
silently reformatting or mis-linting. This implements the **version-enforcement
half** of the adopted `PROP-DEV-TOOLCHAIN-ENV-RESOLUTION` (Option C): LRH owns
version enforcement natively and mandatorily, effective in every environment
including bare CI checkouts that have no Taurworks.

## Motivation

On 2026-07-14, a clean checkout of `taurworks` `master` had `scripts/lint` report
that `src/taurworks/manager.py` "would be reformatted". The CI-pinned Black
(`black==26.3.1`) considers the file correct; the reformatting came only from a
stale base-anaconda `black==25.11.0` running because the invoking session had no
environment resolved. A native guardrail would have turned that silent near-miss
into an immediate, explanatory failure — and would do so regardless of whether
Taurworks resolution is present. See
[`dev-toolchain-env-resolution.md`](../../design/proposals/adopted/dev-toolchain-env-resolution.md)
§2 (incident) and §7/§9 (decision and the shared-`scripts/_env.sh` direction),
and the alignment doc
[`dev_toolchain_reconciliation.md`](../../design/dev_toolchain_reconciliation.md)
§1–§2 (constrain the toolchain; fail fast when versions are out of bounds).

## Scope

In scope:

- A new POSIX-`sh`-compatible `scripts/_env.sh` that reads the pinned Black and
  Ruff versions from `constraints-dev.txt`, detects the active `black`/`ruff`
  versions, and fails fast with an explanatory message on mismatch.
- Sourcing `scripts/_env.sh` from `scripts/format`, `scripts/lint`, and
  `scripts/test` so the check runs before any tool invocation on the canonical
  path.
- Focused tests for the guardrail (in-bound, out-of-bound, missing-tool).

Out of scope (deliberately deferred):

- The **optional-Taurworks detection/interface contract** (the resolution half of
  Option C). That is settled as design in the proposal's §9 but its
  implementation work item is deferred until the contract is confirmed against
  `taurworks`'s `WI-ACTIVATION-PRODUCERS-0001`. This work item must not add a hard
  Taurworks dependency.
- Any broad reformatting, `pytest` version policy beyond sourcing the shared
  guard, or introduction of Docker/uv/pre-commit (excluded by
  `dev_toolchain_reconciliation.md` non-goals).

## Required Changes

- Add `scripts/_env.sh` implementing `require_tool_versions` (or equivalent),
  parsing `constraints-dev.txt` for the `black==` and `ruff==` pins and comparing
  against `black --version` / `ruff --version` output.
- Source the guard at the top of `scripts/format`, `scripts/lint`, and
  `scripts/test`, after `set -euo pipefail`, so a version mismatch exits non-zero
  before the tool runs.
- Emit a single explanatory failure message: expected pinned version, detected
  active version, and the two supported remedies.
- Add a test module exercising in-bound, out-of-bound, and missing-tool paths.

## Acceptance Criteria

See frontmatter `acceptance`. Each criterion is concrete and independently
checkable; the 2026-07-14 incident is captured as an explicit regression guard.

## Validation

- `scripts/format`, `scripts/lint`, `scripts/test` run green with the pinned
  toolchain active.
- The new test module passes.
- `lrh validate` reports 0 errors / 0 warnings on the full project.

## Coordination

- Implements the native/enforcement half of adopted
  `PROP-DEV-TOOLCHAIN-ENV-RESOLUTION`; recorded there as `implemented_by`.
- Aligns with `dev_toolchain_reconciliation.md` follow-on boundary (1):
  "version-policy and script/CI parity updates".
- The optional-Taurworks resolver work item is a separate, later artifact; do not
  fold it into this one.
