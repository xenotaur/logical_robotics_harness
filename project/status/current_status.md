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
    - WI-ASSIST-SOURCETREE-SURVEYOR-MIGRATION
generated_at: 2026-04-22T00:00:00Z
health: yellow
---

# Current Status

LRH has crossed the bootstrap threshold for control-plane foundations and now has canonical assist CLI entrypoints (`lrh request`, `lrh snapshot`), but installability hardening for assist templates is still pending.

## Summary

The immediate objective is to finish packaging-safe assist migration sequencing:

- move runtime templates into package-owned locations
- switch template loading to installed-package-safe resource resolution
- verify install/build behavior with smoke checks
- then mechanically migrate `sourcetree_surveyor` before any capability expansion

## Current Health

Yellow.

Reason:
- core control-plane and precedence foundations are implemented
- precedence canonicalization closure has been validated against docs/code/tests with no remaining correctness follow-up
- assist request/snapshot CLI paths are available and documented
- template loading still relies on source-tree-relative paths that must be hardened for installed usage

## Active Priorities

- package-owned template relocation
- installed-package-safe template/resource loading
- packaging/install smoke-test hardening
- mechanical `sourcetree_surveyor` migration into package code

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

1. Complete WI-ASSIST-TEMPLATES-PACKAGING.
2. Complete WI-ASSIST-INSTALLABILITY-HARDENING.
3. Complete WI-ASSIST-SOURCETREE-SURVEYOR-MIGRATION.
4. Plan WI-ASSIST-SOURCETREE-SURVEYOR-EXPANSION as a separate follow-on.
