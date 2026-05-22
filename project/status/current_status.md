---
id: STATUS-CURRENT
title: Current LRH Status
scope: project
status: active
generated_from:
  focus:
    - FOCUS-EXECUTION-FRAMEWORK-PLANNING
  work_items:
    - WI-LRH-CORE-STATE-APIS-MVP
    - WI-WORKSTREAM-PLANNING-TREE-RELATIONSHIPS-MVP
    - WI-PLANNING-TREE-VALIDATION-RULES-MVP
    - WI-WORKSTREAM-SNAPSHOT-MVP
    - WI-EXECUTION-READINESS-SCHEMA
    - WI-RUN-PACKET-DRY-RUN
    - WI-RUN-REPORT-MVP
    - WI-LRH-SERVE-SAFE-DEFAULT-MVP
generated_at: 2026-05-17T21:50:21Z
health: yellow
---

# Current Status

LRH has crossed the bootstrap threshold for control-plane foundations and now has canonical assist CLI entrypoints (`lrh request`, `lrh snapshot`, `lrh survey`) plus the safe-default `lrh serve` local viewer/workbench. The execution-framework prerequisite work, first execution-contract package, and serve MVP are implemented; the next identified package is Layer 2 durable run state/manual run tracking.

## Summary

The immediate execution-framework objective is to start **Layer 2: durable run state/manual run
tracking** from completed prerequisites, contracts, and the completed safe-default serve surface. The
next package should define durable manual run artifacts and lifecycle state while continuing to:

- reuse shared core-state APIs and planning-tree summaries
- consume opt-in execution-readiness metadata
- preserve run-packet and run-report artifacts for human review
- keep observation adapters, branch containment, autonomous dispatch, branch mutation, PR creation, stabilization loops, and merge/publish automation deferred

Versioning hardening and release/versioning closeout are complete: LRH versioning is tag-derived via `setuptools-scm`, the `scripts/version` workflow (`verify`/`tag`/`push`) is in place, and final release validation succeeded for pushed tag `v0.2.4`.

Final release evidence for `v0.2.4` is successful across local and CI checks: `scripts/release-smoke v0.2.4 --diagnose` passed locally, GitHub Actions Release tag validation succeeded for pushed tag `v0.2.4`, and GitHub Actions smoke validation succeeded for pushed tag `v0.2.4`. Evidence: `project/evidence/EV-0004.md`, `project/evidence/EV-0005.md`, `project/work_items/resolved/WI-RELEASE-TAG-CI.md`, and `project/work_items/resolved/WI-RELEASE-SMOKE-ISOLATION-AUDIT.md`.

Release-smoke isolation audit closeout remains in effect: diagnostic mode (`scripts/release-smoke <tag> --diagnose`) and optional strict isolation (`scripts/release-smoke <tag> --strict-isolation`) are implemented and documented. Default release-smoke behavior remains warning-oriented for pre-install LRH visibility to preserve local development usability, while strict mode is available when a clean preinstall environment is required. Evidence: `project/evidence/EV-0005.md`.

Closeout note (2026-05-03): Completion and work-item tooling (`lrh work-items organize` + `lrh work-items validate`) is implemented, tested, and documented; work-item discovery edge cases including README handling in `lrh work-items validate` are resolved.


Documentation closeout note (2026-05-22): the broad human-facing docs reorg is now closed after navigation dogfooding and CLI-help accuracy audit. The docs index and section READMEs are aligned to current moved paths, and remaining gaps are tracked as narrow follow-up work items rather than as an open-ended docs reorg stream.


Control-plane freshness note (2026-05-17): the stale active orphan leaves
`WI-META-WORKSPACE-RESOLUTION` and `WI-SNAPSHOT-RESOLVED-CONTEXT` were audited and moved to
resolved based on existing implementation/supersession evidence. `WI-META-CLI-MVP` was already
resolved before this audit. `lrh validate` is expected to be warning-free for orphan active planning
leaves after this cleanup.

Execution-framework closeout (2026-05-16): shared core state APIs, planning-tree validation, planning
relationship indexing, snapshot-visible planning summaries, execution-readiness metadata, dry-run
run-packet rendering, run-report rendering, and the safe-default `lrh serve` viewer/workbench are
implemented and have execution records. The next implementation package is Layer 2 durable run
state/manual run tracking.

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

- keep the closed `WI-LRH-SERVE-SAFE-DEFAULT-MVP` safe-default boundary intact while advancing
  **Layer 2: durable run state/manual run tracking** as the next execution-framework package
- preserve package-owned assist template/resource loading
- maintain canonical `lrh survey` delegation to package code
- keep later branch mutation, observation adapters, stabilization loops, and agent backends deferred

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

1. Plan **Layer 2: durable run state/manual run tracking** for `project/runs/<RUN-ID>/`, `packet.yaml`,
   `state.yaml`, `events.jsonl`, prompts, evidence, `report.md`, manual lifecycle states,
   explicit-click/manual updates, and manual/future-automated parity.
2. Keep package-owned assist template/resource behavior stable.
3. Keep `lrh survey` canonical on package-owned implementation.
4. Keep later observation adapters, branch mutation, stabilization loops, PR creation, merge/release
   automation, destructive actions, and agent backends deferred.
