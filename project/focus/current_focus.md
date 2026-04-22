---
id: FOCUS-CONTROL-PLANE-SEMANTICS
title: Package assist runtime assets and finish migration sequencing
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
---

# Current Focus

The immediate priority is to consolidate the assist request/snapshot migration into package-safe, installable behavior.

Recently completed:

- request-system extraction into `src/lrh/assist/`
- thin CLI wrappers wired to `lrh request` and `lrh snapshot`
- assist README updates documenting canonical CLI usage

## Why this is active now

LRH now has canonical assist interfaces, but runtime template loading still depends on repository-relative paths under `scripts/aiprog/templates/`.

That is acceptable for local maintainer workflows but fragile for installed-package use. Before broader collaborator use, package-data and installability behavior must be made first-class and validated.

## Priorities

1. Move runtime templates into package-owned paths (`src/lrh/assist/templates/` target).
2. Update loading to package-resource semantics rather than source-tree-relative lookups.
3. Add packaging/build/install hardening and smoke-test expectations for installed behavior.
4. Migrate `sourcetree_surveyor.py` into `src/lrh/assist/` as a mechanical move.
5. Handle sourcetree capability expansion only as a separate follow-on work item.

## Non-Goals

- Mixing migration mechanics with feature expansion in one PR.
- Broad redesign of request/snapshot semantics.
- Unrelated refactors outside assist packaging/migration sequencing.

## Exit Criteria

This focus is complete when:

1. required templates ship from package-owned locations
2. installed `lrh request` and `lrh snapshot` paths do not rely on repo-relative template discovery
3. packaging/install smoke checks are defined and passing
4. `sourcetree_surveyor` is migrated mechanically, with capability expansion explicitly deferred
