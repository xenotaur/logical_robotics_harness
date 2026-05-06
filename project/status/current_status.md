---
id: STATUS-CURRENT
title: Current LRH Status
scope: project
status: active
generated_from:
  focus:
    - FOCUS-CONTROL-PLANE-SEMANTICS
  work_items:
    - WI-0001
    - WI-0002
    - WI-0003
    - WI-0004
    - WI-PRECEDENCE-RESOLVER
    - WI-SNAPSHOT-RESOLVED-CONTEXT
    - WI-ASSIST-TEMPLATES-PACKAGING
    - WI-ASSIST-INSTALLABILITY-HARDENING
generated_at: 2026-05-05T05:21:32Z
health: yellow
---

# Current Status

LRH has crossed the bootstrap threshold for control-plane foundations and now has canonical assist CLI entrypoints (`lrh request`, `lrh snapshot`, `lrh survey`) with package-owned survey implementation.

## Summary

The immediate objective is to finish packaging-safe assist migration sequencing:

- preserve package-owned template/runtime loading behavior
- verify install/build behavior with smoke checks
- keep `lrh survey` canonical on package-owned `sourcetree_surveyor`
- plan only follow-on sourcetree capability expansion

Versioning hardening and release/versioning closeout are complete: LRH versioning is tag-derived via `setuptools-scm`, the `scripts/version` workflow (`verify`/`tag`/`push`) is in place, and final release validation succeeded for pushed tag `v0.2.4`.

Final release evidence for `v0.2.4` is successful across local and CI checks: `scripts/release-smoke v0.2.4 --diagnose` passed locally, GitHub Actions Release tag validation succeeded for pushed tag `v0.2.4`, and GitHub Actions smoke validation succeeded for pushed tag `v0.2.4`. Evidence: `project/evidence/EV-0004.md`, `project/evidence/EV-0005.md`, `project/work_items/resolved/WI-RELEASE-TAG-CI.md`, and `project/work_items/resolved/WI-RELEASE-SMOKE-ISOLATION-AUDIT.md`.

Release-smoke isolation audit closeout remains in effect: diagnostic mode (`scripts/release-smoke <tag> --diagnose`) and optional strict isolation (`scripts/release-smoke <tag> --strict-isolation`) are implemented and documented. Default release-smoke behavior remains warning-oriented for pre-install LRH visibility to preserve local development usability, while strict mode is available when a clean preinstall environment is required. Evidence: `project/evidence/EV-0005.md`.

Closeout note (2026-05-03): Completion and work-item tooling (`lrh work-items organize` + `lrh work-items validate`) is implemented, tested, and documented; work-item discovery edge cases including README handling in `lrh work-items validate` are resolved.

Evidence snapshot:
- `lrh work-items organize --help` and `lrh work-items validate --help` are available in the CLI.
- `lrh work-items validate --project-root .` passes on this repository.
- `lrh validate` passes on this repository.

## Current Health

Yellow.

Reason:
- core control-plane and precedence foundations are implemented
- precedence canonicalization closure has been validated against docs/code/tests with no remaining correctness follow-up
- assist request/snapshot CLI paths are available and documented
- assist installability hardening and smoke-check coverage should remain continuously enforced

## Accepted Release Direction

Option D tag-push PyPI publishing is now the accepted release direction
for the safe-default `lrh` package. The normal CLI install target is
`pipx install lrh` once published; the default package remains
non-agentic, future agentic capability remains explicit through
`lrh[agentic]` and/or `lrh-agentic`, and follow-up implementation should
land in narrow PRs from metadata/resource hardening through first
release. This is a packaging/governance boundary, not a security sandbox.

## Active Priorities

- packaging/install smoke-test hardening
- preserve package-owned assist template/resource loading
- maintain canonical `lrh survey` delegation to package code
- plan sourcetree capability expansion as a distinct follow-on

## Guardrail Summary

- blocked actions: none recorded
- pending approvals: none recorded
- safety warnings: none recorded
- cost warnings: none recorded
- optics warnings: none recorded

## Risks

- delaying package-data hardening while adding new assist features
- coupling runtime assist behavior to repository layout assumptions
- mixing migration and capability expansion into oversized PRs

## Recommended Next Actions

1. Keep WI-ASSIST-INSTALLABILITY-HARDENING evidence current with repeatable smoke checks.
2. Keep package-owned assist template/resource behavior stable.
3. Keep `lrh survey` canonical on package-owned implementation.
4. Plan WI-ASSIST-SOURCETREE-SURVEYOR-EXPANSION as a separate follow-on.
