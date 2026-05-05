---
id: PROP-SAFE-DEFAULT-AGENTIC-EXTRA-PACKAGING
type: design_proposal
title: Safe-default LRH install with explicit opt-in agentic capability
status: proposed
created_on: 2026-05-05
updated_on: 2026-05-05
---

## 1) Purpose

Define LRH packaging and command-surface semantics so the default
install remains non-agentic and human-assist oriented, while
higher-risk autonomous capability is explicitly opt-in via
`lrh[agentic]` and/or `lrh-agentic`.

This proposal is design-only and intentionally avoids implementation
churn in imports, package metadata, or CLI behavior in this changeset.

## 2) Problem and motivation

Today, LRH is already useful in human-triggered assistance workflows
(request/snapshot/validate/project-control authoring). Over time, LRH
may also grow autonomous or semi-autonomous execution flows.

Some collaborators, institutions, or compliance environments may allow
assistive tooling but restrict autonomous agentic software except in
segmented or air-gapped environments. LRH therefore needs a clear,
reviewable install and command boundary that distinguishes:

- safe-default human-assist operation, and
- explicit opt-in autonomous capability.

This is simultaneously:

- a user trust and governance boundary, and
- a packaging and architecture boundary.

## 3) Design principles for this boundary

1. **Explicit capability state over implicit behavior.**
2. **Safe-by-default install posture for common users.**
3. **Clear evidence-backed behavior in docs, tests, and status.**
4. **No overclaiming security properties.**
5. **Incremental migration with minimal import churn.**

Important wording constraint:

> The default `lrh` install does not include LRH's autonomous
> execution package or autonomous-loop commands.

This is a packaging/governance statement, not a security sandbox
claim. It does **not** imply that LRH artifacts could never be used in
any agentic workflow outside this package boundary.

## 4) Proposed install semantics

Target semantics:

```text
pipx install lrh
```

Installs a usable non-agentic LRH toolkit with core and assist
functionality only.

```text
pipx install "lrh[agentic]"
```

Installs the same default LRH toolkit plus the separate agentic
capability package.

```text
pipx install lrh-agentic
```

Installs the explicit agentic package and direct agentic command.

`lrh[agentic]` is real Python packaging extra syntax, not naming
convention. When implemented, it should map to optional dependencies
in `pyproject.toml` and point at a concrete `lrh-agentic`
distribution.

## 5) Proposed capability boundaries

Conceptual distribution/package roles:

```text
lrh-core      # deterministic shared control-plane functionality; no autonomous loop
lrh-assist    # human-triggered assist workflows; no autonomous execution loop
lrh-agentic   # autonomous execution loop and higher-risk execution integrations
lrh           # safe-default user-facing toolkit / CLI distribution
```

Default `lrh` should include `lrh-core` + `lrh-assist`, and exclude
`lrh-agentic`.

This boundary should be communicated as an install/capability boundary
for governance and user intent, not as a formal runtime confinement
boundary.

## 6) CLI design and command behavior

Preferred behavior:

- `lrh` remains the main integrated command.
- `lrh-agentic` is an explicit direct command from the agentic
  package.
- `lrh agentic ...` is an integrated alias/dispatcher when
  `lrh-agentic` is installed.
- If `lrh-agentic` is not installed, `lrh agentic ...` fails
  explicitly with install guidance.

Illustrative missing-package error:

```text
Agentic LRH support is not installed.

The default lrh install includes human-triggered assist workflows only.
To enable autonomous execution features, install:

    pipx install "lrh[agentic]"

or install the explicit agentic package:

    pipx install lrh-agentic
```

Rationale:

- discoverability without implicit capability activation,
- explicit consent before autonomous capability is installed,
- clearer institutional governance review.

### Help-output concern and mitigation

In strict environments, merely seeing `agentic` in `lrh --help` can be
sensitive. Mitigations to evaluate during implementation:

- show `agentic` as "optional" / "not installed" in main help,
- hide deep agentic subcommands unless dependency is present,
- ensure `lrh agentic --help` yields explicit unavailable messaging
  rather than ambiguous import errors.

## 7) Module layout and migration strategy

A literal top-level split such as:

```text
src/lrh_core/
src/lrh_assist/
src/lrh_agentic/
src/lrh_cli/
```

would require broad import/package refactoring. That may become useful,
but should not be rushed.

Recommended incremental path:

1. Preserve current `src/lrh/` package layout initially.
2. Strengthen logical boundaries inside the existing package
   (`assist/`, control/core modules, CLI dispatch seams).
3. Add design docs and tests that define safe-default behavior.
4. Revisit import-package or distribution splits only when concrete
   packaging pressure justifies churn.

Near-term design should explicitly defer broad import churn and avoid
drive-by refactors.

## 8) Phased implementation strategy

Phase 1 (near-term):

1. Adopt this install-mode and capability-boundary design.
2. Add/refine `lrh agentic` stub behavior that reports clear
   "agentic support not installed" guidance when optional package is
   missing.
3. Introduce install-mode smoke checks for safe-default behavior.
4. Prepare internal module boundaries without broad import churn.

Phase 2 (deferred until needed):

5. Create separate `lrh-agentic` distribution when autonomous loop
   implementation is real/near-term.
6. Add `lrh[agentic]` optional dependency metadata only after a
   concrete `lrh-agentic` package exists.

## 9) Validation plan for future implementation

Recommended smoke checks:

```text
Default install:
  pipx install lrh
  lrh --help
  lrh request --help
  lrh snapshot --help
  lrh agentic --help  # clear not-installed message; no autonomous loop available

Agentic extra install:
  pipx install "lrh[agentic]"
  lrh agentic --help  # works
  lrh-agentic --help  # works

Direct agentic install:
  pipx install lrh-agentic
  lrh-agentic --help  # works
```

Recommended unit-level checks:

- default CLI path does not import `lrh_agentic` at process start,
- agentic dispatch performs lazy import only for `agentic` command,
- missing optional package yields deterministic, user-facing error
  text,
- help output clearly marks agentic commands as optional/unavailable
  when not installed.

## 10) Tradeoffs

Pros:

- clearer institutional/compliance posture,
- safe-default install behavior,
- explicit opt-in autonomy,
- cleaner dependency isolation,
- improved user trust,
- stronger long-term architecture separation across
  control/assist/agentic concerns,
- lower risk of accidental installation of higher-risk integrations.

Cons:

- multi-distribution/versioning complexity,
- compatibility-management burden across packages,
- higher documentation burden,
- potential user confusion among `lrh`, `lrh-agentic`, and
  `lrh[agentic]`,
- risk of overclaiming safety if wording is imprecise,
- possible future import/package migration churn,
- help-surface wording concerns in strict institutions.

## 11) Recommendation and decision posture

Recommend adopting these decisions:

1. Safe-default install semantics are a target LRH design.
2. Default `lrh` remains non-agentic.
3. Agentic capability is explicit via `lrh-agentic` and/or
   `lrh[agentic]`.
4. Preserve existing import layout in the near term.
5. Defer broad package/module refactors until implementation pressure
   is concrete.
6. Treat the boundary as packaging/governance, not sandbox/security
   guarantee.

## 12) Relationship to current LRH design principles

This proposal aligns with existing LRH direction:

- explicit state over implicit behavior,
- evidence-backed status and execution records,
- deterministic validation/snapshot/control-plane workflows,
- human-triggered assist workflows now,
- future autonomous execution as a separate higher-risk capability.

No runtime behavior change is made by this proposal itself.
